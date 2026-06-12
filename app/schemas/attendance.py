from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AttendanceStatus = Literal["Present", "Absent", "Half Day", "On Leave", "Holiday"]

VALID_STATUSES = {"Present", "Absent", "Half Day", "On Leave", "Holiday"}


class AttendanceCreate(BaseModel):
    employee_id: int
    attendance_date: date
    status: AttendanceStatus
    remarks: str | None = None


class BulkAttendanceRecord(BaseModel):
    employee_id: int
    status: AttendanceStatus
    remarks: str | None = None


class BulkAttendanceCreate(BaseModel):
    attendance_date: date
    records: list[BulkAttendanceRecord] = Field(min_length=1)


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus | None = None
    remarks: str | None = None


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    attendance_date: date
    status: str
    remarks: str | None
    marked_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MonthlyAttendanceSummary(BaseModel):
    employee_id: int
    employee_name: str
    present_days: int
    absent_days: int
    half_days: int
    leave_days: int
    holidays: int
    total_records: int
