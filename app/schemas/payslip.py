from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PayslipCreate(BaseModel):
    employee_id: int
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000)
    basic_salary: float = Field(gt=0)
    allowances: float = Field(default=0, ge=0)
    deductions: float = Field(default=0, ge=0)


class PayslipResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    month: int
    year: int
    basic_salary: float
    allowances: float
    deductions: float
    net_salary: float
    pdf_path: str | None
    sent_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
