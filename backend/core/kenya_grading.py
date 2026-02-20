"""
grading.py (backward-compatible filename) - Universal grading helpers.

This module now provides a global, curriculum-agnostic grading model:
  A, B, C, D, E, F

All previous function names are preserved for compatibility with existing
routes and report builders.
"""

from typing import Any, Dict, List, Optional


# Universal grade bands (min_score, label, points, description)
# Ordered high to low.
UNIVERSAL_GRADES = [
    (80.0, "A", 6, "Excellent"),
    (70.0, "B", 5, "Very Good"),
    (60.0, "C", 4, "Good"),
    (50.0, "D", 3, "Satisfactory"),
    (40.0, "E", 2, "Needs Improvement"),
    (0.0, "F", 1, "Poor"),
]

# Compatibility constants expected elsewhere in the codebase.
SCHOOL_TYPES = {
    "universal": "Universal (A-F)",
}
PASS_MARKS = {"universal": 50}
SECONDARY_SUBJECTS: List[str] = []
CBC_PRIMARY_SUBJECTS: List[str] = []
CBC_JUNIOR_SUBJECTS: List[str] = []


def _clamp_score(score: Optional[float]) -> Optional[float]:
    if score is None:
        return None
    try:
        value = float(score)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(100.0, value))


def get_secondary_grade(score: Optional[float]) -> Dict[str, Any]:
    """Compatibility wrapper to universal grading."""
    return get_universal_grade(score)


def get_cbc_grade(score: Optional[float]) -> Dict[str, Any]:
    """Compatibility wrapper to universal grading."""
    return get_universal_grade(score)


def get_universal_grade(score: Optional[float]) -> Dict[str, Any]:
    """Return universal grade info for a 0-100 score."""
    value = _clamp_score(score)
    if value is None:
        return {"label": "-", "points": 0, "description": "No score", "system": "universal"}

    for min_score, label, points, desc in UNIVERSAL_GRADES:
        if value >= min_score:
            return {
                "label": label,
                "points": points,
                "description": desc,
                "system": "universal",
                "score": round(value, 1),
            }

    return {"label": "F", "points": 1, "description": "Poor", "system": "universal", "score": round(value, 1)}


def get_grade_label(score: Optional[float], system: str = "universal") -> str:
    """Return grade label string, e.g. A-F."""
    return get_universal_grade(score)["label"]


def get_grade_points(score: Optional[float], system: str = "universal") -> int:
    """Return numeric points for universal grade bands."""
    return int(get_universal_grade(score)["points"])


def classify_system(class_name: str) -> str:
    """Kept for compatibility; grading is universal regardless of class name."""
    return "universal"


def grade_dataframe_column(scores, system: str = "universal") -> List[str]:
    """Grade a list/series of scores. Returns list of universal grade labels."""
    return [get_grade_label(s, system) for s in scores]


def get_all_grade_thresholds(system: str = "universal") -> List[Dict[str, Any]]:
    """Return full universal grade scale for legend/reference."""
    thresholds = []
    for idx, (min_score, label, points, desc) in enumerate(UNIVERSAL_GRADES):
        max_score = 100.0 if idx == 0 else UNIVERSAL_GRADES[idx - 1][0] - 0.01
        thresholds.append(
            {
                "min": min_score,
                "max": round(max_score, 2),
                "label": label,
                "points": points,
                "description": desc,
            }
        )
    return thresholds


def get_mean_grade(scores, system: str = "universal") -> Dict[str, Any]:
    """Compute mean score and return its universal grade info."""
    valid = []
    for s in scores:
        value = _clamp_score(s)
        if value is not None:
            valid.append(value)
    if not valid:
        return {"mean": None, "label": "-", "points": 0}
    mean = sum(valid) / len(valid)
    info = get_universal_grade(mean)
    info["mean"] = round(mean, 2)
    return info


# 3-term ordering helpers retained for analytics.
TERM_ORDER = ["Term 1", "Term 2", "Term 3"]
TERM_META = {
    "Term 1": {"order": 1},
    "Term 2": {"order": 2},
    "Term 3": {"order": 3},
}


def sort_terms(term_list) -> List[str]:
    """Sort term labels in calendar order (Term 1, Term 2, Term 3)."""
    import re

    def key(term):
        t = str(term).strip()
        if t in TERM_META:
            return TERM_META[t]["order"]
        nums = re.findall(r"\d+", t)
        return int(nums[-1]) if nums else 99

    return sorted(term_list, key=key)
