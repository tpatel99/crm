# CRM

Sales-pipeline CRM for a small team (<10 users). FastAPI + Postgres, React (Vite/TS), Okta OIDC login.

## Features
Kanban deal board (drag between stages) · contacts & companies · activity log per deal · tasks with due dates ·
reports (open pipeline, weighted forecast, win rate) · CSV import/export · admin user management.
First user to sign in becomes admin.

## Run locally (no Okta needed)
    cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
    DEV_AUTH=true .venv/bin/uvicorn app.main:app --reload        # API on :8000
    cd frontend && npm install && npm run dev                      # UI on :5173
In dev mode, sign in by POSTing to `/api/auth/dev-login` (e.g. `curl -c- -X POST localhost:8000/api/auth/dev-login`
or use the Swagger UI at `/docs`); the browser UI's Okta button needs real Okta config.

## Deploy
`docker compose up --build` for a self-hosted stack, or deploy the Dockerfile to any container host
(Fly.io, Render, ECS…) with a managed Postgres and the env vars in `.env.example`.
Okta: create an OIDC Web App, set redirect URI to `<BASE_URL>/api/auth/callback`, assign only your team.

## Tests
    cd backend && .venv/bin/pytest
