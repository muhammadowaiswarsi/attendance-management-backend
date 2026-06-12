from datetime import date

from pydantic import BaseModel


class MonthlyReportResponse(BaseModel):
    employee_name: str
    total_days: int
    present_days: int
    absent_days: int
    half_days: int
    leave_days: int
    attendance_percentage: float


class DepartmentReportResponse(BaseModel):
    department_name: str
    total_employees: int
    average_attendance_percentage: float
    best_performing_employee: str | None


class CompanySummaryResponse(BaseModel):
    total_employees: int
    total_present: int
    total_absent: int
    total_half_days: int
    total_leaves: int
    overall_attendance_percentage: float


class EmployeeDailyStatus(BaseModel):
    employee_id: int
    employee_name: str
    status: str


class DailyReportResponse(BaseModel):
    total_present: int
    total_absent: int
    total_half_days: int
    list_of_employees_status: list[EmployeeDailyStatus]


class ExportResponse(BaseModel):
    message: str
    file_path: str
