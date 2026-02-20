"""
Clean routes — data cleaning endpoints.
"""

import os
from fastapi import APIRouter, HTTPException
import pandas as pd

from core.cleaner import clean_dataframe, generate_cleaning_report

router = APIRouter()


@router.post("/preview")
async def preview_cleaning(payload: dict):
    """
    Preview what cleaning would do to the dataset without committing.
    Expects: { "data": [...records...], "options": { "treat_missing_as_zero": false } }
    """
    data = payload.get("data")
    options = payload.get("options", {})

    if not data:
        raise HTTPException(400, "No data provided.")

    df = pd.DataFrame(data)
    pass_mark = int(os.getenv("PASS_MARK", "50"))

    cleaned_df, report = clean_dataframe(
        df,
        pass_mark=pass_mark,
        treat_missing_as_zero=options.get("treat_missing_as_zero", False),
    )

    return {
        "cleaning_report": report,
        "cleaned_row_count": len(cleaned_df),
        "preview": cleaned_df.head(20).to_dict(orient="records"),
    }


@router.post("/apply")
async def apply_cleaning(payload: dict):
    """
    Apply cleaning to the dataset and return the full cleaned result.
    Expects: { "data": [...records...], "options": { "treat_missing_as_zero": false } }
    """
    data = payload.get("data")
    options = payload.get("options", {})

    if not data:
        raise HTTPException(400, "No data provided.")

    df = pd.DataFrame(data)
    pass_mark = int(os.getenv("PASS_MARK", "50"))

    cleaned_df, report = clean_dataframe(
        df,
        pass_mark=pass_mark,
        treat_missing_as_zero=options.get("treat_missing_as_zero", False),
    )

    return {
        "cleaning_report": report,
        "cleaned_data": cleaned_df.to_dict(orient="records"),
        "cleaned_row_count": len(cleaned_df),
        "columns": list(cleaned_df.columns),
    }
