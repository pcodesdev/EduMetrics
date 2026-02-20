"""
Tests for core/parser.py — CSV/Excel/ODS parsing, layout detection, column mapping.
"""

import os
import sys
import pytest
import pandas as pd

# Ensure backend/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.parser import (
    parse_upload,
    detect_layout,
    suggest_column_mapping,
    convert_wide_to_long,
)

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_school.csv")


class TestParseUpload:
    """Tests for the parse_upload function."""

    def test_csv_parse_returns_dict(self):
        result = parse_upload(SAMPLE_CSV)
        assert isinstance(result, dict)
        assert len(result) >= 1

    def test_csv_parse_first_sheet_is_dataframe(self):
        result = parse_upload(SAMPLE_CSV)
        first_key = list(result.keys())[0]
        assert isinstance(result[first_key], pd.DataFrame)

    def test_csv_parse_has_expected_columns(self):
        result = parse_upload(SAMPLE_CSV)
        df = list(result.values())[0]
        # Sample CSV has: student_id, name, gender, class, subject, score, max_score, term, year, school, region
        assert "student_id" in df.columns or "name" in df.columns

    def test_csv_parse_not_empty(self):
        result = parse_upload(SAMPLE_CSV)
        df = list(result.values())[0]
        assert len(df) > 0

    def test_invalid_file_raises(self):
        with pytest.raises(Exception):
            parse_upload("nonexistent_file.csv")


class TestDetectLayout:
    """Tests for layout detection (wide vs long format)."""

    def test_detect_layout_returns_string(self):
        result = parse_upload(SAMPLE_CSV)
        df = list(result.values())[0]
        layout = detect_layout(df)
        assert isinstance(layout, str)

    def test_detect_layout_value_is_valid(self):
        result = parse_upload(SAMPLE_CSV)
        df = list(result.values())[0]
        layout = detect_layout(df)
        assert layout in ("long", "wide")

    def test_detect_wide_layout_for_subject_columns(self):
        df = pd.DataFrame({
            "student_id": ["S001", "S002"],
            "name": ["Alice", "Brian"],
            "class": ["Form 1A", "Form 1A"],
            "term": ["Term 1", "Term 1"],
            "Mathematics": [78, 45],
            "English": [85, 52],
            "Kiswahili": [72, 58],
        })
        assert detect_layout(df) == "wide"


class TestSuggestColumnMapping:
    """Tests for automatic column mapping suggestion."""

    def test_returns_dict(self):
        result = parse_upload(SAMPLE_CSV)
        df = list(result.values())[0]
        mapping = suggest_column_mapping(df)
        assert isinstance(mapping, dict)

    def test_maps_student_id(self):
        result = parse_upload(SAMPLE_CSV)
        df = list(result.values())[0]
        mapping = suggest_column_mapping(df)
        # Should map student_id to the student_id column
        mapped_values = list(mapping.values())
        mapped_keys = list(mapping.keys())
        # Either 'student_id' is a key or is mapped as a value
        assert any("student" in str(k).lower() or "student" in str(v).lower()
                    for k, v in mapping.items())

    def test_maps_name(self):
        result = parse_upload(SAMPLE_CSV)
        df = list(result.values())[0]
        mapping = suggest_column_mapping(df)
        assert any("name" in str(k).lower() or "name" in str(v).lower()
                    for k, v in mapping.items())


class TestWideToLongConversion:
    """Tests for converting one-row-per-student wide sheets to long format."""

    def test_convert_wide_to_long_expands_subject_rows(self):
        wide_df = pd.DataFrame({
            "student_id": ["S001", "S002"],
            "name": ["Alice", "Brian"],
            "term": ["Term 1", "Term 1"],
            "Mathematics": [78, 45],
            "English": [85, 52],
            "Kiswahili": [72, 58],
        })
        mapping = {
            "student_id": "student_id",
            "name": "name",
            "term": "term",
        }
        long_df = convert_wide_to_long(wide_df, mapping)
        assert "subject" in long_df.columns
        assert "score" in long_df.columns
        assert len(long_df) == 6
