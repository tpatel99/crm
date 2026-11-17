import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models as m, schemas as s
from .auth import admin_user, current_user
from .db import get_db
from .models import STAGES, STAGE_PROB

router = APIRouter(prefix="/api", dependencies=[Depends(current_user)])


def crud(path: str, Model, In, Out, order=None):
    """Register list/create/get/update/delete for a model."""

    @router.get(f"/{path}", response_model=list[Out], name=f"list_{path}")
    def list_(db: Session = Depends(get_db)):
        stmt = select(Model).order_by(order if order is not None else Model.id.desc())
        return db.scalars(stmt).all()

    @router.post(f"/{path}", response_model=Out, status_code=201, name=f"create_{path}")
    def create(data: In, db: Session = Depends(get_db), user: m.User = Depends(current_user)):
        obj = Model(**data.model_dump())
        if Model is m.Deal and obj.owner_id is None:
            obj.owner_id = user.id
        if Model is m.Task and obj.assignee_id is None:
            obj.assignee_id = user.id
        if Model is m.Deal:
            _check_stage(obj.stage)
        db.add(obj)
        db.commit()
        return obj

    @router.get(f"/{path}/{{id}}", response_model=Out, name=f"get_{path}")
    def get(id: int, db: Session = Depends(get_db)):
        obj = db.get(Model, id)
        if not obj:
            raise HTTPException(404)
        return obj

    @router.put(f"/{path}/{{id}}", response_model=Out, name=f"update_{path}")
    def update(id: int, data: In, db: Session = Depends(get_db)):
        obj = db.get(Model, id)
        if not obj:
            raise HTTPException(404)
        for k, v in data.model_dump().items():
            setattr(obj, k, v)
        if Model is m.Deal:
            _check_stage(obj.stage)
            _touch_closed(obj)
        db.commit()
        return obj

    @router.delete(f"/{path}/{{id}}", status_code=204, name=f"delete_{path}")
    def delete(id: int, db: Session = Depends(get_db)):
        obj = db.get(Model, id)
        if not obj:
            raise HTTPException(404)
        db.delete(obj)
        db.commit()


def _check_stage(stage: str):
    if stage not in STAGES:
        raise HTTPException(422, f"stage must be one of {STAGES}")


def _touch_closed(deal: m.Deal):
    if deal.stage in ("Won", "Lost"):
        deal.closed_at = deal.closed_at or datetime.utcnow()
    else:
        deal.closed_at = None


crud("companies", m.Company, s.CompanyIn, s.CompanyOut)
crud("contacts", m.Contact, s.ContactIn, s.ContactOut)
crud("deals", m.Deal, s.DealIn, s.DealOut)
crud("tasks", m.Task, s.TaskIn, s.TaskOut, order=m.Task.done.asc())


@router.patch("/deals/{id}/stage", response_model=s.DealOut)
def move_deal(id: int, data: s.StageIn, db: Session = Depends(get_db)):
    deal = db.get(m.Deal, id)
    if not deal:
        raise HTTPException(404)
    _check_stage(data.stage)
    deal.stage = data.stage
    _touch_closed(deal)
    db.commit()
    return deal


@router.get("/stages")
def stages():
    return STAGES


@router.get("/activities", response_model=list[s.ActivityOut])
def list_activities(deal_id: int | None = None, contact_id: int | None = None,
                    company_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(m.Activity).order_by(m.Activity.created_at.desc())
    for col, val in ((m.Activity.deal_id, deal_id), (m.Activity.contact_id, contact_id),
                     (m.Activity.company_id, company_id)):
        if val is not None:
            stmt = stmt.where(col == val)
    return db.scalars(stmt.limit(200)).all()


@router.post("/activities", response_model=s.ActivityOut, status_code=201)
def add_activity(data: s.ActivityIn, db: Session = Depends(get_db), user: m.User = Depends(current_user)):
    act = m.Activity(**data.model_dump(), user_id=user.id)
    db.add(act)
    db.commit()
    return act


# ---- Reports -------------------------------------------------------------
@router.get("/reports/summary")
def summary(db: Session = Depends(get_db)):
    deals = db.scalars(select(m.Deal)).all()
    by_stage = {st: {"count": 0, "value": 0.0} for st in STAGES}
    for d in deals:
        by_stage[d.stage]["count"] += 1
        by_stage[d.stage]["value"] += float(d.value or 0)
    open_ = [d for d in deals if d.stage not in ("Won", "Lost")]
    won, lost = by_stage["Won"]["count"], by_stage["Lost"]["count"]
    return {
        "by_stage": by_stage,
        "open_value": sum(float(d.value or 0) for d in open_),
        "weighted_forecast": sum(float(d.value or 0) * STAGE_PROB[d.stage] for d in open_),
        "won_value": by_stage["Won"]["value"],
        "win_rate": won / (won + lost) if (won + lost) else None,
    }


# ---- CSV import/export ---------------------------------------------------
CSV_FIELDS = {
    "contacts": ["first_name", "last_name", "email", "phone", "title"],
    "companies": ["name", "website", "industry", "notes"],
    "deals": ["title", "value", "stage", "expected_close"],
}
MODELS = {"contacts": m.Contact, "companies": m.Company, "deals": m.Deal}


@router.get("/export/{kind}.csv")
def export_csv(kind: str, db: Session = Depends(get_db)):
    if kind not in CSV_FIELDS:
        raise HTTPException(404)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(CSV_FIELDS[kind])
    for row in db.scalars(select(MODELS[kind])).all():
        w.writerow([getattr(row, f) if getattr(row, f) is not None else "" for f in CSV_FIELDS[kind]])
    buf.seek(0)
    return StreamingResponse(iter([buf.read()]), media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename={kind}.csv"})


@router.post("/import/{kind}")
async def import_csv(kind: str, file: UploadFile, db: Session = Depends(get_db)):
    if kind not in CSV_FIELDS:
        raise HTTPException(404)
    text = (await file.read()).decode("utf-8-sig")
    created, errors = 0, []
    for i, row in enumerate(csv.DictReader(io.StringIO(text)), start=2):
        try:
            data = {f: (row.get(f) or "").strip() for f in CSV_FIELDS[kind]}
            if not any(data.values()):
                continue  # skip blank rows
            required = CSV_FIELDS[kind][0]
            if not data[required]:
                raise ValueError(f"{required} is required")
            if kind == "deals":
                data["value"] = float(data["value"] or 0)
                data["stage"] = data["stage"] or "Lead"
                _check_stage(data["stage"])
                data["expected_close"] = (datetime.strptime(data["expected_close"], "%Y-%m-%d").date()
                                          if data["expected_close"] else None)
            db.add(MODELS[kind](**data))
            created += 1
        except Exception as e:  # report bad rows, keep going
            errors.append({"row": i, "error": str(getattr(e, "detail", e))})
    db.commit()
    return {"created": created, "errors": errors}


# ---- Admin: user management ---------------------------------------------
@router.get("/users", response_model=list[s.UserOut])
def users(db: Session = Depends(get_db)):
    return db.scalars(select(m.User).order_by(m.User.email)).all()


@router.patch("/users/{id}", response_model=s.UserOut)
def patch_user(id: int, data: s.UserPatch, db: Session = Depends(get_db),
               admin: m.User = Depends(admin_user)):
    u = db.get(m.User, id)
    if not u:
        raise HTTPException(404)
    if u.id == admin.id and (data.is_admin is False or data.is_active is False):
        raise HTTPException(400, "You cannot demote or disable yourself")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(u, k, v)
    db.commit()
    return u
