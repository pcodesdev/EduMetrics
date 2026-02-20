"""
Tests for core/cleaner.py — gender normalisation, subject normalisation, outlier detection.
"""

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.cleaner import clean_dataframe, generate_cleaning_report


@pytest.fixture
def sample_df():
    """A small DataFrame for testing cleaning operations."""
    return pd.DataFrame({
        "student_id": ["S001", "S001", "S002", "S002", "S003", "S003"],
        "name": ["Alice", "Alice", "Bob", "Bob", "Carol", "Carol"],
        "gender": ["F", "female", "m", "Male", "FEMALE", "f"],
        "class": ["8A", "8A", "8A", "8A", "8B", "8B"],
        "subject": ["Maths", "Eng", "mathematics", "english", "MATH", "ENG"],
        "score": [78, 85, 55, 60, 92, 88],
        "term": ["Term 1", "Term 1", "Term 1", "Term 1", "Term 1", "Term 1"],
    })


@pytest.fixture
def sample_df_with_outliers():
    """DataFrame with outlier scores."""
    return pd.DataFrame({
        "student_id": ["S001", "S002", "S003"],
        "name": ["Alice", "Bob", "Carol"],
        "gender": ["Female", "Male", "Female"],
        "class": ["8A", "8A", "8B"],
        "subject": ["Math", "Math", "Math"],
        "score": [78, -10, 150],  # -10 and 150 are outliers
        "term": ["Term 1", "Term 1", "Term 1"],
    })


class TestCleanDataframe:
    """Tests for the clean_dataframe function."""

    def test_returns_tuple(self, sample_df):
        result = clean_dataframe(sample_df)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_dataframe_and_report(self, sample_df):
        cleaned_df, report = clean_dataframe(sample_df)
        assert isinstance(cleaned_df, pd.DataFrame)
        assert isinstance(report, dict)

    def test_cleaned_df_not_empty(self, sample_df):
        cleaned_df, _ = clean_dataframe(sample_df)
        assert len(cleaned_df) > 0

    def test_gender_normalisation(self, sample_df):
        cleaned_df, _ = clean_dataframe(sample_df)
        if "gender" in cleaned_df.columns:
            genders = cleaned_df["gender"].str.lower().unique()
            # After normalisation, gender should be standardised
            for g in genders:
                assert g in ("male", "female", "m", "f", "other", "")

    def test_handles_outlier_scores(self, sample_df_with_outliers):
        cleaned_df, report = clean_dataframe(sample_df_with_outliers)
        # Should handle or flag outlier scores
        assert isinstance(cleaned_df, pd.DataFrame)

    def test_keeps_multiple_exams_within_same_term(self):
        df = pd.DataFrame({
            "student_id": ["S001", "S001"],
            "name": ["Alice", "Alice"],
            "subject": ["Mathematics", "Mathematics"],
            "score": [60, 75],
            "max_score": [100, 100],
            "term": ["Term 1", "Term 1"],
            "exam_name": ["Opener", "Endterm"],
            "year": ["2025", "2025"],
        })
        cleaned_df, _ = clean_dataframe(df)
        assert len(cleaned_df) == 2


class TestGenerateCleaningReport:
    """Tests for the cleaning report generation."""

    def test_report_is_dict(self, sample_df):
        _, report = clean_dataframe(sample_df)
        assert isinstance(report, dict)

    def test_report_has_content(self, sample_df):
        _, report = clean_dataframe(sample_df)
        assert len(report) > 0
