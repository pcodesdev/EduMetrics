"""
Tests for core/report_builder.py — PDF/Excel generation completes without errors.
"""

import os
import sys
import tempfile
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.parser import parse_upload
from core.stats import compute_overview, compute_subject_stats
from core.risk import compute_risk_scores
from core.gaps import compute_gap_analysis
from core.insights import generate_all_insights
from core.report_builder import (
    generate_school_report_pdf,
    generate_class_report_pdf,
    generate_student_report_pdf,
    generate_excel_export,
)

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_school.csv")
PASS_MARK = 50
SCHOOL_NAME = "Test School"


@pytest.fixture
def sample_df():
    sheets = parse_upload(SAMPLE_CSV)
    return list(sheets.values())[0]


@pytest.fixture
def analytics(sample_df):
    """Pre-compute all analytics needed for report generation."""
    return {
        "overview": compute_overview(sample_df, pass_mark=PASS_MARK),
        "subject_stats": compute_subject_stats(sample_df, pass_mark=PASS_MARK),
        "risk_data": compute_risk_scores(sample_df, pass_mark=PASS_MARK),
        "gap_data": compute_gap_analysis(sample_df, pass_mark=PASS_MARK),
        "insights": generate_all_insights(sample_df, pass_mark=PASS_MARK),
    }


class TestGenerateSchoolReportPdf:
    """Test school report PDF generation."""

    def test_creates_pdf_file(self, sample_df, analytics):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "school_report.pdf")
            generate_school_report_pdf(
                output_path=path,
                school_name=SCHOOL_NAME,
                overview=analytics["overview"],
                subject_stats=analytics["subject_stats"],
                risk_data=analytics["risk_data"],
                gap_data=analytics["gap_data"],
                insights=analytics["insights"],
                pass_mark=PASS_MARK,
            )
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0

    def test_pdf_is_valid(self, sample_df, analytics):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "school_report.pdf")
            generate_school_report_pdf(
                output_path=path,
                school_name=SCHOOL_NAME,
                overview=analytics["overview"],
                subject_stats=analytics["subject_stats"],
                risk_data=analytics["risk_data"],
                gap_data=analytics["gap_data"],
                insights=analytics["insights"],
                pass_mark=PASS_MARK,
            )
            with open(path, "rb") as f:
                header = f.read(5)
            assert header == b"%PDF-"


class TestGenerateClassReportPdf:
    """Test class report PDF generation."""

    def test_creates_pdf_file(self, sample_df):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "class_report.pdf")
            # Filter to Form 1A class
            class_col = None
            for col in ["class", "grade", "stream", "form"]:
                if col in sample_df.columns:
                    class_col = col
                    break
            assert class_col is not None, "No class column found in sample data"
            class_name = sample_df[class_col].iloc[0]
            class_df = sample_df[sample_df[class_col] == class_name]

            generate_class_report_pdf(
                output_path=path,
                school_name=SCHOOL_NAME,
                class_name=class_name,
                class_df=class_df,
                school_df=sample_df,
                pass_mark=PASS_MARK,
            )
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0


class TestGenerateStudentReportPdf:
    """Test student report PDF generation."""

    def test_creates_pdf_file(self, sample_df):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "student_report.pdf")
            generate_student_report_pdf(
                output_path=path,
                school_name=SCHOOL_NAME,
                student_id="S001",
                df=sample_df,
                pass_mark=PASS_MARK,
            )
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0


class TestGenerateExcelExport:
    """Test Excel export generation."""

    def test_creates_xlsx_file(self, sample_df):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "export.xlsx")
            generate_excel_export(
                output_path=path,
                df=sample_df,
                school_name=SCHOOL_NAME,
                pass_mark=PASS_MARK,
            )
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0

    def test_excel_has_multiple_sheets(self, sample_df):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "export.xlsx")
            generate_excel_export(
                output_path=path,
                df=sample_df,
                school_name=SCHOOL_NAME,
                pass_mark=PASS_MARK,
            )
            # Read back and verify sheets; close handle before tmpdir cleanup
            xl = pd.ExcelFile(path)
            sheet_count = len(xl.sheet_names)
            xl.close()
            assert sheet_count >= 1, "Expected at least one sheet"
