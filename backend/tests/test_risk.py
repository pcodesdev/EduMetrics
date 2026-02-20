"""
Tests for core/risk.py — risk scoring against known inputs.
"""

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.risk import compute_risk_scores
from core.parser import parse_upload

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_school.csv")
PASS_MARK = 50


@pytest.fixture
def sample_df():
    sheets = parse_upload(SAMPLE_CSV)
    return list(sheets.values())[0]


class TestComputeRiskScores:
    """Tests for the risk scoring engine."""

    def test_returns_dict(self, sample_df):
        result = compute_risk_scores(sample_df, pass_mark=PASS_MARK)
        assert isinstance(result, dict)

    def test_has_at_risk_students(self, sample_df):
        result = compute_risk_scores(sample_df, pass_mark=PASS_MARK)
        assert "at_risk_students" in result or "students" in result

    def test_at_risk_list_not_empty(self, sample_df):
        """Sample data contains students with low scores — there should be at-risk students."""
        result = compute_risk_scores(sample_df, pass_mark=PASS_MARK)
        students = result.get("at_risk_students") or result.get("students") or []
        assert len(students) > 0, "Expected at least one at-risk student in sample data"

    def test_known_low_scorer_is_at_risk(self, sample_df):
        """Nelson Kibet (S014) has scores around 25-40 — should be at risk."""
        result = compute_risk_scores(sample_df, pass_mark=PASS_MARK)
        students = result.get("at_risk_students") or result.get("students") or []
        ids = [s.get("student_id") for s in students]
        names = [s.get("student_name", "").lower() for s in students]
        assert "S014" in ids or any("nelson" in n for n in names), \
            "Nelson Kibet (S014) should be at-risk"

    def test_known_high_scorer_not_at_risk(self, sample_df):
        """Karen Wanjiku (S011) has scores 85-96 — should NOT be at risk."""
        result = compute_risk_scores(sample_df, pass_mark=PASS_MARK)
        students = result.get("at_risk_students") or result.get("students") or []
        ids = [s.get("student_id") for s in students]
        # S011's risk level should be low/none, or she shouldn't be in the high-risk list
        s011 = [s for s in students if s.get("student_id") == "S011"]
        if s011:
            level = s011[0].get("risk_level", "").lower()
            assert level in ("low", "none", ""), \
                f"Karen Wanjiku (S011) should not be high-risk, got: {level}"

    def test_risk_levels_are_valid(self, sample_df):
        result = compute_risk_scores(sample_df, pass_mark=PASS_MARK)
        students = result.get("at_risk_students") or result.get("students") or []
        valid_levels = {"high", "medium", "low", "none", ""}
        for s in students:
            level = s.get("risk_level", "").lower()
            assert level in valid_levels, f"Invalid risk level: {level}"

    def test_students_returned_are_below_school_average(self, sample_df):
        result = compute_risk_scores(sample_df, pass_mark=PASS_MARK)
        students = result.get("at_risk_students") or result.get("students") or []
        school_avg = (result.get("summary") or {}).get("school_average")
        if school_avg is not None:
            for s in students:
                mean = s.get("overall_mean")
                if mean is not None:
                    assert float(mean) < float(school_avg)

    def test_students_returned_are_below_pass_mark(self, sample_df):
        result = compute_risk_scores(sample_df, pass_mark=PASS_MARK)
        students = result.get("at_risk_students") or result.get("students") or []
        for s in students:
            mean = s.get("overall_mean")
            if mean is not None:
                assert float(mean) < float(PASS_MARK)
