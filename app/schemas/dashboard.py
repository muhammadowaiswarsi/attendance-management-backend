from datetime import date, datetime

from pydantic import BaseModel


class AdminDashboardStats(BaseModel):
    total_employees: int
    present_today: int
    absent_today: int
    half_day_today: int
    pending_payslips: int


class TodayAttendanceItem(BaseModel):
    id: int
    employee_name: str
    department: str
    status: str


class PayslipSummary(BaseModel):
    total_this_month: int
    sent: int
    pending: int


class RecentActivityItem(BaseModel):
    id: int
    message: str
    occurred_at: datetime


class AdminDashboardResponse(BaseModel):
    stats: AdminDashboardStats
    today_attendance: list[TodayAttendanceItem]
    payslip_summary: PayslipSummary
    recent_activity: list[RecentActivityItem]


class EmployeeProfileSummary(BaseModel):
    full_name: str
    employee_code: str
    department: str
    designation: str | None
    is_active: bool


class EmployeeAttendanceSummary(BaseModel):
    total_days: int
    present_days: int
    absent_days: int
    half_days: int
    attendance_percentage: float


class RecentAttendanceItem(BaseModel):
    id: int
    date: date
    status: str


class EmployeePayslipPreview(BaseModel):
    id: int
    month: int
    year: int
    net_salary: float
    status: str


class EmployeeQuickInfo(BaseModel):
    total_leaves: int
    this_month_attendance: float
    last_login: str | None


class EmployeeDashboardResponse(BaseModel):
    profile: EmployeeProfileSummary
    attendance_summary: EmployeeAttendanceSummary
    recent_attendance: list[RecentAttendanceItem]
    payslips: list[EmployeePayslipPreview]
    quick_info: EmployeeQuickInfo
