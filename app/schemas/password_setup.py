from pydantic import BaseModel, Field


class SetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)


class MessageResponse(BaseModel):
    message: str
