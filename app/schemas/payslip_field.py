from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PayslipFieldType = Literal["amount"]
PayslipFieldCategory = Literal["earning", "deduction"]


class PayslipFieldCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    field_key: str | None = Field(default=None, min_length=1, max_length=80)
    field_type: PayslipFieldType = "amount"
    category: PayslipFieldCategory
    is_active: bool = True


class PayslipFieldUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: PayslipFieldCategory | None = None
    is_active: bool | None = None
    display_order: int | None = Field(default=None, ge=0)


class PayslipFieldReorderItem(BaseModel):
    id: int
    display_order: int = Field(ge=0)


class PayslipFieldReorderRequest(BaseModel):
    fields: list[PayslipFieldReorderItem] = Field(min_length=1)


class PayslipFieldResponse(BaseModel):
    id: int
    name: str
    field_key: str
    field_type: str
    category: str
    is_active: bool
    display_order: int
    is_system: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
