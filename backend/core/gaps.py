"""
gaps.py — Gap analysis engine.

Computes:
- Gender gap (t-test + Cohen's d + CI per subject)
- Class/stream gap (ANOVA or t-test)
- Regional gap (if multi-school data)
- Term performance gap
- Only surfaces gaps where p < 0.05 and |Cohen's d| > 0.2
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats as sp_stats


def _find_col(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    cols_lower = {str(c).lower().strip(): c for c in df.columns}
    for a in aliases:
        if a.lower() in cols_lower:
            return cols_lower[a.lower()]
    return None


def _safe_float(val) -> Optional[float]:
    try:
        v = float(val)
        return None if np.isnan(v) or np.isinf(v) else round(v, 4)
    except (TypeError, ValueError):
        return None


def _cohens_d(group_a: np.ndarray, group_b: np.ndarray) -> float:
    """Compute Cohen's d effect size."""
    n_a, n_b = len(group_a), len(group_b)
    if n_a < 2 or n_b < 2:
        return 0.0
    var_a = np.var(group_a, ddof=1)
    var_b = np.var(group_b, ddof=1)
    pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    if pooled_std == 0:
        return 0.0
    return float((np.mean(group_a) - np.mean(group_b)) / pooled_std)


def _effect_size_label(d: float) -> str:
    """Label the effect size."""
    d_abs = abs(d)
    if d_abs < 0.2:
        return "negligible"
    elif d_abs < 0.5:
        return "small"
    elif d_abs < 0.8:
        return "medium"
    else:
        return "large"


def _ensure_percentage(df: pd.DataFrame) -> pd.DataFrame:
    if "percentage" in df.columns:
        df["percentage"] = pd.to_numeric(df["percentage"], errors="coerce")
        return df
    score_col = _find_col(df, ["score", "marks", "mark", "total"])
    max_col = _find_col(df, ["max_score", "max_marks", "out_of"])
    if score_col:
        df["score_num"] = pd.to_numeric(df[score_col], errors="coerce")
        if max_col:
            df["max_num"] = pd.to_numeric(df[max_col], errors="coerce")
            mask = df["max_num"].notna() & (df["max_num"] > 0)
            df["percentage"] = np.nan
            df.loc[mask, "percentage"] = (df.loc[mask, "score_num"] / df.loc[mask, "max_num"] * 100).round(2)
            df.loc[~mask, "percentage"] = df.loc[~mask, "score_num"]
        else:
            df["percentage"] = df["score_num"]
    return df


# ── Gender Gap ──────────────────────────────────────────────────────

def _compute_gender_gaps(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Gender gap per subject and overall."""
    gender_col = _find_col(df, ["gender", "sex"])
    subject_col = _find_col(df, ["subject"])

    if not gender_col:
        return []

    gaps = []

    def _analyze_gender_gap(data: pd.DataFrame, label: str) -> Optional[Dict]:
        male_scores = data[data[gender_col].str.lower().isin(["male", "m", "boy"])]["percentage"].dropna().values
        female_scores = data[data[gender_col].str.lower().isin(["female", "f", "girl"])]["percentage"].dropna().values

        if len(male_scores) < 2 or len(female_scores) < 2:
            return None

        t_stat, p_value = sp_stats.ttest_ind(male_scores, female_scores, equal_var=False)
        d = _cohens_d(male_scores, female_scores)
        male_mean = np.mean(male_scores)
        female_mean = np.mean(female_scores)
        gap = abs(male_mean - female_mean)

        # 95% confidence interval for the difference
        se = np.sqrt(np.var(male_scores, ddof=1)/len(male_scores) +
                     np.var(female_scores, ddof=1)/len(female_scores))
        ci_lower = (male_mean - female_mean) - 1.96 * se
        ci_upper = (male_mean - female_mean) + 1.96 * se

        if male_mean > female_mean:
            direction = "girls_underperforming"
        else:
            direction = "boys_underperforming"

        is_significant = p_value < 0.05 and abs(d) > 0.2

        return {
            "type": "gender_gap",
            "label": label,
            "male_mean": _safe_float(male_mean),
            "female_mean": _safe_float(female_mean),
            "gap": _safe_float(gap),
            "direction": direction,
            "t_statistic": _safe_float(t_stat),
            "p_value": _safe_float(p_value),
            "effect_size": _safe_float(d),
            "effect_size_label": _effect_size_label(d),
            "ci_lower": _safe_float(ci_lower),
            "ci_upper": _safe_float(ci_upper),
            "male_count": int(len(male_scores)),
            "female_count": int(len(female_scores)),
            "statistically_significant": is_significant,
        }

    # Overall gender gap
    result = _analyze_gender_gap(df, "Overall")
    if result:
        gaps.append(result)

    # Per-subject gender gap
    if subject_col:
        for subj, sgroup in df.groupby(subject_col):
            result = _analyze_gender_gap(sgroup, str(subj))
            if result:
                result["subject"] = str(subj)
                gaps.append(result)

    return gaps


# ── Class Gap ───────────────────────────────────────────────────────

def _compute_class_gaps(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Class/stream gap analysis."""
    class_col = _find_col(df, ["class", "grade", "form", "stream"])
    if not class_col:
        return []

    classes = df[class_col].dropna().unique()
    if len(classes) < 2:
        return []

    gaps = []

    # Collect means per class
    class_means = {}
    class_groups = {}
    for cls in classes:
        scores = df[df[class_col] == cls]["percentage"].dropna().values
        if len(scores) >= 2:
            class_means[str(cls)] = np.mean(scores)
            class_groups[str(cls)] = scores

    if len(class_groups) < 2:
        return []

    # If 2 classes: t-test. If 3+: ANOVA
    group_arrays = list(class_groups.values())
    group_names = list(class_groups.keys())

    if len(group_arrays) == 2:
        t_stat, p_value = sp_stats.ttest_ind(group_arrays[0], group_arrays[1], equal_var=False)
        d = _cohens_d(group_arrays[0], group_arrays[1])
        test_type = "t-test"
    else:
        f_stat, p_value = sp_stats.f_oneway(*group_arrays)
        t_stat = f_stat
        # Compute effect size as eta-squared
        grand_mean = np.mean(np.concatenate(group_arrays))
        ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in group_arrays)
        ss_total = sum(np.sum((g - grand_mean)**2) for g in group_arrays)
        d = ss_between / ss_total if ss_total > 0 else 0
        test_type = "ANOVA"

    # Find the biggest gap between any two classes
    sorted_classes = sorted(class_means.items(), key=lambda x: x[1], reverse=True)
    best_class = sorted_classes[0]
    worst_class = sorted_classes[-1]

    gaps.append({
        "type": "class_gap",
        "test_type": test_type,
        "best_class": best_class[0],
        "best_mean": _safe_float(best_class[1]),
        "worst_class": worst_class[0],
        "worst_mean": _safe_float(worst_class[1]),
        "gap": _safe_float(best_class[1] - worst_class[1]),
        "statistic": _safe_float(t_stat),
        "p_value": _safe_float(p_value),
        "effect_size": _safe_float(d),
        "statistically_significant": p_value < 0.05,
        "class_means": [{"class": k, "mean": _safe_float(v)} for k, v in sorted_classes],
    })

    return gaps


# ── Regional Gap ────────────────────────────────────────────────────

def _compute_regional_gaps(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Regional gap analysis (for multi-school data)."""
    region_col = _find_col(df, ["region", "county", "district", "zone", "province"])
    if not region_col:
        return []

    regions = df[region_col].dropna().unique()
    if len(regions) < 2:
        return []

    region_groups = {}
    for reg in regions:
        scores = df[df[region_col] == reg]["percentage"].dropna().values
        if len(scores) >= 2:
            region_groups[str(reg)] = scores

    if len(region_groups) < 2:
        return []

    group_arrays = list(region_groups.values())
    region_names = list(region_groups.keys())

    if len(group_arrays) == 2:
        t_stat, p_value = sp_stats.ttest_ind(group_arrays[0], group_arrays[1], equal_var=False)
        test_type = "t-test"
    else:
        t_stat, p_value = sp_stats.f_oneway(*group_arrays)
        test_type = "ANOVA"

    region_means = {r: float(np.mean(g)) for r, g in region_groups.items()}
    sorted_regions = sorted(region_means.items(), key=lambda x: x[1], reverse=True)

    return [{
        "type": "regional_gap",
        "test_type": test_type,
        "best_region": sorted_regions[0][0],
        "best_mean": _safe_float(sorted_regions[0][1]),
        "worst_region": sorted_regions[-1][0],
        "worst_mean": _safe_float(sorted_regions[-1][1]),
        "gap": _safe_float(sorted_regions[0][1] - sorted_regions[-1][1]),
        "statistic": _safe_float(t_stat),
        "p_value": _safe_float(p_value),
        "statistically_significant": p_value < 0.05,
        "region_means": [{"region": r, "mean": _safe_float(m)} for r, m in sorted_regions],
    }]


# ── Term Gap ────────────────────────────────────────────────────────

def _compute_term_gaps(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Term performance gap analysis."""
    term_col = _find_col(df, ["term", "semester"])
    if not term_col:
        return []

    terms = sorted(df[term_col].dropna().unique())
    if len(terms) < 2:
        return []

    term_means = {}
    for term in terms:
        scores = df[df[term_col] == term]["percentage"].dropna().values
        if len(scores) > 0:
            term_means[str(term)] = float(np.mean(scores))

    sorted_terms = sorted(term_means.items(), key=lambda x: x[1], reverse=True)
    best_term = sorted_terms[0]
    worst_term = sorted_terms[-1]

    return [{
        "type": "term_gap",
        "best_term": best_term[0],
        "best_mean": _safe_float(best_term[1]),
        "worst_term": worst_term[0],
        "worst_mean": _safe_float(worst_term[1]),
        "gap": _safe_float(best_term[1] - worst_term[1]),
        "term_means": [{"term": t, "mean": _safe_float(m)} for t, m in sorted_terms],
    }]


def _sanitize(obj):
    """Recursively coerce numpy/pandas scalars to JSON-safe Python types."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return None if (np.isnan(v) or np.isinf(v)) else v
    return obj


# ── Main Entry Point ───────────────────────────────────────────────

def compute_gap_analysis(df: pd.DataFrame, pass_mark: int = 50) -> Dict[str, Any]:
    """Compute all gap analyses."""
    df = _ensure_percentage(df.copy())

    return _sanitize({
        "gender_gaps": _compute_gender_gaps(df),
        "class_gaps": _compute_class_gaps(df),
        "regional_gaps": _compute_regional_gaps(df),
        "term_gaps": _compute_term_gaps(df),
    })
