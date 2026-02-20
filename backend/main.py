"""
EduMetrics — Student Performance Analytics Tool
FastAPI backend entry point.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.upload import router as upload_router
from routes.clean import router as clean_router
from routes.analyze import router as analyze_router
from routes.reports import router as reports_router

# Load environment
load_dotenv()

SCHOOL_NAME = os.getenv("SCHOOL_NAME", "My School")
PASS_MARK = int(os.getenv("PASS_MARK", "50"))
# Comma-separated allowed origins, e.g. http://localhost:5173,https://app.example.com
raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]
SERVE_UPLOADS = os.getenv("SERVE_UPLOADS", "false").strip().lower() in {"1", "true", "yes", "on"}
# Keep upload path stable regardless of where uvicorn is started.
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="EduMetrics API",
    description=(
        "Student Performance Analytics — all insights generated via "
        "statistical computation, zero AI dependency."
    ),
    version="1.0.0",
)

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional static file serving. Keep disabled by default for better data privacy.
if SERVE_UPLOADS:
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Register route modules
app.include_router(upload_router, prefix="/api/upload", tags=["Upload"])
app.include_router(clean_router, prefix="/api/clean", tags=["Cleaning"])
app.include_router(analyze_router, prefix="/api/analyze", tags=["Analytics"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "school_name": SCHOOL_NAME,
        "pass_mark": PASS_MARK,
    }


@app.get("/api/config")
async def get_config():
    """Return server configuration to the frontend."""
    return {
        "school_name": SCHOOL_NAME,
        "pass_mark": PASS_MARK,
    }
