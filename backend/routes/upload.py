"""
Upload routes — handle file upload, auto-detection, column mapping, and sample data loading.
"""

import os
import uuid
import json
import traceback
from pathlib import Path
from time import time
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Form

from core.parser import (
    parse_upload,
    detect_layout,
    suggest_column_mapping,
    convert_wide_to_long,
    SAMPLE_DATA_DIR,
)
from core.cleaner import clean_dataframe

router = APIRouter()

# In-memory session store: session_id → { raw_df, cleaned_df, mapping, metadata }
sessions: dict = {}
SESSION_TTL_SECONDS = 60 * 60  # 1 hour

WIDE_METADATA_FIELDS = {
    "student_id",
    "name",
    "student_name",
    "class",
    "gender",
    "region",
    "term",
    "year",
    "school",
    "stream",
    "school_type",
    "exam_name",
}

MAPPING_PRIORITY = [
    "student_id",
    "student_name",
    "name",
    "class",
    "term",
    "year",
    "exam_name",
    "gender",
    "region",
    "school",
    "stream",
    "school_type",
]


def _df_records(df):
    """
    Convert DataFrame rows to JSON-safe records.
    Ensures NaN/NaT become null so FastAPI serialization won't raise 500.
    """
    return json.loads(df.to_json(orient="records", date_format="iso"))


def _is_temp_upload_file(file_path: str) -> bool:
    try:
        p = Path(file_path).resolve()
        return p.is_file() and p.is_relative_to(UPLOAD_DIR.resolve())
    except Exception:
        return False


def _drop_session(session_id: str, delete_file: bool = True):
    s = sessions.pop(session_id, None)
    if not s:
        return
    if delete_file:
        file_path = s.get("file_path")
        if isinstance(file_path, str) and _is_temp_upload_file(file_path):
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception:
                pass


def _purge_expired_sessions():
    now = time()
    expired = []
    for sid, s in sessions.items():
        created_at = float(s.get("created_at", now))
        if (now - created_at) > SESSION_TTL_SECONDS:
            expired.append(sid)
    for sid in expired:
        _drop_session(sid, delete_file=True)

# Keep upload path stable regardless of process working directory.
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV, Excel, or ODS file.
    Returns auto-detected layout, suggested column mapping, and a preview.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in (".csv", ".xlsx", ".xls", ".ods"):
        raise HTTPException(400, f"Unsupported file type: {ext}. Use CSV, Excel, or ODS.")

    session_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{session_id}{ext}"

    try:
        _purge_expired_sessions()
        with open(save_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

        sheets_data = parse_upload(str(save_path))
        # sheets_data is a dict of {sheet_name: DataFrame}
        # For CSV it will be {"Sheet1": df}
        first_sheet = list(sheets_data.keys())[0]
        df = sheets_data[first_sheet]

        layout = detect_layout(df)
        mapping = suggest_column_mapping(df)

        # Store session
        sessions[session_id] = {
            "file_path": str(save_path),
            "layout": layout,
            "mapping": mapping,
            "original_filename": file.filename,
            "created_at": time(),
        }

        return {
            "session_id": session_id,
            "filename": file.filename,
            "sheets": list(sheets_data.keys()),
            "sheet_row_counts": {k: len(v) for k, v in sheets_data.items()},
            "layout": layout,
            "suggested_mapping": mapping,
            "columns": list(df.columns),
            "preview": _df_records(df.head(10)),
        }

    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(400, f"Failed to process upload '{file.filename}': {str(e)}")


@router.post("/confirm-mapping")
async def confirm_mapping(
    session_id: str = Form(...),
    mapping: str = Form(...),  # JSON string of column mapping
):
    """
    Confirm or override the column mapping, then clean the data.
    Returns the cleaning report and cleaned preview.
    """
    if session_id not in sessions:
        raise HTTPException(404, "Session not found. Please re-upload the file.")

    try:
        col_mapping = json.loads(mapping)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid mapping JSON.")

    session = sessions[session_id]
    try:
        # Auto-resolve duplicate source-column mappings by priority instead of failing.
        # This prevents common spreadsheet cases (e.g. "Student Name" mapped to both
        # name/student_name or "Year" selected in more than one field) from blocking upload.
        source_to_targets = {}
        for target, source in col_mapping.items():
            if isinstance(source, str) and source.strip():
                source_to_targets.setdefault(source, []).append(target)

        resolved_mapping = dict(col_mapping)
        priority_rank = {field: idx for idx, field in enumerate(MAPPING_PRIORITY)}

        for source, targets in source_to_targets.items():
            if len(targets) <= 1:
                continue
            best_target = sorted(
                targets,
                key=lambda t: priority_rank.get(t, len(MAPPING_PRIORITY) + 100)
            )[0]
            for t in targets:
                if t != best_target:
                    resolved_mapping[t] = ""

        col_mapping = resolved_mapping

        try:
            sheets_data = parse_upload(session["file_path"])
        except Exception as e:
            raise HTTPException(400, f"Failed to reopen uploaded file for mapping: {str(e)}")

        import pandas as pd
        # Merge all sheets into one DataFrame
        all_dfs = []
        for sheet_name, df in sheets_data.items():
            df = df.copy()
            if "sheet_source" not in df.columns:
                df["sheet_source"] = sheet_name
            all_dfs.append(df)

        combined_df = pd.concat(all_dfs, ignore_index=True)

        layout = session.get("layout", "long")

        # If source is wide (one row per student, subjects as columns),
        # convert it to long format expected by analytics.
        if layout == "wide":
            wide_mapping = {
                k: v for k, v in col_mapping.items()
                if k in WIDE_METADATA_FIELDS and v and v in combined_df.columns
            }
            combined_df = convert_wide_to_long(combined_df, wide_mapping)
            rename_map = {
                v: k for k, v in wide_mapping.items()
                if v in combined_df.columns
            }
        else:
            # Apply column mapping (rename columns)
            rename_map = {v: k for k, v in col_mapping.items() if v and v in combined_df.columns}

        combined_df = combined_df.rename(columns=rename_map)

        # Clean the data
        pass_mark = int(os.getenv("PASS_MARK", "50"))
        cleaned_df, cleaning_report = clean_dataframe(combined_df, pass_mark=pass_mark)

        # Store cleaned data in session
        session["cleaned_data"] = _df_records(cleaned_df)
        session["cleaning_report"] = cleaning_report
        session["column_mapping"] = col_mapping

        response = {
            "session_id": session_id,
            "cleaning_report": cleaning_report,
            "cleaned_row_count": len(cleaned_df),
            "cleaned_columns": list(cleaned_df.columns),
            "cleaned_data": _df_records(cleaned_df),
            "preview": _df_records(cleaned_df.head(10)),
        }
        # Security-first: delete session + uploaded file immediately after processing.
        _drop_session(session_id, delete_file=True)
        return response
    except HTTPException:
        _drop_session(session_id, delete_file=True)
        raise
    except Exception as e:
        traceback.print_exc()
        _drop_session(session_id, delete_file=True)
        raise HTTPException(400, f"Failed to confirm mapping: {str(e)}")


@router.get("/sample/{dataset_name}")
async def load_sample_data(dataset_name: str):
    """Load one of the bundled sample datasets."""
    sample_files = {
        "school": SAMPLE_DATA_DIR / "sample_school.csv",
        "district": SAMPLE_DATA_DIR / "sample_district.xlsx",
        "secondary": SAMPLE_DATA_DIR / "sample_school_secondary.csv",
        "cbc": SAMPLE_DATA_DIR / "sample_school_cbc.csv",
    }

    if dataset_name not in sample_files:
        raise HTTPException(404, f"Sample dataset '{dataset_name}' not found. Available: {list(sample_files.keys())}")

    file_path = sample_files[dataset_name]
    if not file_path.exists():
        raise HTTPException(404, f"Sample file not found on disk: {file_path}")

    _purge_expired_sessions()
    session_id = str(uuid.uuid4())

    try:
        sheets_data = parse_upload(str(file_path))
        first_sheet = list(sheets_data.keys())[0]
        df = sheets_data[first_sheet]
    except Exception as e:
        raise HTTPException(400, f"Failed to load sample dataset '{dataset_name}': {str(e)}")

    layout = detect_layout(df)
    mapping = suggest_column_mapping(df)

    sessions[session_id] = {
        "file_path": str(file_path),
        "layout": layout,
        "mapping": mapping,
        "original_filename": file_path.name,
        "created_at": time(),
    }

    return {
        "session_id": session_id,
        "filename": file_path.name,
        "sheets": list(sheets_data.keys()),
        "sheet_row_counts": {k: len(v) for k, v in sheets_data.items()},
        "layout": layout,
        "suggested_mapping": mapping,
        "columns": list(df.columns),
        "preview": _df_records(df.head(10)),
    }


@router.get("/sessions")
async def list_sessions():
    """List active sessions."""
    _purge_expired_sessions()
    return {
        sid: {
            "filename": s.get("original_filename"),
            "has_cleaned_data": "cleaned_data" in s,
        }
        for sid, s in sessions.items()
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session info."""
    _purge_expired_sessions()
    if session_id not in sessions:
        raise HTTPException(404, "Session not found.")
    s = sessions[session_id]
    return {
        "session_id": session_id,
        "filename": s.get("original_filename"),
        "layout": s.get("layout"),
        "mapping": s.get("mapping"),
        "has_cleaned_data": "cleaned_data" in s,
        "cleaning_report": s.get("cleaning_report"),
    }


@router.post("/end-session")
async def end_session(session_id: Optional[str] = Form(None)):
    """
    Explicitly end session and remove temporary data.
    If session_id is omitted, all in-memory sessions are purged (single-tenant dev mode).
    """
    if session_id:
        _drop_session(session_id, delete_file=True)
        return {"status": "ok", "message": f"Session {session_id} deleted."}

    for sid in list(sessions.keys()):
        _drop_session(sid, delete_file=True)
    return {"status": "ok", "message": "All active sessions deleted."}
