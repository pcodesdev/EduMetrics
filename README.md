# EduMetrics
Open-source student performance analytics platform for schools, classes, and individual learners.

EduMetrics helps you upload assessment data, clean it, generate transparent insights, and produce printable reports with charts. The analytics engine is deterministic and statistics-based (no LLM dependency for scoring logic).

## Table of Contents
- Overview
- Key Features
- Tech Stack
- Project Structure
- Data Flow
- Security and Data Lifecycle
- Grading Model
- Requirements
- Quick Start (Local)
- Configuration
- API Overview
- Frontend SEO and Analytics
- Reports
- Testing
- Deployment Notes
- Troubleshooting
- Roadmap Ideas
- Contributing
- License and Disclaimer

## Overview
EduMetrics is built as a full-stack web app:
- Backend: FastAPI + pandas/scipy/report generation.
- Frontend: React + Vite + Tailwind + Recharts.

The app supports:
- Uploading CSV/Excel/ODS files.
- Mapping columns from heterogeneous sheets.
- Auto-cleaning and normalization.
- Analytics dashboards (overview, subjects, gaps, risk, term comparison).
- Student profile drilldowns.
- Class and student report exports (PDF), plus Excel export.

## Key Features
- Upload + mapping workflow for wide/long exam data.
- Class-scoped analytics across the app.
- At-risk student detection and explainable factors.
- Rule-based insights with actionable recommendations.
- Term-by-term comparison and trend analysis.
- Browser-preview + downloadable PDF reports.
- Data security workflow:
  - Temporary upload/session cleanup.
  - Generated report files auto-deleted after response.
- Branding, favicon, footer links.
- SEO metadata + optional GA4 analytics.

## Tech Stack
### Backend
- Python 3.11
- FastAPI
- pandas, numpy, scipy
- reportlab, openpyxl
- python-dotenv, python-multipart

### Frontend
- React 19
- Vite 7
- Tailwind CSS 4
- Recharts
- React Router
- Lucide icons

## Project Structure
```text
EduMetrics/
  backend/
    core/                 # Analytics, insights, grading, report builders
    routes/               # FastAPI route modules
    sample_data/          # Example datasets
    uploads/              # Temp uploads + reports (ephemeral in runtime)
    main.py               # FastAPI app entry
    requirements.txt
  frontend/
    public/               # Static assets (logo, robots, sitemap)
    src/
      components/
      pages/
      lib/                # SEO + analytics instrumentation
      App.jsx
      main.jsx
    index.html
    package.json
  docker-compose.yml
  .env.example
```

## Data Flow
1. Upload file (`/api/upload/file`).
2. Auto-detect layout and suggest mapping.
3. Confirm mapping (`/api/upload/confirm-mapping`).
4. Clean and normalize data.
5. Use cleaned payload in analytics/report endpoints.
6. Render dashboards and generate exports.

## Security and Data Lifecycle
### What gets deleted
- Session data in memory is purged:
  - immediately after confirm-mapping response,
  - on explicit `end-session`,
  - on TTL expiry.
- Temporary uploaded files are deleted when session drops.
- Generated report files are deleted automatically after file response is sent.

### What does not get deleted by server
- Files that users explicitly save/download on their own device/browser.

### Relevant controls
- `SERVE_UPLOADS=false` by default (safer; no static `/uploads` mount).
- CORS is env-driven (`CORS_ORIGINS`).

## Grading Model
The app uses a universal grading model globally:
- `A, B, C, D, E, F`
- No Kenya-specific grading dependency in final outputs.

Term ordering is normalized and deterministic (`Term 1`, `Term 2`, `Term 3`), with robust matching across formatting variants.

## Requirements
- Python 3.11+
- Node.js 18+
- npm 9+

## Quick Start (Local)
### 1. Backend
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at `http://localhost:8000`.

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Configuration
Root `.env.example` contains backend defaults:
```env
SCHOOL_NAME=My School
PASS_MARK=50
MAX_UPLOAD_SIZE_MB=50
```

Additional backend envs supported:
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
SERVE_UPLOADS=false
```

Frontend env template (`frontend/.env.example`):
```env
VITE_SITE_URL=https://example.com
VITE_GA_MEASUREMENT_ID=
```

## API Overview
Base: `/api`

### Upload
- `POST /upload/file`
- `POST /upload/confirm-mapping`
- `GET /upload/sample/{dataset_name}`
- `GET /upload/sessions`
- `GET /upload/session/{session_id}`
- `POST /upload/end-session`

### Cleaning
- `POST /clean/preview`
- `POST /clean/apply`

### Analytics
- `POST /analyze/overview`
- `POST /analyze/subjects`
- `POST /analyze/risk`
- `POST /analyze/gaps`
- `POST /analyze/insights`
- `POST /analyze/student/{student_id}`
- `POST /analyze/term-comparison`
- `GET /analyze/school-modes`

### Reports
- `POST /reports/school-pdf`
- `POST /reports/class-pdf`
- `POST /reports/student-pdf`
- `POST /reports/excel`

## Frontend SEO and Analytics
### SEO
- Static SEO tags in `frontend/index.html`.
- Dynamic route-aware titles/descriptions/canonical in:
  - `frontend/src/lib/siteInstrumentation.js`

### Crawlers
- `frontend/public/robots.txt`
- `frontend/public/sitemap.xml` (replace `https://example.com` with your real domain).

### GA4 (optional)
Set:
```env
VITE_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```
Pageview tracking is automatic on route changes.

## Reports
Supported outputs:
- Class Performance Report (PDF)
- Student Report Card (PDF)
- Excel export

Current behavior:
- Reports can be previewed in browser for printing.
- Files are deleted server-side right after response is sent.

## Testing
Backend tests are under `backend/tests`.

From `backend/`:
```bash
pytest
```

## Deployment Notes
### Docker
There is a `docker-compose.yml`, but currently:
- `backend` service is defined and has a Dockerfile.
- `frontend` service in compose references `frontend/Dockerfile`, which is not present in this repository.

Recommended options:
- Run frontend via Vite for now, or
- Add a frontend Dockerfile before using compose in production.

### Production checklist
- Set `CORS_ORIGINS` to your actual frontend domain(s).
- Keep `SERVE_UPLOADS=false` unless explicitly needed.
- Set `VITE_SITE_URL` to your production URL.
- Update `frontend/public/sitemap.xml` domain.
- Add `VITE_GA_MEASUREMENT_ID` if analytics is desired.

## Troubleshooting
### “Term 1 data missing” or “insufficient data” in term comparison
- Ensure term values are present and consistent.
- Current backend normalizes term labels (e.g., `term 1`, `T1`, ` Term 1 ` -> `Term 1`).

### Report generation works but files not found on server
- Expected. Report files are auto-deleted after response delivery.

### SEO build warnings about `%VITE_SITE_URL%`
- Resolved by using safe static defaults in `index.html` and runtime overrides.

## Roadmap Ideas
- Add frontend Dockerfile and fully verified compose flow.
- Add OpenAPI documentation examples per endpoint.
- Add role-based access and authentication.
- Add persistent audit logs for report generation.
- Add i18n and localization.

## Contributing
Contributions are welcome:
- Open an issue for bugs/feature requests.
- Submit a PR with a clear description and test notes.
- Keep changes focused and documented.

Useful links:
- GitHub: https://github.com/pcodesdev
- LinkedIn: https://www.linkedin.com/in/pcodesdev/
- Medium: https://medium.com/@pcodesdev
- Email: pcodesdev@gmail.com

## License and Disclaimer
EduMetrics is open-source software provided "as is", without warranty of any kind, express or implied. Use in educational decision-making should include human review and institutional policy checks.
