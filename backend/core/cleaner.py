"""
cleaner.py — Pandas data cleaning pipeline.

Handles:
- Gender standardization
- Subject name normalization
- Score → percentage conversion
- Z-score outlier detection
- Deduplication
- Whitespace / capitalization fixes
- Cleaning report generation
"""

from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd


# ── Gender Standardization ──────────────────────────────────────────

GENDER_MAP = {
    "m": "Male", "male": "Male", "boy": "Male", "b": "Male", "man": "Male",
    "f": "Female", "female": "Female", "girl": "Female", "g": "Female", "woman": "Female",
    "other": "Other", "non-binary": "Other", "nb": "Other", "x": "Other",
}


def standardize_gender(value: str) -> str:
    """Map gender variants to Male/Female/Other."""
    if pd.isna(value):
        return "Unknown"
    cleaned = str(value).strip().lower()
    return GENDER_MAP.get(cleaned, "Other")


# ── Subject Normalization ───────────────────────────────────────────

SUBJECT_MAP = {
    "maths": "Mathematics", "math": "Mathematics", "mathematics": "Mathematics",
    "mat": "Mathematics",
    "eng": "English", "english": "English", "english language": "English",
    "engl": "English",
    "kis": "Kiswahili", "kiswahili": "Kiswahili", "swahili": "Kiswahili",
    "kiswa": "Kiswahili",
    "sci": "Science", "science": "Science", "general science": "Science",
    "bio": "Biology", "biology": "Biology",
    "phy": "Physics", "physics": "Physics", "phys": "Physics",
    "chem": "Chemistry", "chemistry": "Chemistry",
    "hist": "History", "history": "History", "history & government": "History",
    "hist & gov": "History",
    "geo": "Geography", "geography": "Geography", "geog": "Geography",
    "cre": "CRE", "christian religious education": "CRE", "c.r.e": "CRE",
    "c.r.e.": "CRE",
    "ire": "IRE", "islamic religious education": "IRE", "i.r.e": "IRE",
    "bus": "Business Studies", "business": "Business Studies",
    "business studies": "Business Studies",
    "agri": "Agriculture", "agriculture": "Agriculture", "agric": "Agriculture",
    "comp": "Computer Studies", "computer": "Computer Studies",
    "computer studies": "Computer Studies", "ict": "Computer Studies",
    "art": "Art & Design", "art and design": "Art & Design",
    "art & design": "Art & Design",
    "music": "Music",
    "french": "French", "fre": "French",
    "german": "German",
    "arabic": "Arabic",
    "home science": "Home Science", "home sci": "Home Science",
    "hs": "Home Science",
    "pe": "Physical Education", "physical education": "Physical Education",
    "p.e": "Physical Education", "p.e.": "Physical Education",
    "sst": "Social Studies", "social studies": "Social Studies",
    "s.s.t": "Social Studies",
}


def normalize_subject(value: str) -> str:
    """Normalize subject name variants to standard names."""
    if pd.isna(value):
        return str(value)
    cleaned = str(value).strip().lower()
    return SUBJECT_MAP.get(cleaned, str(value).strip().title())


# ── Main Cleaning Pipeline ──────────────────────────────────────────

def clean_dataframe(
    df: pd.DataFrame,
    pass_mark: int = 50,
    treat_missing_as_zero: bool = False,
) -> Tuple[pd.DataFrame, Dict]:
    """
    Clean the DataFrame and return (cleaned_df, cleaning_report).
    """
    report: Dict = {
        "original_rows": len(df),
        "original_columns": len(df.columns),
        "steps": [],
        "warnings": [],
    }

    cleaned = df.copy()

    # ── 1. Trim whitespace and fix capitalization ───────────────────
    str_cols = cleaned.select_dtypes(include=["object"]).columns
    for col in str_cols:
        cleaned[col] = cleaned[col].astype(str).str.strip()
        # Don't title-case score or ID columns
        if col.lower() not in ("score", "marks", "mark", "max_score", "max_marks",
                                "student_id", "id", "adm_no", "reg_no"):
            cleaned[col] = cleaned[col].str.strip()

    # Replace 'nan' strings back to NaN
    cleaned = cleaned.replace({"nan": np.nan, "NaN": np.nan, "": np.nan, "None": np.nan})
    report["steps"].append("Trimmed whitespace from all string fields.")

    # ── 2. Gender standardization ──────────────────────────────────
    gender_col = _find_column(cleaned, ["gender", "sex", "m/f", "gen"])
    if gender_col:
        original_genders = cleaned[gender_col].dropna().unique()
        cleaned[gender_col] = cleaned[gender_col].apply(standardize_gender)
        new_genders = cleaned[gender_col].unique()
        report["steps"].append(
            f"Standardized gender values: {list(original_genders)} → {list(new_genders)}"
        )

    # ── 3. Subject normalization ───────────────────────────────────
    subject_col = _find_column(cleaned, ["subject", "subject_name", "course"])
    if subject_col:
        original_subjects = cleaned[subject_col].dropna().unique()
        cleaned[subject_col] = cleaned[subject_col].apply(normalize_subject)
        new_subjects = cleaned[subject_col].dropna().unique()
        normalized_count = sum(
            1 for s in original_subjects
            if str(s).strip().lower() in SUBJECT_MAP
            and SUBJECT_MAP[str(s).strip().lower()] != str(s).strip()
        )
        report["steps"].append(
            f"Normalized {normalized_count} subject name variants. "
            f"Subjects found: {list(new_subjects)}"
        )

    # ── 4. Convert scores to numeric ───────────────────────────────
    score_col = _find_column(cleaned, ["score", "marks", "mark", "total", "total_score",
                                        "raw_score", "points", "result", "percentage"])
    max_score_col = _find_column(cleaned, ["max_score", "max_marks", "total_marks",
                                            "out_of", "max", "maximum"])

    if score_col:
        original_na = cleaned[score_col].isna().sum()
        cleaned[score_col] = pd.to_numeric(cleaned[score_col], errors="coerce")
        new_na = cleaned[score_col].isna().sum()
        parse_errors = new_na - original_na
        if parse_errors > 0:
            report["warnings"].append(
                f"{parse_errors} score values could not be converted to numbers."
            )
        report["steps"].append("Converted scores to numeric.")

    if max_score_col:
        cleaned[max_score_col] = pd.to_numeric(cleaned[max_score_col], errors="coerce")

    # ── 5. Compute percentage ──────────────────────────────────────
    if score_col:
        if max_score_col and max_score_col in cleaned.columns:
            mask = cleaned[max_score_col].notna() & (cleaned[max_score_col] > 0)
            cleaned["percentage"] = np.nan
            cleaned.loc[mask, "percentage"] = (
                cleaned.loc[mask, score_col] / cleaned.loc[mask, max_score_col] * 100
            ).round(2)
            # Where max_score is not available, assume score IS percentage
            cleaned.loc[~mask, "percentage"] = cleaned.loc[~mask, score_col]
            report["steps"].append("Computed percentage from score / max_score.")
        else:
            # Assume scores are already percentages or out of 100
            cleaned["percentage"] = cleaned[score_col]
            report["steps"].append("Using score as percentage (no max_score column found).")

    # ── 6. Handle missing scores ───────────────────────────────────
    if score_col:
        missing_scores = cleaned[score_col].isna().sum()
        if missing_scores > 0:
            if treat_missing_as_zero:
                cleaned[score_col] = cleaned[score_col].fillna(0)
                cleaned["percentage"] = cleaned["percentage"].fillna(0)
                report["steps"].append(
                    f"Treated {missing_scores} missing scores as 0."
                )
            else:
                report["warnings"].append(
                    f"{missing_scores} rows have missing scores. "
                    "They will be excluded from aggregations."
                )
                report["steps"].append(
                    f"Flagged {missing_scores} missing scores (not treated as 0)."
                )

    # ── 7. Outlier detection (z-score > 3) ─────────────────────────
    outlier_indices = []
    if "percentage" in cleaned.columns:
        pct = cleaned["percentage"].dropna()
        if len(pct) > 2:
            mean = pct.mean()
            std = pct.std()
            if std > 0:
                z_scores = ((cleaned["percentage"] - mean) / std).abs()
                outlier_mask = z_scores > 3
                outlier_indices = cleaned[outlier_mask].index.tolist()
                if outlier_indices:
                    cleaned["is_outlier"] = False
                    cleaned.loc[outlier_indices, "is_outlier"] = True
                    report["warnings"].append(
                        f"{len(outlier_indices)} potential outliers detected "
                        f"(|z-score| > 3). Flagged but not removed."
                    )
                    report["steps"].append(
                        f"Detected {len(outlier_indices)} outliers via z-score."
                    )

    # ── 8. Deduplication ───────────────────────────────────────────
    id_col = _find_column(cleaned, ["student_id", "studentid", "id", "adm_no", "reg_no"])
    term_col = _find_column(cleaned, ["term", "semester", "exam_period"])
    exam_col = _find_column(
        cleaned,
        ["exam_name", "assessment", "assessment_name", "exam", "exam_type", "test"],
    )
    year_col = _find_column(cleaned, ["year", "academic_year", "academic year"])

    dedup_cols = []
    if id_col:
        dedup_cols.append(id_col)
    elif _find_column(cleaned, ["name", "student_name", "full_name"]):
        dedup_cols.append(_find_column(cleaned, ["name", "student_name", "full_name"]))

    if subject_col:
        dedup_cols.append(subject_col)
    if term_col:
        dedup_cols.append(term_col)
    if exam_col and exam_col not in dedup_cols:
        dedup_cols.append(exam_col)
    if year_col and year_col not in dedup_cols:
        dedup_cols.append(year_col)
    if score_col and score_col not in dedup_cols:
        dedup_cols.append(score_col)

    if dedup_cols:
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates(subset=dedup_cols, keep="last")
        removed = before - len(cleaned)
        if removed > 0:
            report["steps"].append(
                f"Removed {removed} duplicate rows using keys: {dedup_cols}."
            )
        else:
            report["steps"].append("No duplicate rows found.")

    # ── 9. Compute pass/fail ───────────────────────────────────────
    if "percentage" in cleaned.columns:
        cleaned["pass_fail"] = cleaned["percentage"].apply(
            lambda x: "Pass" if pd.notna(x) and x >= pass_mark else (
                "Fail" if pd.notna(x) else "N/A"
            )
        )
        report["steps"].append(f"Computed pass/fail using pass mark of {pass_mark}%.")

    # ── Final summary ─────────────────────────────────────────────
    cleaned = cleaned.reset_index(drop=True)
    report["cleaned_rows"] = len(cleaned)
    report["cleaned_columns"] = len(cleaned.columns)
    report["columns"] = list(cleaned.columns)

    return cleaned, report


def generate_cleaning_report(report: Dict) -> str:
    """Generate a human-readable cleaning report text."""
    lines = [
        "═══ Data Cleaning Report ═══",
        f"Original: {report['original_rows']} rows × {report['original_columns']} columns",
        f"Cleaned:  {report['cleaned_rows']} rows × {report['cleaned_columns']} columns",
        "",
        "Steps performed:",
    ]
    for i, step in enumerate(report["steps"], 1):
        lines.append(f"  {i}. {step}")

    if report["warnings"]:
        lines.append("")
        lines.append("⚠ Warnings:")
        for w in report["warnings"]:
            lines.append(f"  • {w}")

    return "\n".join(lines)


# ── Helpers ─────────────────────────────────────────────────────────

def _find_column(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    """Find the first column in df that matches any of the aliases."""
    cols_lower = {str(c).lower().strip(): c for c in df.columns}
    for alias in aliases:
        if alias in cols_lower:
            return cols_lower[alias]
    return None
