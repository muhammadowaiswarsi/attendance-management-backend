from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmployeeCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str | None = None
    designation: str | None = None
    salary: Decimal = Field(gt=0)
    joining_date: date
    address: str | None = None
    department_id: int


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    phone_number: str | None = None
    designation: str | None = None
    salary: Decimal | None = Field(default=None, gt=0)
    address: str | None = None
    department_id: int | None = None


class EmployeeResponse(BaseModel):
    id: int
    employee_code: str
    full_name: str
    email: EmailStr
    phone_number: str | None
    designation: str | None
    salary: Decimal
    joining_date: date
    address: str | None
    is_active: bool
    password_set: bool = False
    department_id: int
    department_name: str

    model_config = ConfigDict(from_attributes=True)
