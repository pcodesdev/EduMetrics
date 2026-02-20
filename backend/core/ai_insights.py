"""
ai_insights.py — Safe AI-assisted narratives on top of deterministic metrics.

Design:
- Never compute grades/ranks via AI.
- Always derive metrics from existing deterministic analytics.
- Use AI only to explain, simplify, and recommend.
- Gracefully fall back to deterministic templates when AI is disabled/unavailable.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import httpx

from core.stats import compute_student_profile
from core.kenya_grading import get_grade_label


def _safe_float(val: Any) -> Optional[float]:
    try:
        v = float(val)
        if np.isnan(v) or np.isinf(v):
            return None
        return round(v, 2)
    except (TypeError, ValueError):
        return None


def _find_col(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    cols_lower = {str(c).lower().strip(): c for c in df.columns}
    for a in aliases:
        if a.lower() in cols_lower:
            return cols_lower[a.lower()]
    return None


def _student_metrics(df: pd.DataFrame, student_id: str, pass_mark: int) -> Optional[Dict[str, Any]]:
    profile = compute_student_profile(df, student_id, pass_mark=pass_mark)
    if not profile:
        return None

    class_col = _find_col(df, ["class", "grade", "form", "stream"])
    student_col = _find_col(df, ["student_id", "name", "student_name"])
    term_col = _find_col(df, ["term", "semester"])

    school_mean = _safe_float(pd.to_numeric(df.get("percentage"), errors="coerce").mean()) if "percentage" in df.columns else None

    class_mean = None
    student_class = profile.get("class")
    if class_col and student_class is not None and "percentage" in df.columns:
        cdf = df[df[class_col].astype(str) == str(student_class)]
        class_mean = _safe_float(pd.to_numeric(cdf.get("percentage"), errors="coerce").mean())

    trend_points: List[Dict[str, Any]] = []
    for row in profile.get("term_trends", []) or []:
        term = row.get("term")
        mean = _safe_float(row.get("mean"))
        if term is not None and mean is not None:
            trend_points.append({"term": str(term), "mean": mean})

    strengths: List[str] = []
    concerns: List[str] = []
    recommendations: List[str] = []

    overall_mean = _safe_float(profile.get("overall_mean"))
    if overall_mean is not None:
        if overall_mean >= 75:
            strengths.append("Consistently strong overall performance.")
        if overall_mean < pass_mark:
            concerns.append(f"Overall score is below pass mark ({pass_mark}%).")
            recommendations.append("Create a weekly recovery plan with focused revision targets.")

    if class_mean is not None and overall_mean is not None:
        if overall_mean >= class_mean + 5:
            strengths.append("Performs above class average.")
        elif overall_mean <= class_mean - 5:
            concerns.append("Currently below class average.")
            recommendations.append("Schedule class teacher follow-up and targeted support by subject.")

    if trend_points and len(trend_points) >= 2:
        first = trend_points[0]["mean"]
        last = trend_points[-1]["mean"]
        delta = round(last - first, 1)
        if delta >= 3:
            strengths.append(f"Positive trend across terms (+{delta} points).")
        elif delta <= -3:
            concerns.append(f"Declining trend across terms ({delta} points).")
            recommendations.append("Review causes of decline and adjust study routine early.")

    subject_scores = profile.get("subject_scores") or []
    if subject_scores:
        sorted_subjects = sorted(
            [
                {"subject": s.get("subject", "Unknown"), "score": _safe_float(s.get("score"))}
                for s in subject_scores
                if _safe_float(s.get("score")) is not None
            ],
            key=lambda x: x["score"], reverse=True
        )
        if sorted_subjects:
            top = sorted_subjects[0]
            strengths.append(f"Strongest subject: {top['subject']} ({top['score']}%).")
        if len(sorted_subjects) > 1:
            weak = sorted_subjects[-1]
            concerns.append(f"Needs improvement in {weak['subject']} ({weak['score']}%).")
            recommendations.append(f"Add extra practice and teacher check-ins for {weak['subject']}.")

    # Deduplicate while preserving order
    strengths = list(dict.fromkeys(strengths))[:3]
    concerns = list(dict.fromkeys(concerns))[:3]
    recommendations = list(dict.fromkeys(recommendations))[:3]

    return {
        "student_id": str(profile.get("student_id", student_id)),
        "student_name": str(profile.get("name", student_id)),
        "class": profile.get("class"),
        "overall_mean": overall_mean,
        "student_grade": get_grade_label(overall_mean or 0, "universal"),
        "class_mean": class_mean,
        "school_mean": school_mean,
        "pass_mark": pass_mark,
        "trend_points": trend_points,
        "strengths": strengths,
        "concerns": concerns,
        "recommendations": recommendations,
        "supporting_profile": profile,
        "student_count": int(df[student_col].nunique()) if student_col else len(df),
    }


def _deterministic_parent_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    name = metrics["student_name"]
    overall = metrics.get("overall_mean")
    grade = metrics.get("student_grade", "N/A")
    cls = metrics.get("class") or "N/A"
    class_mean = metrics.get("class_mean")
    school_mean = metrics.get("school_mean")
    pass_mark = metrics.get("pass_mark", 50)

    summary_parts: List[str] = [
        f"{name} is in {cls} with an overall score of {overall if overall is not None else 'N/A'}% (Grade {grade})."
    ]
    if class_mean is not None:
        summary_parts.append(f"Class average is {class_mean}%.")
    if school_mean is not None:
        summary_parts.append(f"School average is {school_mean}%.")
    summary_parts.append(f"Pass mark is {pass_mark}%.")

    return {
        "mode": "deterministic",
        "summary": " ".join(summary_parts),
        "strengths": metrics.get("strengths", []),
        "concerns": metrics.get("concerns", []),
        "recommendations": metrics.get("recommendations", []),
        "metrics": {
            "student_id": metrics.get("student_id"),
            "student_name": metrics.get("student_name"),
            "class": cls,
            "overall_mean": overall,
            "student_grade": grade,
            "class_mean": class_mean,
            "school_mean": school_mean,
            "pass_mark": pass_mark,
        },
    }


def _call_openai_parent_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    timeout_s = float(os.getenv("AI_TIMEOUT_SECONDS", "20"))
    temperature = float(os.getenv("AI_TEMPERATURE", "0.2"))
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    system_prompt = (
        "You are an education assistant. Explain student performance in plain language for a parent with basic literacy. "
        "Do not invent numbers. Use only provided metrics. Keep recommendations practical and non-judgmental. "
        "Return strict JSON with keys: summary, strengths, concerns, recommendations."
    )
    user_prompt = (
        "Create a short parent summary from these metrics:\n"
        f"{metrics}\n\n"
        "Constraints:\n"
        "- summary: max 90 words\n"
        "- strengths: 1-3 bullets\n"
        "- concerns: 1-3 bullets\n"
        "- recommendations: exactly 3 bullets\n"
        "- mention pass mark explicitly once\n"
    )

    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
        ],
        "temperature": temperature,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "parent_summary",
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "summary": {"type": "string"},
                        "strengths": {"type": "array", "items": {"type": "string"}},
                        "concerns": {"type": "array", "items": {"type": "string"}},
                        "recommendations": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["summary", "strengths", "concerns", "recommendations"],
                },
                "strict": True,
            }
        },
    }

    with httpx.Client(timeout=timeout_s) as client:
        res = client.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        res.raise_for_status()
        data = res.json()

    text = (data.get("output_text") or "").strip()
    if not text:
        raise RuntimeError("Empty AI response.")

    import json as _json
    parsed = _json.loads(text)
    return {
        "mode": "ai_openai",
        "summary": parsed.get("summary", ""),
        "strengths": parsed.get("strengths", [])[:3],
        "concerns": parsed.get("concerns", [])[:3],
        "recommendations": parsed.get("recommendations", [])[:3],
        "metrics": {
            "student_id": metrics.get("student_id"),
            "student_name": metrics.get("student_name"),
            "class": metrics.get("class"),
            "overall_mean": metrics.get("overall_mean"),
            "student_grade": metrics.get("student_grade"),
            "class_mean": metrics.get("class_mean"),
            "school_mean": metrics.get("school_mean"),
            "pass_mark": metrics.get("pass_mark"),
        },
    }


def generate_parent_summary(df: pd.DataFrame, student_id: str, pass_mark: int = 50) -> Dict[str, Any]:
    """
    Public entrypoint for AI-assisted parent summary.

    Behavior:
    - If AI is disabled/misconfigured/fails, return deterministic fallback.
    - If AI is enabled + configured, return AI narrative with deterministic metrics attached.
    """
    metrics = _student_metrics(df, student_id, pass_mark=pass_mark)
    if not metrics:
        return {"error": "student_not_found", "student_id": student_id}

    ai_enabled = os.getenv("AI_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    provider = os.getenv("AI_PROVIDER", "openai").strip().lower()

    if not ai_enabled:
        return _deterministic_parent_summary(metrics)

    try:
        if provider == "openai":
            return _call_openai_parent_summary(metrics)
        return _deterministic_parent_summary(metrics)
    except Exception as exc:
        fallback = _deterministic_parent_summary(metrics)
        fallback["mode"] = "deterministic_fallback"
        fallback["ai_error"] = str(exc)
        return fallback

