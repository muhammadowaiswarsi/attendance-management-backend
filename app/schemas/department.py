from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
