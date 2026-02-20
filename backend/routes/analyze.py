"""
Analyze routes — analytics API endpoints.
"""

import os
from fastapi import APIRouter, HTTPException
import pandas as pd

from core.stats import (
    compute_overview, compute_subject_stats,
    compute_student_profile, compute_term_comparison,
)
from core.risk import compute_risk_scores
from core.gaps import compute_gap_analysis
from core.insights import generate_all_insights
from core.ai_insights import generate_parent_summary
from core.kenya_grading import get_all_grade_thresholds

router = APIRouter()

PASS_MARK = int(os.getenv("PASS_MARK", "50"))


def _df_from_payload(payload: dict) -> pd.DataFrame:
    """Extract DataFrame from request payload."""
    data = payload.get("data")
    if not data:
        raise HTTPException(400, "No data provided.")
    return pd.DataFrame(data)


@router.post("/overview")
async def overview(payload: dict):
    """School overview: totals, means, distributions, top/bottom lists."""
    df = _df_from_payload(payload)
    return compute_overview(df, pass_mark=PASS_MARK)


@router.post("/subjects")
async def subjects(payload: dict):
    """Per-subject statistics: mean, median, std, pass rate, correlations."""
    df = _df_from_payload(payload)
    return compute_subject_stats(df, pass_mark=PASS_MARK)


@router.post("/risk")
async def risk(payload: dict):
    """At-risk student detection with risk scores and recommendations."""
    df = _df_from_payload(payload)
    return compute_risk_scores(df, pass_mark=PASS_MARK)


@router.post("/gaps")
async def gaps(payload: dict):
    """Gap analysis: gender, class, regional, term."""
    df = _df_from_payload(payload)
    return compute_gap_analysis(df, pass_mark=PASS_MARK)


@router.post("/insights")
async def insights(payload: dict):
    """Generate all rule-based insights."""
    df = _df_from_payload(payload)
    return generate_all_insights(df, pass_mark=PASS_MARK)


@router.post("/student/{student_id}")
async def student_profile(student_id: str, payload: dict):
    """Individual student profile: scores, trends, risk, rank."""
    df = _df_from_payload(payload)
    result = compute_student_profile(df, student_id, pass_mark=PASS_MARK)
    if result is None:
        raise HTTPException(404, f"Student '{student_id}' not found.")
    return result


@router.post("/ai/parent-summary/{student_id}")
async def ai_parent_summary(student_id: str, payload: dict):
    """
    Parent-friendly student summary.
    Uses deterministic fallback by default unless AI is enabled by env vars.
    """
    df = _df_from_payload(payload)
    result = generate_parent_summary(df, student_id, pass_mark=PASS_MARK)
    if result.get("error") == "student_not_found":
        raise HTTPException(404, f"Student '{student_id}' not found.")
    return result


@router.post("/term-comparison")
async def term_comparison(payload: dict):
    """
    3-term comparison: per-student/subject/class deltas and trends.
    Uses a universal global grading scale.
    """
    df = _df_from_payload(payload)
    return compute_term_comparison(df, pass_mark=PASS_MARK)


@router.get("/school-modes")
async def school_modes():
    """Return universal grading metadata."""
    return {
        "school_types": [
            {
                "id": "universal",
                "label": "Universal (A-F)",
                "pass_mark": PASS_MARK,
                "grade_scale": get_all_grade_thresholds("universal"),
                "subjects": [],
            }
        ]
    }
