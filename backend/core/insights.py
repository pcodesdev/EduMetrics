"""
insights.py — Rule-based insight generation engine.

Evaluates statistics from stats.py, risk.py, and gaps.py against a
configurable rule library.  Each rule produces structured insight objects
with: id, category, severity, title, narrative, supporting_data,
recommendation.

Categories: performance, gap, at_risk, positive, correlation.
Severity levels: info, warning, critical.

Zero AI dependency — every insight is a deterministic threshold check.
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from core.stats import compute_overview, compute_subject_stats
from core.risk import compute_risk_scores
from core.gaps import compute_gap_analysis
from core.narrative import (
    narrate_low_overall_mean,
    narrate_high_overall_mean,
    narrate_high_fail_rate,
    narrate_weakest_subject,
    narrate_strongest_subject,
    narrate_subject_high_fail_rate,
    narrate_gender_gap,
    narrate_class_gap,
    narrate_term_gap,
    narrate_regional_gap,
    narrate_risk_summary,
    narrate_class_risk_cluster,
    narrate_top_performer,
    narrate_most_improved,
    narrate_strong_subject,
    narrate_improving_trend,
    narrate_strong_correlation,
    generate_executive_summary,
)


# ── Helpers ─────────────────────────────────────────────────────────

def _safe_float(val) -> float:
    try:
        v = float(val)
        return 0.0 if (np.isnan(v) or np.isinf(v)) else round(v, 2)
    except (TypeError, ValueError):
        return 0.0


def _find_col(df: pd.DataFrame, aliases: list) -> str | None:
    cols_lower = {str(c).lower().strip(): c for c in df.columns}
    for a in aliases:
        if a.lower() in cols_lower:
            return cols_lower[a.lower()]
    return None


# ── Performance Insights ────────────────────────────────────────────

def _performance_insights(
    overview: Dict[str, Any],
    subject_stats: Dict[str, Any],
    pass_mark: int,
) -> List[Dict[str, Any]]:
    """Generate insights about overall and subject-level performance."""
    insights: List[Dict[str, Any]] = []
    overall_mean = _safe_float(overview.get("overall_mean", 0))
    fail_rate = _safe_float(overview.get("fail_rate", 0))
    total_records = overview.get("total_records", 0)
    fail_count = overview.get("fail_count", 0)

    # Rule 1: Overall mean below pass mark
    if overall_mean < pass_mark:
        severity = "critical" if overall_mean < pass_mark - 15 else "warning"
        insights.append({
            "id": "perf_low_overall_mean",
            "category": "performance",
            "severity": severity,
            "title": "Below-Average School Performance",
            "narrative": narrate_low_overall_mean(overall_mean, pass_mark),
            "supporting_data": {
                "overall_mean": overall_mean,
                "pass_mark": pass_mark,
                "shortfall": round(pass_mark - overall_mean, 1),
            },
            "recommendation": (
                "Conduct a school-wide academic review. Focus remedial "
                "resources on the weakest subjects and lowest-performing "
                "classes. Consider teacher training and curriculum adjustments."
            ),
        })
    else:
        insights.append({
            "id": "perf_good_overall_mean",
            "category": "performance",
            "severity": "info",
            "title": "School Performance Above Pass Mark",
            "narrative": narrate_high_overall_mean(overall_mean, pass_mark),
            "supporting_data": {
                "overall_mean": overall_mean,
                "pass_mark": pass_mark,
                "surplus": round(overall_mean - pass_mark, 1),
            },
            "recommendation": (
                "Maintain current strategies and focus on raising "
                "lower-performing subjects and students closer to the top."
            ),
        })

    # Rule 2: High fail rate (> 40%)
    if fail_rate > 40:
        severity = "critical" if fail_rate > 60 else "warning"
        insights.append({
            "id": "perf_high_fail_rate",
            "category": "performance",
            "severity": severity,
            "title": "High Overall Failure Rate",
            "narrative": narrate_high_fail_rate(
                fail_rate, fail_count, total_records
            ),
            "supporting_data": {
                "fail_rate": fail_rate,
                "fail_count": fail_count,
                "total_records": total_records,
            },
            "recommendation": (
                "Introduce after-school revision sessions and peer tutoring. "
                "Review assessment difficulty and grading standards."
            ),
        })

    # Rule 3: Weakest subject (more than 10 points below school mean)
    subjects = subject_stats.get("subjects", [])
    if subjects and overall_mean > 0:
        weakest = subjects[-1]  # Already sorted by mean descending
        weakest_mean = _safe_float(weakest.get("mean", 0))
        if overall_mean - weakest_mean > 10:
            insights.append({
                "id": "perf_weakest_subject",
                "category": "performance",
                "severity": "warning",
                "title": f"Weak Subject: {weakest['subject']}",
                "narrative": narrate_weakest_subject(
                    weakest["subject"], weakest_mean, overall_mean
                ),
                "supporting_data": {
                    "subject": weakest["subject"],
                    "subject_mean": weakest_mean,
                    "school_mean": overall_mean,
                    "gap": round(overall_mean - weakest_mean, 1),
                },
                "recommendation": (
                    f"Arrange targeted support for {weakest['subject']}: "
                    f"teacher coaching, extra tutorials, and updated learning materials."
                ),
            })

    # Rule 4: Subjects with > 50% fail rate
    for subj in subjects:
        subj_fail_rate = _safe_float(subj.get("fail_rate", 0))
        if subj_fail_rate > 50:
            insights.append({
                "id": f"perf_subject_high_fail_{subj['subject'].lower().replace(' ', '_')}",
                "category": "performance",
                "severity": "critical" if subj_fail_rate > 70 else "warning",
                "title": f"High Failure Rate in {subj['subject']}",
                "narrative": narrate_subject_high_fail_rate(
                    subj["subject"], subj_fail_rate
                ),
                "supporting_data": {
                    "subject": subj["subject"],
                    "fail_rate": subj_fail_rate,
                    "fail_count": subj.get("fail_count", 0),
                    "total": subj.get("count", 0),
                },
                "recommendation": (
                    f"Review {subj['subject']} curriculum delivery. "
                    f"Consider remedial classes and diagnostic assessments."
                ),
            })

    return insights


# ── Gap Insights ────────────────────────────────────────────────────

def _gap_insights(gap_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate insights from gender, class, regional, and term gaps."""
    insights: List[Dict[str, Any]] = []

    # Gender gaps — only surfaces when statistically significant
    for gap in gap_data.get("gender_gaps", []):
        if gap.get("statistically_significant"):
            effect = gap.get("effect_size_label", "")
            severity = "critical" if effect in ("large", "medium") else "warning"
            label = gap.get("label", "Overall")
            insights.append({
                "id": f"gap_gender_{label.lower().replace(' ', '_')}",
                "category": "gap",
                "severity": severity,
                "title": f"Gender Gap: {label}",
                "narrative": narrate_gender_gap(gap),
                "supporting_data": gap,
                "recommendation": (
                    "Investigate root causes of the gender disparity. "
                    "Consider gender-responsive teaching strategies, "
                    "mentoring programmes, and equitable classroom engagement."
                ),
            })

    # Class gaps
    for gap in gap_data.get("class_gaps", []):
        if gap.get("statistically_significant"):
            gap_val = _safe_float(gap.get("gap", 0))
            severity = "critical" if gap_val > 15 else "warning"
            insights.append({
                "id": "gap_class",
                "category": "gap",
                "severity": severity,
                "title": "Significant Class Performance Gap",
                "narrative": narrate_class_gap(gap),
                "supporting_data": gap,
                "recommendation": (
                    "Review class allocations, teacher assignments, and "
                    "resource distribution. Consider sharing best practices "
                    "from the top class with others."
                ),
            })

    # Regional gaps
    for gap in gap_data.get("regional_gaps", []):
        if gap.get("statistically_significant"):
            gap_val = _safe_float(gap.get("gap", 0))
            severity = "critical" if gap_val > 20 else "warning"
            insights.append({
                "id": "gap_regional",
                "category": "gap",
                "severity": severity,
                "title": "Regional Performance Disparity",
                "narrative": narrate_regional_gap(gap),
                "supporting_data": gap,
                "recommendation": (
                    "Allocate additional resources to underperforming regions. "
                    "Facilitate inter-school knowledge sharing."
                ),
            })

    # Term gaps (always surfaced if meaningful)
    for gap in gap_data.get("term_gaps", []):
        gap_val = _safe_float(gap.get("gap", 0))
        if gap_val > 5:
            severity = "warning" if gap_val > 10 else "info"
            insights.append({
                "id": "gap_term",
                "category": "gap",
                "severity": severity,
                "title": "Term Performance Variation",
                "narrative": narrate_term_gap(gap),
                "supporting_data": gap,
                "recommendation": (
                    "Align curriculum pacing across terms. Investigate "
                    "whether external factors contribute to term dips."
                ),
            })

    return insights


# ── At-Risk Insights ────────────────────────────────────────────────

def _at_risk_insights(
    risk_data: Dict[str, Any],
    df: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """Generate insights about at-risk student patterns."""
    insights: List[Dict[str, Any]] = []
    summary = risk_data.get("summary", {})
    students = risk_data.get("students", [])
    total = summary.get("total", 0)
    high = summary.get("high_risk", 0)
    medium = summary.get("medium_risk", 0)
    high_pct = _safe_float(summary.get("high_risk_pct", 0))

    if total == 0:
        return insights

    # Rule 1: High-risk student proportion
    if high > 0:
        if high_pct > 25:
            severity = "critical"
        elif high_pct > 15:
            severity = "warning"
        else:
            severity = "info"

        insights.append({
            "id": "risk_summary",
            "category": "at_risk",
            "severity": severity,
            "title": f"{high} Student(s) at High Risk",
            "narrative": narrate_risk_summary(total, high, medium, high_pct),
            "supporting_data": {
                "total_students": total,
                "high_risk": high,
                "medium_risk": medium,
                "high_risk_pct": high_pct,
            },
            "recommendation": (
                "Create individual intervention plans for all high-risk students. "
                "Involve parents, counsellors, and class teachers."
            ),
        })

    # Rule 2: Class-level risk clusters (3+ high-risk in one class)
    class_col = _find_col(df, ["class", "grade", "form", "stream"])
    if class_col:
        high_risk_students = [s for s in students if s.get("risk_level") == "High"]
        class_risk: Dict[str, int] = {}
        class_total: Dict[str, int] = {}
        for stud in students:
            cls = stud.get("class")
            if cls:
                class_total[cls] = class_total.get(cls, 0) + 1
        for stud in high_risk_students:
            cls = stud.get("class")
            if cls:
                class_risk[cls] = class_risk.get(cls, 0) + 1

        for cls, count in class_risk.items():
            if count >= 3:
                insights.append({
                    "id": f"risk_cluster_{cls.lower().replace(' ', '_')}",
                    "category": "at_risk",
                    "severity": "critical",
                    "title": f"Risk Cluster in {cls}",
                    "narrative": narrate_class_risk_cluster(
                        cls, count, class_total.get(cls, 0)
                    ),
                    "supporting_data": {
                        "class": cls,
                        "high_risk_count": count,
                        "total_in_class": class_total.get(cls, 0),
                    },
                    "recommendation": (
                        f"Conduct a class-level review for {cls}. "
                        f"Investigate shared barriers and consider class-wide support."
                    ),
                })

    return insights


# ── Positive Insights ───────────────────────────────────────────────

def _positive_insights(
    overview: Dict[str, Any],
    subject_stats: Dict[str, Any],
    risk_data: Dict[str, Any],
    df: pd.DataFrame,
    pass_mark: int,
) -> List[Dict[str, Any]]:
    """Generate insights celebrating achievements and improvements."""
    insights: List[Dict[str, Any]] = []

    # Rule 1: Top performers (students with mean > 80%)
    top_students = overview.get("top_students", [])
    for stud in top_students[:3]:
        mean = _safe_float(stud.get("mean", 0))
        if mean >= 80:
            insights.append({
                "id": f"pos_top_{stud['name'].lower().replace(' ', '_')}",
                "category": "positive",
                "severity": "info",
                "title": f"Top Performer: {stud['name']}",
                "narrative": narrate_top_performer(stud["name"], mean),
                "supporting_data": {
                    "student": stud["name"],
                    "mean": mean,
                },
                "recommendation": (
                    "Recognise this student publicly. Consider peer mentoring "
                    "roles and academic enrichment opportunities."
                ),
            })

    # Rule 2: Improving students (positive trend > 3 pts/term)
    term_col = _find_col(df, ["term", "semester"])
    student_col = _find_col(df, ["student_id", "name", "student_name"])
    if term_col and student_col and "percentage" not in df.columns:
        # Ensure percentage exists
        df_copy = df.copy()
        score_col = _find_col(df_copy, ["score", "marks", "mark", "total"])
        max_col = _find_col(df_copy, ["max_score", "max_marks", "out_of"])
        if score_col:
            df_copy["score_num"] = pd.to_numeric(df_copy[score_col], errors="coerce")
            if max_col:
                df_copy["max_num"] = pd.to_numeric(df_copy[max_col], errors="coerce")
                mask = df_copy["max_num"].notna() & (df_copy["max_num"] > 0)
                df_copy["percentage"] = np.nan
                df_copy.loc[mask, "percentage"] = (
                    df_copy.loc[mask, "score_num"] / df_copy.loc[mask, "max_num"] * 100
                )
                df_copy.loc[~mask, "percentage"] = df_copy.loc[~mask, "score_num"]
            else:
                df_copy["percentage"] = df_copy["score_num"]
    elif "percentage" in df.columns:
        df_copy = df.copy()
        df_copy["percentage"] = pd.to_numeric(df_copy["percentage"], errors="coerce")
    else:
        df_copy = None

    if df_copy is not None and term_col and student_col:
        from core.kenya_grading import sort_terms
        for sid in df_copy[student_col].unique():
            sdf = df_copy[df_copy[student_col] == sid]
            term_means = sdf.groupby(term_col)["percentage"].mean()
            ordered_terms = sort_terms([str(t) for t in term_means.index.tolist()])
            ordered_values = [term_means.get(t) for t in ordered_terms if pd.notna(term_means.get(t))]
            if len(ordered_values) >= 2:
                x = np.arange(len(ordered_values))
                y = np.array(ordered_values, dtype=float)
                slope = float(np.polyfit(x, y, 1)[0])
                if slope > 3:
                    name_col = _find_col(df_copy, ["name", "student_name", "full_name"])
                    student_name = str(sdf.iloc[0][name_col]) if name_col else str(sid)
                    insights.append({
                        "id": f"pos_improving_{str(sid).lower().replace(' ', '_')}",
                        "category": "positive",
                        "severity": "info",
                        "title": f"Most Improved: {student_name}",
                        "narrative": narrate_most_improved(student_name, slope),
                        "supporting_data": {
                            "student": student_name,
                            "slope": round(slope, 1),
                        },
                        "recommendation": (
                            "Acknowledge this student's progress. "
                            "Identify the factors behind their improvement."
                        ),
                    })

    # Rule 3: Strong subjects (pass rate > 85%)
    for subj in subject_stats.get("subjects", []):
        pass_rate = _safe_float(subj.get("pass_rate", 0))
        if pass_rate >= 85:
            insights.append({
                "id": f"pos_strong_{subj['subject'].lower().replace(' ', '_')}",
                "category": "positive",
                "severity": "info",
                "title": f"Strong Subject: {subj['subject']}",
                "narrative": narrate_strong_subject(subj["subject"], pass_rate),
                "supporting_data": {
                    "subject": subj["subject"],
                    "pass_rate": pass_rate,
                },
                "recommendation": (
                    f"Document and share {subj['subject']} teaching strategies "
                    f"with other departments."
                ),
            })

    # Rule 4: Improving overall trend (last term better than first)
    term_trends = overview.get("term_trends", [])
    if len(term_trends) >= 2:
        first = term_trends[0]
        last = term_trends[-1]
        first_mean = _safe_float(first.get("mean", 0))
        last_mean = _safe_float(last.get("mean", 0))
        if last_mean > first_mean + 2:
            insights.append({
                "id": "pos_improving_trend",
                "category": "positive",
                "severity": "info",
                "title": "Positive Performance Trend",
                "narrative": narrate_improving_trend(
                    last["term"], last_mean, first["term"], first_mean
                ),
                "supporting_data": {
                    "first_term": first["term"],
                    "first_mean": first_mean,
                    "last_term": last["term"],
                    "last_mean": last_mean,
                    "improvement": round(last_mean - first_mean, 1),
                },
                "recommendation": (
                    "Continue the strategies that contributed to this "
                    "positive trajectory."
                ),
            })

    return insights


# ── Correlation Insights ────────────────────────────────────────────

def _correlation_insights(
    subject_stats: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate insights about subject correlations."""
    insights: List[Dict[str, Any]] = []
    corr = subject_stats.get("correlation_matrix", {})
    pairs = corr.get("pairs", [])

    for pair in pairs:
        r = _safe_float(pair.get("r", 0))
        p = _safe_float(pair.get("p_value", 1))
        if abs(r) > 0.6 and p < 0.05:
            subj_a = pair["subject_a"]
            subj_b = pair["subject_b"]
            insights.append({
                "id": f"corr_{subj_a.lower().replace(' ', '_')}_{subj_b.lower().replace(' ', '_')}",
                "category": "correlation",
                "severity": "info",
                "title": f"Strong Correlation: {subj_a} ↔ {subj_b}",
                "narrative": narrate_strong_correlation(subj_a, subj_b, r, p),
                "supporting_data": {
                    "subject_a": subj_a,
                    "subject_b": subj_b,
                    "r": r,
                    "p_value": p,
                },
                "recommendation": (
                    f"Explore cross-curricular links between {subj_a} and "
                    f"{subj_b}. If one is strong and the other weak, "
                    f"leverage the stronger for scaffolding."
                ),
            })

    return insights


# ── Main Entry Point ───────────────────────────────────────────────

def generate_all_insights(
    df: pd.DataFrame, pass_mark: int = 50
) -> Dict[str, Any]:
    """
    Generate all rule-based insights.

    Returns:
        {
            "insights": [...],          # List of insight dicts
            "summary": {                # Counts by category/severity
                "total": int,
                "by_category": {...},
                "by_severity": {...},
            },
            "executive_summary": str,   # Human-readable paragraph
        }
    """
    # Compute all upstream analytics
    overview = compute_overview(df, pass_mark=pass_mark)
    subject_stats = compute_subject_stats(df, pass_mark=pass_mark)
    risk_data = compute_risk_scores(df, pass_mark=pass_mark)
    gap_data = compute_gap_analysis(df, pass_mark=pass_mark)

    # Collect insights from every category
    all_insights: List[Dict[str, Any]] = []
    all_insights.extend(_performance_insights(overview, subject_stats, pass_mark))
    all_insights.extend(_gap_insights(gap_data))
    all_insights.extend(_at_risk_insights(risk_data, df))
    all_insights.extend(
        _positive_insights(overview, subject_stats, risk_data, df, pass_mark)
    )
    all_insights.extend(_correlation_insights(subject_stats))

    # Sort: critical first, then warning, then info
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    all_insights.sort(key=lambda i: severity_order.get(i.get("severity", "info"), 9))

    # Build summary counts
    by_category: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    for insight in all_insights:
        cat = insight.get("category", "unknown")
        sev = insight.get("severity", "info")
        by_category[cat] = by_category.get(cat, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1

    return {
        "insights": all_insights,
        "summary": {
            "total": len(all_insights),
            "by_category": by_category,
            "by_severity": by_severity,
        },
        "executive_summary": generate_executive_summary(all_insights),
    }
