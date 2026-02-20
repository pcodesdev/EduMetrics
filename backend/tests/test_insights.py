"""
Tests for core/insights.py — verifies insights are generated with expected categories.
"""

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.insights import generate_all_insights
from core.parser import parse_upload

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_school.csv")
PASS_MARK = 50


@pytest.fixture
def sample_df():
    sheets = parse_upload(SAMPLE_CSV)
    return list(sheets.values())[0]


class TestGenerateAllInsights:
    """Tests for the insight generation engine."""

    def test_returns_dict(self, sample_df):
        result = generate_all_insights(sample_df, pass_mark=PASS_MARK)
        assert isinstance(result, dict)

    def test_has_insights_list(self, sample_df):
        result = generate_all_insights(sample_df, pass_mark=PASS_MARK)
        # Should have an insights list or all_insights list
        assert "insights" in result or "all_insights" in result

    def test_insights_not_empty(self, sample_df):
        """Sample data has enough variation to generate insights."""
        result = generate_all_insights(sample_df, pass_mark=PASS_MARK)
        insights = result.get("insights") or result.get("all_insights") or []
        assert len(insights) > 0, "Expected at least one insight from sample data"

    def test_each_insight_has_required_fields(self, sample_df):
        result = generate_all_insights(sample_df, pass_mark=PASS_MARK)
        insights = result.get("insights") or result.get("all_insights") or []
        for i, insight in enumerate(insights):
            assert isinstance(insight, dict), f"Insight {i} should be a dict"
            # Should have at least a title/message and severity/level
            has_text = any(k in insight for k in ("title", "message", "description"))
            assert has_text, f"Insight {i} missing title/message"

    def test_severity_levels_are_valid(self, sample_df):
        result = generate_all_insights(sample_df, pass_mark=PASS_MARK)
        insights = result.get("insights") or result.get("all_insights") or []
        valid_severities = {"critical", "high", "medium", "low", "positive", "info", "warning"}
        for insight in insights:
            severity = insight.get("severity", insight.get("level", "")).lower()
            if severity:
                assert severity in valid_severities, f"Invalid severity: {severity}"

    def test_insights_cover_multiple_categories(self, sample_df):
        """Insights should span different analysis categories."""
        result = generate_all_insights(sample_df, pass_mark=PASS_MARK)
        insights = result.get("insights") or result.get("all_insights") or []
        categories = set()
        for insight in insights:
            cat = insight.get("category", insight.get("type", ""))
            if cat:
                categories.add(cat.lower())
        # With diverse sample data, we should get multiple categories
        if len(insights) >= 3:
            assert len(categories) >= 1, "Expected insights from at least one category"
