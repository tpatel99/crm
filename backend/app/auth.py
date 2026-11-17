from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth = OAuth()
if settings.okta_issuer:
    oauth.register(
        name="okta",
        server_metadata_url=f"{settings.okta_issuer}/.well-known/openid-configuration",
        client_id=settings.okta_client_id,
        client_secret=settings.okta_client_secret,
        client_kwargs={"scope": "openid email profile"},
    )


def _upsert_user(db: Session, email: str, name: str) -> User:
    email = email.lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        first = db.scalar(select(func.count(User.id))) == 0
        user = User(email=email, name=name, is_admin=first)  # first user becomes admin
        db.add(user)
        db.commit()
    return user


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    if settings.auth_disabled:
        return _upsert_user(db, "local@crm.local", "Local Admin")
    uid = request.session.get("uid")
    user = db.get(User, uid) if uid else None
    if not user or not user.is_active:
        raise HTTPException(401, "Not authenticated")
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    return user


@router.get("/login")
async def login(request: Request):
    if not settings.okta_issuer:
        raise HTTPException(503, "Okta not configured")
    return await oauth.okta.authorize_redirect(request, f"{settings.base_url}/api/auth/callback")


@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.okta.authorize_access_token(request)
    info = token.get("userinfo") or {}
    if not info.get("email"):
        raise HTTPException(400, "Okta did not return an email")
    user = _upsert_user(db, info["email"], info.get("name", ""))
    if not user.is_active:
        raise HTTPException(403, "Account disabled")
    request.session["uid"] = user.id
    return RedirectResponse("/")


@router.post("/dev-login")
def dev_login(request: Request, email: str = "dev@example.com", db: Session = Depends(get_db)):
    if not settings.dev_auth:
        raise HTTPException(404)
    request.session["uid"] = _upsert_user(db, email, "Dev User").id
    return {"ok": True}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email, "name": user.name, "is_admin": user.is_admin,
            "auth_disabled": settings.auth_disabled}
