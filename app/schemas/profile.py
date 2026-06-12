from datetime import date

from pydantic import BaseModel, EmailStr, Field


class ProfileResponse(BaseModel):
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    employee_code: str | None = None
    department_name: str | None = None
    designation: str | None = None
    joining_date: date | None = None
    phone_number: str | None = None
    address: str | None = None
    last_login: str | None = None


class ProfileUpdate(BaseModel):
    phone_number: str | None = None
    address: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)
