from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PayslipFieldValueInput(BaseModel):
    field_key: str = Field(min_length=1, max_length=80)
    value: float = Field(ge=0)


class PayslipFieldValueSnapshot(BaseModel):
    field_id: int | None = None
    field_key: str
    name: str
    field_type: str
    category: str
    value: float


class PayslipCreate(BaseModel):
    employee_id: int
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000)
    basic_salary: float = Field(gt=0)
    allowances: float = Field(default=0, ge=0)
    deductions: float = Field(default=0, ge=0)
    field_values: list[PayslipFieldValueInput] = Field(default_factory=list)


class PayslipResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    month: int
    year: int
    basic_salary: float
    allowances: float
    deductions: float
    field_values: list[PayslipFieldValueSnapshot] = Field(default_factory=list)
    net_salary: float
    pdf_path: str | None
    sent_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("field_values", mode="before")
    @classmethod
    def default_field_values(cls, value):
        return value or []
