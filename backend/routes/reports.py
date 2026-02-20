"""
Report routes — PDF and Excel report generation endpoints.
"""

import os
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
import pandas as pd

from core.report_builder import (
    generate_school_report_pdf,
    generate_class_report_pdf,
    generate_student_report_pdf,
    generate_excel_export,
)
from core.stats import compute_overview, compute_subject_stats
from core.risk import compute_risk_scores
from core.gaps import compute_gap_analysis
from core.insights import generate_all_insights

router = APIRouter()

PASS_MARK = int(os.getenv("PASS_MARK", "50"))
SCHOOL_NAME = os.getenv("SCHOOL_NAME", "My School")
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
REPORTS_DIR = UPLOAD_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_school_name(df: pd.DataFrame) -> str:
    """Prefer school name from uploaded data; fallback to env config."""
    for col in ["school", "school_name", "institution"]:
        if col in df.columns:
            vals = df[col].dropna().astype(str).str.strip()
            if not vals.empty:
                top = vals[vals != ""]
                if not top.empty:
                    return str(top.mode().iloc[0])
    return SCHOOL_NAME


def _safe_token(value: str, fallback: str = "item") -> str:
    """Create filesystem-safe token for filenames."""
    token = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._-")
    return token or fallback


def _safe_unlink(path: str):
    """Best-effort file deletion after response is sent."""
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


@router.post("/school-pdf")
async def school_report_pdf(payload: dict):
    """Generate a full school performance report PDF."""
    data = payload.get("data")
    if not data:
        raise HTTPException(400, "No data provided.")

    df = pd.DataFrame(data)
    school_name = _resolve_school_name(df)
    report_id = str(uuid.uuid4())[:8]
    output_path = REPORTS_DIR / f"school_report_{report_id}.pdf"

    overview = compute_overview(df, pass_mark=PASS_MARK)
    subject_stats = compute_subject_stats(df, pass_mark=PASS_MARK)
    risk_data = compute_risk_scores(df, pass_mark=PASS_MARK)
    gap_data = compute_gap_analysis(df, pass_mark=PASS_MARK)
    insights = generate_all_insights(df, pass_mark=PASS_MARK)

    generate_school_report_pdf(
        output_path=str(output_path),
        school_name=school_name,
        overview=overview,
        subject_stats=subject_stats,
        risk_data=risk_data,
        gap_data=gap_data,
        insights=insights,
        pass_mark=PASS_MARK,
        school_system="universal",
    )

    return FileResponse(
        str(output_path),
        media_type="application/pdf",
        filename=f"EduMetrics_School_Report_{report_id}.pdf",
        background=BackgroundTask(_safe_unlink, str(output_path)),
    )


@router.post("/class-pdf")
async def class_report_pdf(payload: dict):
    """Generate merged class performance report PDF (school + class context)."""
    data = payload.get("data")
    class_name = payload.get("class_name")
    if not data or not class_name:
        raise HTTPException(400, "Provide 'data' and 'class_name'.")

    df = pd.DataFrame(data)
    school_name = _resolve_school_name(df)

    # Filter to the specified class
    class_col = None
    for col in ["class", "grade", "stream", "form"]:
        if col in df.columns:
            class_col = col
            break

    if class_col is None:
        raise HTTPException(400, "No class/grade column found in data.")

    class_df = df[df[class_col].astype(str).str.strip().str.lower() == str(class_name).strip().lower()]
    if class_df.empty:
        raise HTTPException(404, f"No data found for class '{class_name}'.")

    report_id = str(uuid.uuid4())[:8]
    class_token = _safe_token(class_name, fallback="class")
    output_path = REPORTS_DIR / f"class_report_{class_token}_{report_id}.pdf"

    generate_class_report_pdf(
        output_path=str(output_path),
        school_name=school_name,
        class_name=class_name,
        class_df=class_df,
        school_df=df,
        pass_mark=PASS_MARK,
    )

    return FileResponse(
        str(output_path),
        media_type="application/pdf",
        filename=f"EduMetrics_Class_Performance_{class_token}_{report_id}.pdf",
        background=BackgroundTask(_safe_unlink, str(output_path)),
    )


@router.post("/student-pdf")
async def student_report_pdf(payload: dict):
    """Generate an individual student report card PDF."""
    data = payload.get("data")
    student_id = payload.get("student_id")
    if not data or not student_id:
        raise HTTPException(400, "Provide 'data' and 'student_id'.")

    df = pd.DataFrame(data)
    school_name = _resolve_school_name(df)
    report_id = str(uuid.uuid4())[:8]
    student_token = _safe_token(student_id, fallback="student")
    output_path = REPORTS_DIR / f"student_report_{student_token}_{report_id}.pdf"

    generate_student_report_pdf(
        output_path=str(output_path),
        school_name=school_name,
        student_id=student_id,
        df=df,
        pass_mark=PASS_MARK,
    )

    return FileResponse(
        str(output_path),
        media_type="application/pdf",
        filename=f"EduMetrics_Student_{student_token}_{report_id}.pdf",
        background=BackgroundTask(_safe_unlink, str(output_path)),
    )


@router.post("/excel")
async def excel_export(payload: dict):
    """Export cleaned data with computed columns as an Excel workbook."""
    data = payload.get("data")
    if not data:
        raise HTTPException(400, "No data provided.")

    df = pd.DataFrame(data)
    school_name = _resolve_school_name(df)
    report_id = str(uuid.uuid4())[:8]
    output_path = REPORTS_DIR / f"edumetrics_export_{report_id}.xlsx"

    generate_excel_export(
        output_path=str(output_path),
        df=df,
        school_name=school_name,
        pass_mark=PASS_MARK,
    )

    return FileResponse(
        str(output_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"EduMetrics_Export_{report_id}.xlsx",
        background=BackgroundTask(_safe_unlink, str(output_path)),
    )
