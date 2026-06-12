from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class HolidayCreate(BaseModel):
    title: str = Field(min_length=1)
    holiday_date: date
    description: str | None = None


class HolidayUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    holiday_date: date | None = None
    description: str | None = None


class HolidayResponse(BaseModel):
    id: int
    title: str
    holiday_date: date
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
