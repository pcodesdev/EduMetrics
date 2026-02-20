"""
risk.py — At-risk student scoring engine.

Risk score (0–100) per student per term based on weighted factors:
- Overall average below pass mark: 30%
- Number of subjects failed: 25%
- Score trend (negative slope over 2+ terms): 25%
- Class deviation (>1.5 std below class mean): 10%
- Sudden drop (any subject dropped >20 points in one term): 10%

Risk levels: High (≥70), Medium (40–69), Low (<40)
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# ── Recommendation Library ──────────────────────────────────────────

RECOMMENDATIONS = {
    "overall_average": (
        "Schedule a one-on-one meeting with the student to discuss study strategies. "
        "Consider pairing with a stronger peer for study support."
    ),
    "subjects_failed": (
        "Arrange a multi-subject support plan with the class teacher. "
        "Prioritize remedial classes in the weakest subjects."
    ),
    "negative_trend": (
        "Review term-by-term attendance records and check for external disruptions. "
        "Engage the parent or guardian to identify barriers to learning."
    ),
    "class_deviation": (
        "Investigate whether the student requires targeted academic support. "
        "Consider assigning a study buddy within the class."
    ),
    "sudden_drop": (
        "Investigate sudden performance changes — possible causes include "
        "personal issues, teacher changes, or health problems. "
        "Talk to the student privately."
    ),
    "general_high": (
        "This student is at high risk of academic failure. Immediate intervention is recommended: "
        "involve the guidance counselor, parents, and class teacher in a support plan."
    ),
    "general_medium": (
        "This student shows signs of struggling. Monitor closely this term and consider "
        "additional support in weak subjects."
    ),
}


# ── Helpers ─────────────────────────────────────────────────────────

def _find_col(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    cols_lower = {str(c).lower().strip(): c for c in df.columns}
    for a in aliases:
        if a.lower() in cols_lower:
            return cols_lower[a.lower()]
    return None


def _safe_float(val) -> Optional[float]:
    try:
        v = float(val)
        return None if np.isnan(v) or np.isinf(v) else round(v, 2)
    except (TypeError, ValueError):
        return None


def _sanitize(obj):
    """Recursively coerce numpy/pandas scalars to JSON-safe Python types."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return None if (np.isnan(v) or np.isinf(v)) else v
    return obj


# ── Risk Computation ────────────────────────────────────────────────

def compute_risk_scores(df: pd.DataFrame, pass_mark: int = 50) -> Dict[str, Any]:
    """
    Compute risk scores for all students.
    Returns a list of student risk assessments.
    """
    df = df.copy()

    # Ensure percentage column
    if "percentage" not in df.columns:
        score_col = _find_col(df, ["score", "marks", "mark", "total"])
        max_col = _find_col(df, ["max_score", "max_marks", "out_of"])
        if score_col:
            df["score_num"] = pd.to_numeric(df[score_col], errors="coerce")
            if max_col:
                df["max_num"] = pd.to_numeric(df[max_col], errors="coerce")
                mask = df["max_num"].notna() & (df["max_num"] > 0)
                df["percentage"] = np.nan
                df.loc[mask, "percentage"] = (df.loc[mask, "score_num"] / df.loc[mask, "max_num"] * 100).round(2)
                df.loc[~mask, "percentage"] = df.loc[~mask, "score_num"]
            else:
                df["percentage"] = df["score_num"]
    else:
        df["percentage"] = pd.to_numeric(df["percentage"], errors="coerce")

    student_col = _find_col(df, ["student_id", "name", "student_name"])
    subject_col = _find_col(df, ["subject"])
    term_col = _find_col(df, ["term", "semester"])
    class_col = _find_col(df, ["class", "grade", "form"])
    name_col = _find_col(df, ["name", "student_name", "full_name"])

    if not student_col:
        return {"students": [], "summary": {"total": 0}}

    school_average = _safe_float(df["percentage"].dropna().mean())

    # Compute class-level stats for class deviation factor
    class_stats = {}
    if class_col:
        for cls, cgroup in df.groupby(class_col):
            pct = cgroup["percentage"].dropna()
            if len(pct) > 1:
                class_stats[cls] = {"mean": pct.mean(), "std": pct.std()}

    students = []
    student_ids = df[student_col].unique()

    for sid in student_ids:
        sdf = df[df[student_col] == sid]
        pct = sdf["percentage"].dropna()

        if len(pct) == 0:
            continue

        student_mean = pct.mean()
        factors = []
        risk_score = 0.0

        # ── Factor 1: Overall average below pass mark (30%) ────────
        avg_score = 0.0
        if student_mean < pass_mark:
            # Scale: further below = higher risk
            shortfall = pass_mark - student_mean
            avg_score = min(shortfall / pass_mark * 100, 100)
            factors.append({
                "factor": "Overall Average",
                "weight": 30,
                "triggered": True,
                "detail": f"Average is {student_mean:.1f}%, which is {shortfall:.1f} points below pass mark ({pass_mark}%).",
            })
        else:
            factors.append({
                "factor": "Overall Average",
                "weight": 30,
                "triggered": False,
                "detail": f"Average is {student_mean:.1f}%, above pass mark.",
            })
        risk_score += avg_score * 0.30

        # ── Factor 2: Subjects failed (25%) ────────────────────────
        fail_score = 0.0
        if subject_col:
            subject_means = sdf.groupby(subject_col)["percentage"].mean()
            failed_subjects = (subject_means < pass_mark).sum()
            total_subjects = len(subject_means)
            if failed_subjects >= 3:
                fail_score = min(failed_subjects / max(total_subjects, 1) * 100, 100)
                factors.append({
                    "factor": "Subjects Failed",
                    "weight": 25,
                    "triggered": True,
                    "detail": f"Failing {failed_subjects} out of {total_subjects} subjects.",
                    "failed_subjects": [str(s) for s in subject_means[subject_means < pass_mark].index],
                })
            else:
                factors.append({
                    "factor": "Subjects Failed",
                    "weight": 25,
                    "triggered": failed_subjects > 0,
                    "detail": f"Failing {failed_subjects} out of {total_subjects} subjects.",
                })
                if failed_subjects > 0:
                    fail_score = failed_subjects / max(total_subjects, 1) * 50
        risk_score += fail_score * 0.25

        # ── Factor 3: Score trend over terms (25%) ─────────────────
        trend_score = 0.0
        trend_direction = "stable"
        if term_col:
            term_means = sdf.groupby(term_col)["percentage"].mean().sort_index()
            if len(term_means) >= 2:
                x = np.arange(len(term_means))
                y = term_means.values.astype(float)
                slope = np.polyfit(x, y, 1)[0]

                if slope < -3:  # Declining by > 3 points per term
                    trend_score = min(abs(slope) / 10 * 100, 100)
                    trend_direction = "declining"
                    factors.append({
                        "factor": "Score Trend",
                        "weight": 25,
                        "triggered": True,
                        "detail": f"Scores declining at {slope:.1f} points per term.",
                    })
                elif slope > 3:
                    trend_direction = "improving"
                    factors.append({
                        "factor": "Score Trend",
                        "weight": 25,
                        "triggered": False,
                        "detail": f"Scores improving at +{slope:.1f} points per term.",
                    })
                else:
                    factors.append({
                        "factor": "Score Trend",
                        "weight": 25,
                        "triggered": False,
                        "detail": f"Scores relatively stable (slope: {slope:.1f}).",
                    })
            else:
                factors.append({
                    "factor": "Score Trend",
                    "weight": 25,
                    "triggered": False,
                    "detail": "Insufficient terms for trend analysis.",
                })
        risk_score += trend_score * 0.25

        # ── Factor 4: Class deviation (10%) ────────────────────────
        class_dev_score = 0.0
        if class_col and len(sdf) > 0:
            student_class = str(sdf.iloc[0][class_col])
            if student_class in class_stats:
                cs = class_stats[student_class]
                if cs["std"] > 0:
                    deviation = (cs["mean"] - student_mean) / cs["std"]
                    if deviation > 1.5:
                        class_dev_score = min(deviation / 3 * 100, 100)
                        factors.append({
                            "factor": "Class Deviation",
                            "weight": 10,
                            "triggered": True,
                            "detail": f"Performing {deviation:.1f} std deviations below class mean ({cs['mean']:.1f}%).",
                        })
                    else:
                        factors.append({
                            "factor": "Class Deviation",
                            "weight": 10,
                            "triggered": False,
                            "detail": f"Within normal range for class (deviation: {deviation:.1f} std).",
                        })
        risk_score += class_dev_score * 0.10

        # ── Factor 5: Sudden drop (10%) ────────────────────────────
        drop_score = 0.0
        if term_col and subject_col:
            terms = sorted(sdf[term_col].unique())
            if len(terms) >= 2:
                biggest_drop = 0
                drop_subject = None
                for subj in sdf[subject_col].unique():
                    subj_data = sdf[sdf[subject_col] == subj].sort_values(term_col)
                    scores = subj_data["percentage"].values
                    for i in range(1, len(scores)):
                        if pd.notna(scores[i]) and pd.notna(scores[i-1]):
                            drop = float(scores[i-1]) - float(scores[i])
                            if drop > biggest_drop:
                                biggest_drop = drop
                                drop_subject = subj

                if biggest_drop > 20:
                    drop_score = min(biggest_drop / 40 * 100, 100)
                    factors.append({
                        "factor": "Sudden Drop",
                        "weight": 10,
                        "triggered": True,
                        "detail": f"Dropped {biggest_drop:.0f} points in {drop_subject} between terms.",
                    })
                else:
                    factors.append({
                        "factor": "Sudden Drop",
                        "weight": 10,
                        "triggered": False,
                        "detail": f"No sudden drops detected (max: {biggest_drop:.0f} points).",
                    })
        risk_score += drop_score * 0.10

        # ── Final risk level ───────────────────────────────────────
        risk_score = min(round(risk_score, 1), 100)
        if risk_score >= 70:
            risk_level = "High"
        elif risk_score >= 40:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # ── Recommendation ─────────────────────────────────────────
        triggered_factors = [f for f in factors if f["triggered"]]
        if risk_level == "High":
            recommendation = RECOMMENDATIONS["general_high"]
            if triggered_factors:
                top_factor = max(triggered_factors, key=lambda f: f["weight"])
                factor_key = top_factor["factor"].lower().replace(" ", "_")
                if factor_key in RECOMMENDATIONS:
                    recommendation += " " + RECOMMENDATIONS[factor_key]
        elif risk_level == "Medium":
            recommendation = RECOMMENDATIONS["general_medium"]
        else:
            recommendation = "Student is performing satisfactorily. Continue monitoring."

        student_name = str(sdf.iloc[0][name_col]) if name_col else str(sid)

        students.append({
            "student_id": str(sid),
            "name": student_name,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "overall_mean": _safe_float(student_mean),
            "trend_direction": trend_direction,
            "factors": factors,
            "recommendation": recommendation,
            "class": str(sdf.iloc[0][class_col]) if class_col else None,
        })

    # Keep only students below school average AND below pass mark.
    if school_average is not None:
        students = [
            s for s in students
            if (
                s.get("overall_mean") is not None
                and float(s["overall_mean"]) < float(school_average)
                and float(s["overall_mean"]) < float(pass_mark)
            )
        ]

    # Sort by risk score descending
    students.sort(key=lambda s: s["risk_score"], reverse=True)

    # Summary
    high_count = sum(1 for s in students if s["risk_level"] == "High")
    medium_count = sum(1 for s in students if s["risk_level"] == "Medium")
    low_count = sum(1 for s in students if s["risk_level"] == "Low")

    return _sanitize({
        "students": students,
        "summary": {
            "total": len(students),
            "high_risk": high_count,
            "medium_risk": medium_count,
            "low_risk": low_count,
            "school_average": school_average,
            "high_risk_pct": _safe_float(high_count / len(students) * 100) if students else 0,
        },
    })
