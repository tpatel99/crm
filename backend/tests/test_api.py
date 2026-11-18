import os

os.environ.update(DATABASE_URL="sqlite:///./test.db", DEV_AUTH="true")
import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


@pytest.fixture()
def c():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as client:
        yield client


def login(c, email="a@x.com"):
    assert c.post("/api/auth/dev-login", params={"email": email}).status_code == 200


def test_requires_auth(c):
    assert c.get("/api/deals").status_code == 401


def test_first_user_admin_second_not(c):
    login(c)
    assert c.get("/api/auth/me").json()["is_admin"] is True
    login(c, "b@x.com")
    assert c.get("/api/auth/me").json()["is_admin"] is False
    assert c.patch("/api/users/1", json={"is_admin": False}).status_code == 403


def test_deal_flow_and_report(c):
    login(c)
    co = c.post("/api/companies", json={"name": "Acme"}).json()
    d = c.post("/api/deals", json={"title": "Big", "value": 1000, "company_id": co["id"]}).json()
    assert c.patch(f"/api/deals/{d['id']}/stage", json={"stage": "Proposal"}).status_code == 200
    assert c.patch(f"/api/deals/{d['id']}/stage", json={"stage": "Bogus"}).status_code == 422
    r = c.get("/api/reports/summary").json()
    assert r["open_value"] == 1000 and r["weighted_forecast"] == 500
    c.patch(f"/api/deals/{d['id']}/stage", json={"stage": "Won"})
    r = c.get("/api/reports/summary").json()
    assert r["won_value"] == 1000 and r["win_rate"] == 1.0


def test_csv_roundtrip(c):
    login(c)
    csv_ = "first_name,last_name,email,phone,title\nAda,L,ada@x.com,,CTO\n,,,,\n"
    r = c.post("/api/import/contacts", files={"file": ("c.csv", csv_)}).json()
    assert r["created"] == 1 and r["errors"] == []
    assert "Ada" in c.get("/api/export/contacts.csv").text


def test_activity_and_task(c):
    login(c)
    d = c.post("/api/deals", json={"title": "D"}).json()
    c.post("/api/activities", json={"kind": "call", "body": "hi", "deal_id": d["id"]})
    assert len(c.get("/api/activities", params={"deal_id": d["id"]}).json()) == 1
    t = c.post("/api/tasks", json={"title": "follow up"}).json()
    assert t["assignee_id"] == 1


def test_auth_disabled_mode(c, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "auth_disabled", True)
    assert c.get("/api/auth/me").json()["is_admin"] is True
    assert c.post("/api/deals", json={"title": "x"}).status_code == 201


def test_startup_validation():
    import pytest
    from app.config import Settings
    with pytest.raises(RuntimeError):
        Settings(auth_disabled=False, dev_auth=False, okta_issuer="").validate_for_startup()
    with pytest.raises(RuntimeError):
        Settings(dev_auth=False, okta_issuer="https://x", okta_client_id="a", okta_client_secret="b").validate_for_startup()
    Settings(dev_auth=False, okta_issuer="https://x", okta_client_id="a", okta_client_secret="b", secret_key="k" * 32).validate_for_startup()
    Settings(auth_disabled=True).validate_for_startup()
    assert Settings(database_url="postgres://u:p@h/db").database_url.startswith("postgresql+psycopg://")
