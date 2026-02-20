import pandas as pd

from core.ai_insights import generate_parent_summary


def _sample_df():
    return pd.DataFrame(
        [
            {"student_id": "S001", "name": "Alice", "class": "Form 1A", "term": "Term 1", "percentage": 48},
            {"student_id": "S001", "name": "Alice", "class": "Form 1A", "term": "Term 2", "percentage": 55},
            {"student_id": "S002", "name": "Brian", "class": "Form 1A", "term": "Term 1", "percentage": 63},
            {"student_id": "S002", "name": "Brian", "class": "Form 1A", "term": "Term 2", "percentage": 61},
        ]
    )


def test_parent_summary_deterministic_mode(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    df = _sample_df()
    result = generate_parent_summary(df, "S001", pass_mark=50)

    assert result["mode"] == "deterministic"
    assert "summary" in result and result["summary"]
    assert "metrics" in result
    assert result["metrics"]["student_id"] == "S001"
    assert "recommendations" in result


def test_parent_summary_student_not_found(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    df = _sample_df()
    result = generate_parent_summary(df, "MISSING", pass_mark=50)

    assert result["error"] == "student_not_found"
    assert result["student_id"] == "MISSING"

