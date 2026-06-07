<p align="center">
  <h1 align="center">Present Yourself</h1>
  <p align="center">
    <strong>AI-powered slide deck generation platform</strong>
    <br />
    From topic to research to AI authoring to branded PPTX in minutes.
  </p>
</p>

## 🚀 Overview

**Present Yourself** is a full-stack platform that leverages AI to automatically generate professional, branded presentation slide decks. Simply provide a topic, and the system handles the research, content authoring, and presentation generation, outputting a polished PowerPoint (`.pptx`) file.

## 🏗️ Architecture & Tech Stack

The platform is designed as a monorepo containing a modern web frontend and a robust asynchronous backend API.

- **Frontend (`apps/web`)**: Next.js 16 (React 19, App Router) with Tailwind CSS v4 for a responsive, modern UI.
- **Backend (`apps/api`)**: FastAPI (Python 3.13) paired with Celery workers for handling intensive tasks like research, generation, rendering, and exporting.
- **Infrastructure**: Docker Compose for local development (Postgres 16, Redis 7, MinIO) and Render for production deployment.

## 📂 Project Structure

```text
.
├── apps/
│   ├── api/                 # FastAPI backend & Celery workers
│   └── web/                 # Next.js frontend application
├── docs/                    # Design docs (PRD, tech stack, UI/UX)
├── infra/                   # Render infrastructure definitions
└── docker-compose.yml       # Local development dependencies
```

## 🛠️ Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- Node.js (v20+) & `pnpm`
- Python 3.13

### 1. Boot Infrastructure
Start the required local services (Postgres, Redis, MinIO):
```bash
docker compose up -d
```

### 2. Setup Backend API
In a new terminal, initialize and run the FastAPI server:
```bash
cd apps/api
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Unix/macOS: source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```
*API will be available at `http://localhost:8000`*

### 3. Start Celery Worker
In a new terminal, start the background worker for AI tasks:
```bash
cd apps/api
# Ensure your virtual environment is activated
celery -A app.tasks.celery_app worker -l info -Q generate,render,export
```

### 4. Setup Frontend Web App
In a new terminal, install dependencies and start the development server:
```bash
cd apps/web
pnpm install
pnpm dev
```
*Web app will be available at `http://localhost:3000`*

## ☁️ Production Deployment

The project is configured for automated deployment on Render. The blueprint is located at `infra/render.yaml`.
For detailed topology and architecture, refer to the [Tech Stack Documentation](docs/01-tech-stack.md).

## 📖 Documentation

Comprehensive documentation covering requirements, design, and architecture can be found in the [docs directory](docs/README.md).

---
*Built with modern web technologies and advanced AI authoring pipelines.*
