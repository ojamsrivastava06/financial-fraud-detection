# Deployment Guide

## Prerequisites
- Python 3.11+
- Docker & Docker Compose (optional for containerized deployment)

## Local Development Deployment

### 1. Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 3. Run FastAPI Backend
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Run Streamlit Dashboard
```bash
streamlit run dashboard/app.py --server.port 8501
```

## Docker Containerized Deployment

```bash
docker-compose up --build -d
```
- FastAPI API will be available at `http://localhost:8000`
- Streamlit Dashboard will be available at `http://localhost:8501`
