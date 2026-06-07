# Present Yourself — API

FastAPI + Celery backend.

## Run locally

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate            # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Make sure docker-compose is up at repo root:
#   docker compose up -d
# Then copy .env.example → .env at repo root and fill MASTER_ENCRYPTION_KEY:
#   python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

In another shell:

```bash
celery -A app.tasks.celery_app worker -l info -Q generate,render,export
```

## Dev auth bypass

When `CLERK_JWKS_URL` is empty and `ENV != prod`, requests with header
`X-Dev-User-Id: any-string` are auto-authenticated and upsert that user.

```bash
curl -H "X-Dev-User-Id: dev1" http://localhost:8000/v1/me
```
