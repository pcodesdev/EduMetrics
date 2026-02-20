"""
parser.py — CSV, Excel, ODS ingestion with auto-detection.

Supports:
- CSV files
- Excel (.xlsx, .xls) — single and multi-sheet
- ODS (OpenDocument Spreadsheet)
- Auto-detect wide vs long format
- Fuzzy column name mapping
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

SAMPLE_DATA_DIR = Path(__file__).parent.parent / "sample_data"

# Common column name variations for auto-mapping
COLUMN_ALIASES = {
    "student_id": [
        "student_id", "studentid", "student id", "id", "admission_no",
        "admission no", "adm_no", "adm no", "reg_no", "registration",
        "index_no", "index no", "student_number", "student number", "s/n",
    ],
    "name": [
        "name", "student_name", "student name", "full_name", "full name",
        "pupil_name", "pupil name", "learner_name", "learner name",
        "first_name", "surname", "last_name",
    ],
    "gender": [
        "gender", "sex", "gen", "m/f",
    ],
    "class": [
        "class", "grade", "form", "level", "year", "standard",
        "class_name", "class name", "grade_level", "grade level",
        "stream", "section",
    ],
    "stream": [
        "stream", "section", "arm", "division",
    ],
    "school": [
        "school", "school_name", "school name", "institution",
        "centre", "center",
    ],
    "region": [
        "region", "county", "district", "sub_county", "sub county",
        "zone", "ward", "province", "state", "area",
    ],
    "subject": [
        "subject", "subject_name", "subject name", "course",
        "paper", "exam_subject",
    ],
    "score": [
        "score", "marks", "mark", "total", "total_score", "total score",
        "raw_score", "raw score", "points", "result", "perc", "percentage",
    ],
    "max_score": [
        "max_score", "max score", "max_marks", "max marks", "total_marks",
        "total marks", "out_of", "out of", "max", "maximum",
    ],
    "term": [
        "term", "semester", "period", "exam_period", "exam period",
        "session",
    ],
    "exam_name": [
        "exam_name", "exam name", "assessment", "assessment_name",
        "assessment name", "test", "exam_type", "exam type", "exam",
    ],
    "year": [
        "year", "academic_year", "academic year", "acad_year",
    ],
}


def parse_upload(file_path: str) -> Dict[str, pd.DataFrame]:
    """
    Parse an uploaded file and return a dict of {sheet_name: DataFrame}.
    For CSV files, returns {"Sheet1": df}.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".csv":
        df = pd.read_csv(file_path, dtype=str)
        return {"Sheet1": df}

    elif ext in (".xlsx", ".xls"):
        engine = "openpyxl" if ext == ".xlsx" else "xlrd"
        xls = pd.ExcelFile(file_path, engine=engine)
        sheets = {}
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
            # Skip empty sheets
            if not df.empty and len(df.columns) > 1:
                sheets[sheet_name] = df
        if not sheets:
            raise ValueError("No valid sheets found in the Excel file.")
        return sheets

    elif ext == ".ods":
        xls = pd.ExcelFile(file_path, engine="odf")
        sheets = {}
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
            if not df.empty and len(df.columns) > 1:
                sheets[sheet_name] = df
        if not sheets:
            raise ValueError("No valid sheets found in the ODS file.")
        return sheets

    else:
        raise ValueError(f"Unsupported file type: {ext}")


def detect_layout(df: pd.DataFrame) -> str:
    """
    Detect whether the data is in 'wide' or 'long' format.

    Wide format: one row per student, subjects as columns (column names are subject names).
    Long format: one row per student-subject combination (has a 'subject' column).
    """
    cols_lower = [str(c).lower().strip() for c in df.columns]

    # If there's a 'subject' column, it's likely long format
    subject_aliases = COLUMN_ALIASES["subject"]
    has_subject_col = any(alias in cols_lower for alias in subject_aliases)

    if has_subject_col:
        return "long"

    # Check if multiple columns look like subject names (wide format indicator)
    known_metadata_cols = set()
    for aliases in COLUMN_ALIASES.values():
        known_metadata_cols.update(aliases)

    non_metadata_cols = [c for c in cols_lower if c not in known_metadata_cols]

    # If there are 3+ columns that don't match known metadata fields,
    # they're probably subject columns → wide format
    if len(non_metadata_cols) >= 3:
        return "wide"

    return "long"  # Default to long


def suggest_column_mapping(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Suggest a mapping from expected field names to actual column names.
    Returns: { expected_field: actual_column_name_or_None }
    """
    cols = list(df.columns)
    cols_lower = {str(c).lower().strip(): c for c in cols}
    mapping: Dict[str, Optional[str]] = {}

    for field, aliases in COLUMN_ALIASES.items():
        matched = None
        for alias in aliases:
            if alias in cols_lower:
                matched = cols_lower[alias]
                break
        mapping[field] = matched

    return mapping


def convert_wide_to_long(df: pd.DataFrame, mapping: Dict[str, Optional[str]]) -> pd.DataFrame:
    """
    Convert a wide-format DataFrame to long format.
    Assumes non-mapped columns are subject score columns.
    """
    # Identify metadata columns (the ones that were mapped)
    metadata_cols = [v for v in mapping.values() if v and v in df.columns]
    # Internal/helper columns should never be interpreted as academic subjects.
    helper_cols = {"sheet_source", "source_sheet", "upload_session_id"}
    metadata_cols = list(dict.fromkeys(metadata_cols + [c for c in helper_cols if c in df.columns]))
    # Remaining columns are assumed to be subject scores
    subject_cols = [c for c in df.columns if c not in metadata_cols]

    if not subject_cols:
        return df

    id_vars = metadata_cols
    long_df = df.melt(
        id_vars=id_vars,
        value_vars=subject_cols,
        var_name="subject",
        value_name="score",
    )

    return long_df


def validate_data(df: pd.DataFrame) -> List[Dict]:
    """
    Validate the parsed data and return a list of issues found.
    """
    issues = []
    cols_lower = [str(c).lower().strip() for c in df.columns]

    # Check for required columns
    required_fields = ["name", "score"]
    mapping = suggest_column_mapping(df)

    for field in required_fields:
        if mapping.get(field) is None:
            issues.append({
                "type": "missing_column",
                "severity": "critical",
                "message": f"Required column '{field}' not found. "
                           f"Expected one of: {COLUMN_ALIASES.get(field, [])}",
            })

    # Check for empty dataframe
    if len(df) == 0:
        issues.append({
            "type": "empty_data",
            "severity": "critical",
            "message": "The uploaded file contains no data rows.",
        })

    # Check for score validity
    score_col = mapping.get("score")
    if score_col and score_col in df.columns:
        try:
            scores = pd.to_numeric(df[score_col], errors="coerce")
            invalid_count = scores.isna().sum() - df[score_col].isna().sum()
            if invalid_count > 0:
                issues.append({
                    "type": "invalid_scores",
                    "severity": "warning",
                    "message": f"{invalid_count} scores could not be parsed as numbers.",
                })

            # Check for out-of-range scores
            valid_scores = scores.dropna()
            if len(valid_scores) > 0:
                if (valid_scores < 0).any():
                    issues.append({
                        "type": "negative_scores",
                        "severity": "warning",
                        "message": "Some scores are negative — likely data entry errors.",
                    })
                if (valid_scores > 100).any():
                    max_score_col = mapping.get("max_score")
                    if max_score_col is None:
                        issues.append({
                            "type": "scores_over_100",
                            "severity": "info",
                            "message": (
                                "Some scores exceed 100. If these are raw scores, "
                                "please ensure a 'max_score' column is present for percentage conversion."
                            ),
                        })
        except Exception:
            pass

    # Check for duplicate students in same subject+term
    id_col = mapping.get("student_id") or mapping.get("name")
    subject_col = mapping.get("subject")
    term_col = mapping.get("term")

    if id_col and subject_col and id_col in df.columns and subject_col in df.columns:
        group_cols = [id_col, subject_col]
        if term_col and term_col in df.columns:
            group_cols.append(term_col)
        dupes = df.duplicated(subset=group_cols, keep=False)
        dupe_count = dupes.sum()
        if dupe_count > 0:
            issues.append({
                "type": "duplicates",
                "severity": "warning",
                "message": f"{dupe_count} duplicate entries detected (same student + subject + term).",
            })

    return issues
