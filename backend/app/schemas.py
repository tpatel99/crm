from datetime import date
from pydantic import BaseModel, ConfigDict


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CompanyIn(BaseModel):
    name: str
    website: str = ""
    industry: str = ""
    notes: str = ""


class CompanyOut(CompanyIn, ORM):
    id: int


class ContactIn(BaseModel):
    first_name: str
    last_name: str = ""
    email: str = ""
    phone: str = ""
    title: str = ""
    company_id: int | None = None


class ContactOut(ContactIn, ORM):
    id: int


class DealIn(BaseModel):
    title: str
    value: float = 0
    stage: str = "Lead"
    expected_close: date | None = None
    company_id: int | None = None
    contact_id: int | None = None
    owner_id: int | None = None


class DealOut(DealIn, ORM):
    id: int


class StageIn(BaseModel):
    stage: str


class ActivityIn(BaseModel):
    kind: str = "note"
    body: str = ""
    deal_id: int | None = None
    contact_id: int | None = None
    company_id: int | None = None


class ActivityOut(ActivityIn, ORM):
    id: int
    user_id: int | None
    created_at: object


class TaskIn(BaseModel):
    title: str
    due_date: date | None = None
    done: bool = False
    deal_id: int | None = None
    contact_id: int | None = None
    assignee_id: int | None = None


class TaskOut(TaskIn, ORM):
    id: int


class UserOut(ORM):
    id: int
    email: str
    name: str
    is_admin: bool
    is_active: bool


class UserPatch(BaseModel):
    is_admin: bool | None = None
    is_active: bool | None = None
