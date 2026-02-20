"""
stats.py — All scipy/numpy statistical computations.

Computes:
- Per-subject stats (mean, median, std, pass/fail rates)
- Per-class and per-school aggregations
- Term-over-term trends (numpy polyfit)
- Pearson correlations (scipy.stats.pearsonr)
- Score distributions for charts
- Student profiles
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats as sp_stats


# ── Helpers ─────────────────────────────────────────────────────────

def _safe_float(val) -> Optional[float]:
    """Convert to float or return None."""
    try:
        v = float(val)
        return None if np.isnan(v) or np.isinf(v) else round(v, 2)
    except (TypeError, ValueError):
        return None


def _sanitize(obj):
    """Recursively coerce numpy/pandas scalars to JSON-safe Python types."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return None if (np.isnan(v) or np.isinf(v)) else v
    return obj


def _find_col(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    """Find the first column matching any alias (case-insensitive)."""
    cols_lower = {str(c).lower().strip(): c for c in df.columns}
    for a in aliases:
        if a.lower() in cols_lower:
            return cols_lower[a.lower()]
    return None


def _ensure_percentage(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure a 'percentage' column exists."""
    if "percentage" in df.columns:
        df["percentage"] = pd.to_numeric(df["percentage"], errors="coerce")
        return df

    score_col = _find_col(df, ["score", "marks", "mark", "total", "points"])
    max_col = _find_col(df, ["max_score", "max_marks", "out_of", "maximum"])

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


# ── School Overview ─────────────────────────────────────────────────

def compute_overview(df: pd.DataFrame, pass_mark: int = 50) -> Dict[str, Any]:
    """Compute school-wide overview statistics."""
    df = _ensure_percentage(df.copy())

    subject_col = _find_col(df, ["subject"])
    class_col = _find_col(df, ["class", "grade", "form", "stream"])
    term_col = _find_col(df, ["term", "semester"])
    student_col = _find_col(df, ["student_id", "name", "student_name"])
    student_id_col = _find_col(df, ["student_id", "studentid", "id", "adm_no", "admission_no"])
    student_name_col = _find_col(df, ["name", "student_name", "full_name", "student"])

    pct = df["percentage"].dropna()

    overview: Dict[str, Any] = {
        "total_students": df[student_col].nunique() if student_col else len(df),
        "total_subjects": df[subject_col].nunique() if subject_col else 0,
        "total_classes": df[class_col].nunique() if class_col else 0,
        "total_terms": df[term_col].nunique() if term_col else 0,
        "total_records": len(df),
        "overall_mean": _safe_float(pct.mean()),
        "overall_median": _safe_float(pct.median()),
        "overall_std": _safe_float(pct.std()),
        "pass_rate": _safe_float((pct >= pass_mark).sum() / len(pct) * 100) if len(pct) > 0 else 0,
        "fail_rate": _safe_float((pct < pass_mark).sum() / len(pct) * 100) if len(pct) > 0 else 0,
        "pass_count": int((pct >= pass_mark).sum()),
        "fail_count": int((pct < pass_mark).sum()),
    }

    # Score distribution (histogram bins)
    if len(pct) > 0:
        hist_counts, hist_edges = np.histogram(pct, bins=[0, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        overview["distribution"] = {
            "bins": [f"{int(hist_edges[i])}-{int(hist_edges[i+1])}" for i in range(len(hist_counts))],
            "counts": [int(c) for c in hist_counts],
        }

    # Top and bottom 5 students
    if student_col:
        student_means = df.groupby(student_col)["percentage"].mean().sort_values(ascending=False)

        # Build lookup maps so we can show Name (ID) where available.
        id_to_name = {}
        name_to_id = {}
        if student_id_col and student_name_col:
            for _, r in df[[student_id_col, student_name_col]].dropna().iterrows():
                sid = str(r.get(student_id_col, "")).strip()
                sname = str(r.get(student_name_col, "")).strip()
                if sid and sid.lower() != "nan" and sname and sname.lower() != "nan":
                    id_to_name[sid.lower()] = sname
                    name_to_id[sname.lower()] = sid

        def _student_display(student_key: Any) -> tuple[str, str | None, str | None]:
            raw = str(student_key).strip()
            sid: str | None = None
            sname: str | None = None

            # Resolve ID/name depending on the grouping key used.
            if student_id_col and student_col == student_id_col:
                sid = raw
                sname = id_to_name.get(raw.lower())
            elif student_name_col and student_col == student_name_col:
                sname = raw
                sid = name_to_id.get(raw.lower())
            else:
                # Fallback when grouped by a mixed/other student column.
                sname = id_to_name.get(raw.lower(), raw)
                sid = name_to_id.get(raw.lower())

            if sname and sid and sname.lower() != sid.lower():
                return f"{sname} ({sid})", sid, sname
            if sname:
                return sname, sid, sname
            if sid:
                return sid, sid, sname
            return raw, sid, sname

        overview["top_students"] = [
            {
                "name": _student_display(student_key)[0],
                "student_id": _student_display(student_key)[1],
                "student_name": _student_display(student_key)[2],
                "mean": _safe_float(mean),
            }
            for student_key, mean in student_means.head(5).items()
        ]
        overview["bottom_students"] = [
            {
                "name": _student_display(student_key)[0],
                "student_id": _student_display(student_key)[1],
                "student_name": _student_display(student_key)[2],
                "mean": _safe_float(mean),
            }
            for student_key, mean in student_means.tail(5).items()
        ]

    # Top and bottom subjects
    if subject_col:
        subject_means = df.groupby(subject_col)["percentage"].mean().sort_values(ascending=False)
        overview["top_subjects"] = [
            {"subject": subj, "mean": _safe_float(mean)}
            for subj, mean in subject_means.head(5).items()
        ]
        overview["bottom_subjects"] = [
            {"subject": subj, "mean": _safe_float(mean)}
            for subj, mean in subject_means.tail(5).items()
        ]

    # Class averages
    if class_col:
        class_means = df.groupby(class_col)["percentage"].mean().sort_values(ascending=False)
        overview["class_averages"] = [
            {"class": cls, "mean": _safe_float(mean)}
            for cls, mean in class_means.items()
        ]

    # Term trends
    if term_col:
        from core.kenya_grading import sort_terms
        term_means = df.groupby(term_col)["percentage"].mean()
        ordered_terms = sort_terms([str(t) for t in term_means.index.tolist()])
        overview["term_trends"] = [
            {"term": str(term), "mean": _safe_float(term_means.get(term))}
            for term in ordered_terms
        ]

    return _sanitize(overview)


# ── Subject Statistics ──────────────────────────────────────────────

def compute_subject_stats(df: pd.DataFrame, pass_mark: int = 50) -> Dict[str, Any]:
    """Per-subject deep statistics."""
    df = _ensure_percentage(df.copy())
    subject_col = _find_col(df, ["subject"])

    if not subject_col:
        return {"subjects": [], "correlation_matrix": {}}

    subjects_data = []
    for subj, group in df.groupby(subject_col):
        pct = group["percentage"].dropna()
        if len(pct) == 0:
            continue

        subjects_data.append({
            "subject": str(subj),
            "mean": _safe_float(pct.mean()),
            "median": _safe_float(pct.median()),
            "std": _safe_float(pct.std()),
            "min": _safe_float(pct.min()),
            "max": _safe_float(pct.max()),
            "pass_rate": _safe_float((pct >= pass_mark).sum() / len(pct) * 100),
            "fail_rate": _safe_float((pct < pass_mark).sum() / len(pct) * 100),
            "pass_count": int((pct >= pass_mark).sum()),
            "fail_count": int((pct < pass_mark).sum()),
            "count": len(pct),
            "distribution": {
                "q1": _safe_float(pct.quantile(0.25)),
                "q3": _safe_float(pct.quantile(0.75)),
                "iqr": _safe_float(pct.quantile(0.75) - pct.quantile(0.25)),
            },
        })

    # Sort by mean descending
    subjects_data.sort(key=lambda x: x["mean"] or 0, reverse=True)

    # Correlation matrix
    student_col = _find_col(df, ["student_id", "name", "student_name"])
    correlation_matrix = {}
    if student_col:
        pivot = df.pivot_table(
            index=student_col, columns=subject_col,
            values="percentage", aggfunc="mean"
        )
        if len(pivot.columns) >= 2:
            corr_pairs = []
            cols = list(pivot.columns)
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    col_a, col_b = cols[i], cols[j]
                    valid = pivot[[col_a, col_b]].dropna()
                    if len(valid) >= 3:
                        r, p = sp_stats.pearsonr(valid[col_a], valid[col_b])
                        corr_pairs.append({
                            "subject_a": str(col_a),
                            "subject_b": str(col_b),
                            "r": _safe_float(r),
                            "p_value": _safe_float(p),
                        })
            correlation_matrix = {
                "pairs": corr_pairs,
                "matrix": pivot.corr().round(3).to_dict(),
            }

    return _sanitize({
        "subjects": subjects_data,
        "correlation_matrix": correlation_matrix,
    })


# ── Student Profile ─────────────────────────────────────────────────

def compute_student_profile(
    df: pd.DataFrame, student_id: str, pass_mark: int = 50
) -> Optional[Dict[str, Any]]:
    """Compute individual student profile."""
    df = _ensure_percentage(df.copy())

    student_col = _find_col(df, ["student_id", "name", "student_name"])
    subject_col = _find_col(df, ["subject"])
    term_col = _find_col(df, ["term", "semester"])
    class_col = _find_col(df, ["class", "grade", "form"])
    name_col = _find_col(df, ["name", "student_name", "full_name"])

    if not student_col:
        return None

    student_df = df[df[student_col].astype(str) == str(student_id)]
    if student_df.empty:
        return None

    profile: Dict[str, Any] = {
        "student_id": student_id,
        "name": str(student_df.iloc[0][name_col]) if name_col else str(student_id),
    }

    # Basic info
    for col_name in ["gender", "class", "school", "region"]:
        c = _find_col(student_df, [col_name])
        if c:
            profile[col_name] = str(student_df.iloc[0][c])

    # Overall stats
    pct = student_df["percentage"].dropna()
    profile["overall_mean"] = _safe_float(pct.mean())
    profile["overall_median"] = _safe_float(pct.median())
    profile["pass_count"] = int((pct >= pass_mark).sum())
    profile["fail_count"] = int((pct < pass_mark).sum())

    # Per-subject scores (for radar chart)
    if subject_col:
        subj_scores = student_df.groupby(subject_col)["percentage"].mean()
        profile["subject_scores"] = [
            {"subject": str(s), "score": _safe_float(v)}
            for s, v in subj_scores.items()
        ]

    # Per-term trends
    if term_col and subject_col:
        term_data = []
        for term, tgroup in student_df.groupby(term_col):
            term_entry = {"term": str(term), "mean": _safe_float(tgroup["percentage"].mean())}
            for subj, sgroup in tgroup.groupby(subject_col):
                term_entry[str(subj)] = _safe_float(sgroup["percentage"].mean())
            term_data.append(term_entry)
        profile["term_trends"] = term_data

    # Rank within class
    if class_col and student_col:
        student_class = str(student_df.iloc[0][class_col])
        class_df = df[df[class_col].astype(str) == student_class]
        class_means = class_df.groupby(student_col)["percentage"].mean().sort_values(ascending=False)
        rank_list = list(class_means.index)
        profile["class_rank"] = rank_list.index(student_id) + 1 if student_id in rank_list else None
        profile["class_total"] = len(rank_list)

    # Rank within school
    if student_col:
        school_means = df.groupby(student_col)["percentage"].mean().sort_values(ascending=False)
        rank_list = list(school_means.index)
        profile["school_rank"] = rank_list.index(student_id) + 1 if student_id in rank_list else None
        profile["school_total"] = len(rank_list)

    # All scores
    records = []
    for _, row in student_df.iterrows():
        rec = {"percentage": _safe_float(row.get("percentage"))}
        if subject_col:
            rec["subject"] = str(row[subject_col])
        if term_col:
            rec["term"] = str(row[term_col])
        rec["pass_fail"] = "Pass" if rec["percentage"] and rec["percentage"] >= pass_mark else "Fail"
        records.append(rec)
    profile["all_scores"] = records

    return _sanitize(profile)


# ── Term Comparison (3-Term Calendar) ────────────────────────────────

def compute_term_comparison(df: pd.DataFrame, pass_mark: int = 50) -> Dict[str, Any]:
    """
    Compare student performance across Term 1, Term 2, Term 3.

    Returns:
      - terms: sorted list of term names
      - school_by_term: school-wide mean/pass-rate per term
      - subjects_by_term: per-subject mean per term
      - students_by_term: per-student mean per term with delta + trend
      - class_by_term: per-class mean per term
      - subject_term_matrix: [subject][term] = mean (for grouped bar chart)
    """
    import re
    from core.kenya_grading import sort_terms, get_grade_label

    df = _ensure_percentage(df.copy())

    term_col    = _find_col(df, ["term", "semester"])
    exam_col    = _find_col(df, ["exam_name", "assessment", "assessment_name", "exam", "exam_type", "test"])
    student_col = _find_col(df, ["student_id", "name", "student_name"])
    student_name_col = _find_col(df, ["name", "student_name", "full_name", "student"])
    subject_col = _find_col(df, ["subject"])
    class_col   = _find_col(df, ["class", "grade", "form", "stream"])

    if not term_col:
        return {"error": "No 'term' column found in data.", "terms": []}

    # Normalize term labels so matching is robust (whitespace/case/variants).
    # Examples handled:
    #   "term 1", " Term 1 ", "T1" -> "Term 1"
    def _canonical_term(value: Any):
        if pd.isna(value):
            return np.nan
        raw = str(value).strip()
        if not raw or raw.lower() == "nan":
            return np.nan
        match = re.search(r"(\d+)", raw)
        if match:
            return f"Term {int(match.group(1))}"
        return raw

    df[term_col] = df[term_col].apply(_canonical_term)

    # Universal grading is used globally.
    school_system = "universal"

    # Sort terms in calendar order
    raw_terms = df[term_col].dropna().astype(str).unique().tolist()
    sorted_term_list = sort_terms(raw_terms)

    # ── 1. School-wide per-term stats ────────────────────────────────
    school_by_term = []
    for term in sorted_term_list:
        tdf = df[df[term_col].astype(str) == str(term)]
        pct = tdf["percentage"].dropna()
        school_by_term.append({
            "term": str(term),
            "mean": _safe_float(pct.mean()),
            "median": _safe_float(pct.median()),
            "pass_rate": _safe_float((pct >= pass_mark).sum() / len(pct) * 100) if len(pct) > 0 else 0,
            "pass_count": int((pct >= pass_mark).sum()),
            "fail_count": int((pct < pass_mark).sum()),
            "student_count": tdf[student_col].nunique() if student_col else len(tdf),
            "grade": get_grade_label(float(pct.mean()), school_system) if len(pct) > 0 else "—",
        })

    # Compute school delta (term-over-term change)
    for i in range(1, len(school_by_term)):
        prev = school_by_term[i-1]["mean"]
        curr = school_by_term[i]["mean"]
        if prev is not None and curr is not None:
            school_by_term[i]["delta"] = round(curr - prev, 2)
            school_by_term[i]["trend"] = "improving" if curr > prev + 1 else "declining" if curr < prev - 1 else "stable"
        else:
            school_by_term[i]["delta"] = None
            school_by_term[i]["trend"] = "unknown"
    if school_by_term:
        school_by_term[0]["delta"] = None
        school_by_term[0]["trend"] = "baseline"

    # ── 2. Per-subject per-term means ────────────────────────────────
    subjects_by_term = []
    subject_term_matrix: Dict[str, Dict[str, Any]] = {}

    if subject_col:
        for subj in sorted(df[subject_col].dropna().unique()):
            sdf = df[df[subject_col].astype(str) == str(subj)]
            row: Dict[str, Any] = {"subject": str(subj), "terms": {}}
            prev_mean = None
            for term in sorted_term_list:
                tdf = sdf[sdf[term_col].astype(str) == str(term)]
                pct = tdf["percentage"].dropna()
                mean = _safe_float(pct.mean())
                delta = round(mean - prev_mean, 2) if (mean is not None and prev_mean is not None) else None
                trend = (
                    "improving" if delta and delta > 1 else
                    "declining" if delta and delta < -1 else
                    "stable" if delta is not None else "baseline"
                )
                row["terms"][str(term)] = {
                    "mean": mean,
                    "pass_rate": _safe_float((pct >= pass_mark).sum() / len(pct) * 100) if len(pct) > 0 else 0,
                    "grade": get_grade_label(mean, school_system) if mean is not None else "—",
                    "delta": delta,
                    "trend": trend,
                }
                prev_mean = mean
            subjects_by_term.append(row)

            # Build matrix for grouped bar chart
            subject_term_matrix[str(subj)] = {
                t: row["terms"][t]["mean"] for t in row["terms"]
            }

    # ── 3. Per-student per-term means ────────────────────────────────
    students_by_term = []
    if student_col:
        for sid in df[student_col].dropna().unique():
            stdf = df[df[student_col].astype(str) == str(sid)]
            if student_name_col and student_name_col in stdf.columns:
                raw_name = stdf.iloc[0].get(student_name_col, sid)
            else:
                raw_name = sid
            display_name = str(raw_name).strip() if raw_name is not None else str(sid)
            if not display_name or display_name.lower() == "nan":
                display_name = str(sid)

            info: Dict[str, Any] = {
                "student_id": str(sid),
                "name": display_name,
                "terms": {},
            }
            if class_col:
                info["class"] = str(stdf.iloc[0][class_col])

            prev_mean = None
            term_means = []
            for term in sorted_term_list:
                tdf = stdf[stdf[term_col].astype(str) == str(term)]
                pct = tdf["percentage"].dropna()
                mean = _safe_float(pct.mean())
                delta = round(mean - prev_mean, 2) if (mean is not None and prev_mean is not None) else None
                trend = (
                    "improving" if delta and delta > 1 else
                    "declining" if delta and delta < -1 else
                    "stable" if delta is not None else "baseline"
                )
                info["terms"][str(term)] = {
                    "mean": mean,
                    "grade": get_grade_label(mean, school_system) if mean is not None else "—",
                    "delta": delta,
                    "trend": trend,
                    "pass_count": int((pct >= pass_mark).sum()),
                    "fail_count": int((pct < pass_mark).sum()),
                }
                if mean is not None:
                    term_means.append(mean)
                prev_mean = mean

            # Overall trend across all terms (polyfit slope)
            if len(term_means) >= 2:
                x = np.arange(len(term_means))
                slope = float(np.polyfit(x, term_means, 1)[0])
                info["overall_trend"] = "improving" if slope > 0.5 else "declining" if slope < -0.5 else "stable"
                info["trend_slope"] = round(slope, 3)
            else:
                info["overall_trend"] = "insufficient_data"
                info["trend_slope"] = None

            students_by_term.append(info)

        # Sort by latest term mean descending
        last_term = sorted_term_list[-1] if sorted_term_list else None
        if last_term:
            students_by_term.sort(
                key=lambda s: s["terms"].get(str(last_term), {}).get("mean") or 0,
                reverse=True
            )
        # Add rank
        for i, s in enumerate(students_by_term):
            s["rank"] = i + 1

    # ── 4. Per-class per-term stats ─────────────────────────────────
    class_by_term = []
    if class_col:
        for cls in sorted(df[class_col].dropna().unique()):
            cdf = df[df[class_col].astype(str) == str(cls)]
            row = {"class": str(cls), "terms": {}}
            for term in sorted_term_list:
                tdf = cdf[cdf[term_col].astype(str) == str(term)]
                pct = tdf["percentage"].dropna()
                row["terms"][str(term)] = {
                    "mean": _safe_float(pct.mean()),
                    "pass_rate": _safe_float((pct >= pass_mark).sum() / len(pct) * 100) if len(pct) > 0 else 0,
                    "grade": get_grade_label(_safe_float(pct.mean()), school_system) if len(pct) > 0 else "—",
                }
            class_by_term.append(row)

    # ── 5. Top improvers / decliners ────────────────────────────────
    top_improvers, top_decliners = [], []
    improved_count, declined_count, stable_count = 0, 0, 0
    if students_by_term and len(sorted_term_list) >= 2:
        first_t = sorted_term_list[0]
        last_t  = sorted_term_list[-1]
        for s in students_by_term:
            t1_mean = (s["terms"].get(str(first_t)) or {}).get("mean")
            t_last_mean = (s["terms"].get(str(last_t)) or {}).get("mean")
            if t1_mean is not None and t_last_mean is not None:
                s["_total_delta"] = round(t_last_mean - t1_mean, 2)
                if s["_total_delta"] > 1:
                    improved_count += 1
                elif s["_total_delta"] < -1:
                    declined_count += 1
                else:
                    stable_count += 1

        ranked = sorted([s for s in students_by_term if "_total_delta" in s],
                        key=lambda s: s["_total_delta"], reverse=True)
        top_improvers = [
            {"name": s.get("name"), "student_id": s.get("student_id"), "delta": s["_total_delta"]}
            for s in ranked[:5]
        ]
        top_decliners = [
            {"name": s.get("name"), "student_id": s.get("student_id"), "delta": s["_total_delta"]}
            for s in ranked[-5:][::-1]
        ]

    # ── 6. Exam timeline (many exams within each term) ──────────────
    exam_timeline: List[Dict[str, Any]] = []
    if exam_col:
        import re

        def _exam_key(label: Any):
            s = str(label).strip().lower()
            nums = re.findall(r"\d+", s)
            n = int(nums[0]) if nums else 0
            if any(k in s for k in ["opener", "opening", "baseline", "entry"]):
                return (1, n, s)
            if any(k in s for k in ["cat", "continuous", "mid", "midterm"]):
                return (2, n, s)
            if any(k in s for k in ["end", "final", "eot"]):
                return (3, n, s)
            return (4, n, s)

        for term in sorted_term_list:
            tdf = df[df[term_col].astype(str) == str(term)]
            exams = sorted(tdf[exam_col].dropna().unique().tolist(), key=_exam_key)
            for exam in exams:
                edf = tdf[tdf[exam_col].astype(str) == str(exam)]
                pct = edf["percentage"].dropna()
                exam_timeline.append({
                    "term": str(term),
                    "exam": str(exam),
                    "label": f"{term} - {exam}",
                    "mean": _safe_float(pct.mean()),
                    "pass_rate": _safe_float((pct >= pass_mark).sum() / len(pct) * 100) if len(pct) > 0 else 0,
                    "student_count": edf[student_col].nunique() if student_col else len(edf),
                    "grade": get_grade_label(_safe_float(pct.mean()), school_system) if len(pct) > 0 else "—",
                })

        for i in range(1, len(exam_timeline)):
            prev = exam_timeline[i - 1]["mean"]
            curr = exam_timeline[i]["mean"]
            if prev is not None and curr is not None:
                delta = round(curr - prev, 2)
                exam_timeline[i]["delta"] = delta
                exam_timeline[i]["trend"] = "improving" if delta > 1 else "declining" if delta < -1 else "stable"
            else:
                exam_timeline[i]["delta"] = None
                exam_timeline[i]["trend"] = "unknown"
        if exam_timeline:
            exam_timeline[0]["delta"] = None
            exam_timeline[0]["trend"] = "baseline"

    # ── 7. Early performance comparison ─────────────────────────────
    early_performance = {
        "baseline_label": None,
        "baseline_mean": None,
        "latest_label": None,
        "latest_mean": None,
        "delta": None,
        "trend": "insufficient_data",
    }
    if len(exam_timeline) >= 2:
        first_point = exam_timeline[0]
        last_point = exam_timeline[-1]
        delta = None
        if first_point["mean"] is not None and last_point["mean"] is not None:
            delta = round(last_point["mean"] - first_point["mean"], 2)
        early_performance = {
            "baseline_label": first_point["label"],
            "baseline_mean": first_point["mean"],
            "latest_label": last_point["label"],
            "latest_mean": last_point["mean"],
            "delta": delta,
            "trend": "improving" if delta is not None and delta > 1 else
                     "declining" if delta is not None and delta < -1 else
                     "stable" if delta is not None else "insufficient_data",
        }
    elif len(school_by_term) >= 2:
        first_point = school_by_term[0]
        last_point = school_by_term[-1]
        delta = None
        if first_point["mean"] is not None and last_point["mean"] is not None:
            delta = round(last_point["mean"] - first_point["mean"], 2)
        early_performance = {
            "baseline_label": first_point["term"],
            "baseline_mean": first_point["mean"],
            "latest_label": last_point["term"],
            "latest_mean": last_point["mean"],
            "delta": delta,
            "trend": "improving" if delta is not None and delta > 1 else
                     "declining" if delta is not None and delta < -1 else
                     "stable" if delta is not None else "insufficient_data",
        }

    return _sanitize({
        "terms": sorted_term_list,
        "school_system": school_system,
        "school_by_term": school_by_term,
        "subjects_by_term": subjects_by_term,
        "subject_term_matrix": subject_term_matrix,
        "students_by_term": students_by_term,
        "class_by_term": class_by_term,
        "top_improvers": top_improvers,
        "top_decliners": top_decliners,
        "student_delta_summary": {
            "improved": improved_count,
            "declined": declined_count,
            "stable": stable_count,
        },
        "exam_timeline": exam_timeline,
        "early_performance": early_performance,
    })
