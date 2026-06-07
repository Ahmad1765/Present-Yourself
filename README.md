# Present Yourself

AI-powered slide deck generation platform. Web app on Render. Topic → research → AI authoring → branded PPTX.

## Layout

```
apps/
  api/        FastAPI + Celery worker (Python 3.13)
  web/        Next.js 16 (React 19, App Router, Tailwind v4)
docs/         Design docs (PRD, requirements, tech stack, UI/UX)
infra/        Render blueprint
docker-compose.yml   Local dev: Postgres 16, Redis 7, MinIO
```

## Quick start (local)

```bash
# 1. Boot infra
docker compose up -d

# 2. Backend
cd apps/api
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Worker (new shell)
cd apps/api
celery -A app.tasks.celery_app worker -l info -Q research,generate,render,export

# 4. Frontend (new shell)
cd apps/web
pnpm install
pnpm dev
```

App at `http://localhost:3000`. API at `http://localhost:8000`.

## Production

Render Blueprint: `infra/render.yaml`. See [docs/01-tech-stack.md](docs/01-tech-stack.md) §2 for topology.

## Docs

See [docs/README.md](docs/README.md).
