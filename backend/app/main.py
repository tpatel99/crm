from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .auth import router as auth_router
from .config import settings
from .db import Base, engine
from .routes import router

settings.validate_for_startup()
Base.metadata.create_all(engine)  # swap for Alembic migrations once the schema stabilises

app = FastAPI(title="CRM")
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, same_site="lax",
                   https_only=settings.base_url.startswith("https"), max_age=60 * 60 * 12)
app.include_router(auth_router)
app.include_router(router)


@app.get("/healthz")
def healthz():
    return {"ok": True}


static = Path(settings.static_dir)
if static.is_dir():
    app.mount("/assets", StaticFiles(directory=static / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = static / path
        return FileResponse(f if path and f.is_file() else static / "index.html")
