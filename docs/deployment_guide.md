# EduMetrics — Deployment Guide

## Prerequisites

| Requirement | Version |
|------------|---------|
| Python | 3.10 or higher |
| Node.js | 18 or higher |
| npm | 9 or higher |
| Docker (optional) | 20+ |

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd EduMetrics
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp ../.env.example .env
# Edit .env if needed (SCHOOL_NAME, PASS_MARK)

# Start the backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`. It proxies `/api` requests to the backend automatically.

## Docker Setup

The simplest way to run the full stack:

```bash
docker-compose up --build
```

This starts both backend and frontend containers. The app will be available at `http://localhost:5173`.

### Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8000 | FastAPI server |
| `frontend` | 5173 | Vite dev server |

## Environment Variables

Configure via `.env` file in the project root:

| Variable | Default | Description |
|----------|---------|-------------|
| `SCHOOL_NAME` | `My School` | School name shown in reports and PDFs |
| `PASS_MARK` | `50` | Pass/fail threshold (percentage) |

## Production Deployment

### Backend (uvicorn + gunicorn)

```bash
cd backend
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend (static build)

```bash
cd frontend
npm run build
# Serve the dist/ folder with any static file server (nginx, caddy, etc.)
```

### Nginx Example

```nginx
server {
    listen 80;
    server_name edumetrics.example.com;

    # Frontend
    location / {
        root /var/www/edumetrics/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Offline Usage

EduMetrics is designed for **100% offline operation**:

- No external API calls or AI dependencies
- All analytics computed locally via NumPy, SciPy, and pandas
- No internet connection required after initial setup
- Sample data included for immediate testing

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure virtual environment is active and `pip install -r requirements.txt` was run |
| Frontend can't reach API | Verify backend is running on port 8000; check Vite proxy config |
| File upload fails | Ensure `uploads/` directory exists and is writable |
| PDF generation error | Install system fonts; check ReportLab and matplotlib are installed |
| Port already in use | Kill existing process or use `--port <other-port>` flag |
