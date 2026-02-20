"""
Tests for core/stats.py — compute_overview, compute_subject_stats, compute_student_profile.
"""

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.stats import (
    compute_overview,
    compute_subject_stats,
    compute_student_profile,
    compute_term_comparison,
)
from core.parser import parse_upload

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_school.csv")
PASS_MARK = 50


@pytest.fixture
def sample_df():
    """Load sample data for testing."""
    sheets = parse_upload(SAMPLE_CSV)
    return list(sheets.values())[0]


class TestComputeOverview:
    """Tests for compute_overview."""

    def test_returns_dict(self, sample_df):
        result = compute_overview(sample_df, pass_mark=PASS_MARK)
        assert isinstance(result, dict)

    def test_has_total_students(self, sample_df):
        result = compute_overview(sample_df, pass_mark=PASS_MARK)
        assert "total_students" in result or "total_records" in result

    def test_has_mean(self, sample_df):
        result = compute_overview(sample_df, pass_mark=PASS_MARK)
        assert "mean" in result or "average" in result or "school_mean" in result or "overall_mean" in result

    def test_mean_is_numeric(self, sample_df):
        result = compute_overview(sample_df, pass_mark=PASS_MARK)
        mean_val = result.get("mean") or result.get("average") or result.get("school_mean") or result.get("overall_mean")
        if mean_val is not None:
            assert isinstance(mean_val, (int, float))

    def test_mean_in_valid_range(self, sample_df):
        result = compute_overview(sample_df, pass_mark=PASS_MARK)
        mean_val = result.get("mean") or result.get("average") or result.get("school_mean") or result.get("overall_mean")
        if mean_val is not None:
            assert 0 <= mean_val <= 100


class TestComputeSubjectStats:
    """Tests for compute_subject_stats."""

    def test_returns_dict(self, sample_df):
        result = compute_subject_stats(sample_df, pass_mark=PASS_MARK)
        assert isinstance(result, dict)

    def test_has_subjects_key(self, sample_df):
        result = compute_subject_stats(sample_df, pass_mark=PASS_MARK)
        assert "subjects" in result

    def test_subjects_not_empty(self, sample_df):
        result = compute_subject_stats(sample_df, pass_mark=PASS_MARK)
        subjects = result.get("subjects", {})
        assert len(subjects) > 0

    def test_each_subject_has_mean(self, sample_df):
        result = compute_subject_stats(sample_df, pass_mark=PASS_MARK)
        subjects = result.get("subjects", [])
        # Subjects may be a list of dicts or a dict
        if isinstance(subjects, list):
            for s in subjects:
                assert "mean" in s or "average" in s, f"Subject entry missing mean: {s}"
        else:
            for name, stats in subjects.items():
                assert "mean" in stats or "average" in stats, f"Subject '{name}' missing mean"


class TestComputeStudentProfile:
    """Tests for compute_student_profile."""

    def test_returns_dict_for_known_student(self, sample_df):
        result = compute_student_profile(sample_df, "S001", pass_mark=PASS_MARK)
        assert result is not None
        assert isinstance(result, dict)

    def test_returns_none_for_unknown_student(self, sample_df):
        result = compute_student_profile(sample_df, "NONEXISTENT", pass_mark=PASS_MARK)
        assert result is None

    def test_profile_has_student_name(self, sample_df):
        result = compute_student_profile(sample_df, "S001", pass_mark=PASS_MARK)
        if result:
            assert any(k in result for k in ("student_name", "name"))

    def test_profile_has_subject_scores(self, sample_df):
        result = compute_student_profile(sample_df, "S001", pass_mark=PASS_MARK)
        if result:
            assert any(k in result for k in ("subject_scores", "subjects", "scores"))


class TestComputeTermComparison:
    """Tests for term comparison with 3 terms and multiple exams per term."""

    @pytest.fixture
    def multi_exam_df(self):
        return pd.DataFrame([
            # Student 1, Mathematics across 3 terms and 2 exams per term
            {"student_id": "S001", "name": "Alice", "class": "Form 1A", "subject": "Mathematics", "score": 60, "max_score": 100, "term": "Term 1", "exam_name": "Opener"},
            {"student_id": "S001", "name": "Alice", "class": "Form 1A", "subject": "Mathematics", "score": 68, "max_score": 100, "term": "Term 1", "exam_name": "Endterm"},
            {"student_id": "S001", "name": "Alice", "class": "Form 1A", "subject": "Mathematics", "score": 70, "max_score": 100, "term": "Term 2", "exam_name": "Opener"},
            {"student_id": "S001", "name": "Alice", "class": "Form 1A", "subject": "Mathematics", "score": 75, "max_score": 100, "term": "Term 2", "exam_name": "Endterm"},
            {"student_id": "S001", "name": "Alice", "class": "Form 1A", "subject": "Mathematics", "score": 76, "max_score": 100, "term": "Term 3", "exam_name": "Opener"},
            {"student_id": "S001", "name": "Alice", "class": "Form 1A", "subject": "Mathematics", "score": 82, "max_score": 100, "term": "Term 3", "exam_name": "Endterm"},
            # Student 2, Mathematics
            {"student_id": "S002", "name": "Brian", "class": "Form 1A", "subject": "Mathematics", "score": 40, "max_score": 100, "term": "Term 1", "exam_name": "Opener"},
            {"student_id": "S002", "name": "Brian", "class": "Form 1A", "subject": "Mathematics", "score": 45, "max_score": 100, "term": "Term 1", "exam_name": "Endterm"},
            {"student_id": "S002", "name": "Brian", "class": "Form 1A", "subject": "Mathematics", "score": 42, "max_score": 100, "term": "Term 2", "exam_name": "Opener"},
            {"student_id": "S002", "name": "Brian", "class": "Form 1A", "subject": "Mathematics", "score": 48, "max_score": 100, "term": "Term 2", "exam_name": "Endterm"},
            {"student_id": "S002", "name": "Brian", "class": "Form 1A", "subject": "Mathematics", "score": 50, "max_score": 100, "term": "Term 3", "exam_name": "Opener"},
            {"student_id": "S002", "name": "Brian", "class": "Form 1A", "subject": "Mathematics", "score": 55, "max_score": 100, "term": "Term 3", "exam_name": "Endterm"},
        ])

    def test_term_comparison_has_three_terms(self, multi_exam_df):
        result = compute_term_comparison(multi_exam_df, pass_mark=PASS_MARK)
        assert "terms" in result
        assert len(result["terms"]) == 3

    def test_term_comparison_has_exam_timeline(self, multi_exam_df):
        result = compute_term_comparison(multi_exam_df, pass_mark=PASS_MARK)
        assert "exam_timeline" in result
        assert len(result["exam_timeline"]) >= 6

    def test_term_comparison_has_early_performance(self, multi_exam_df):
        result = compute_term_comparison(multi_exam_df, pass_mark=PASS_MARK)
        early = result.get("early_performance", {})
        assert early.get("baseline_label") is not None
        assert early.get("latest_label") is not None
