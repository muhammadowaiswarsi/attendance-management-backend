from datetime import date, datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.payslip import Payslip
from app.models.user import User
from app.schemas.dashboard import (
    AdminDashboardResponse,
    AdminDashboardStats,
    EmployeeAttendanceSummary,
    EmployeeDashboardResponse,
    EmployeePayslipPreview,
    EmployeeProfileSummary,
    EmployeeQuickInfo,
    PayslipSummary,
    RecentActivityItem,
    RecentAttendanceItem,
    TodayAttendanceItem,
)
from app.services import report_service
from app.utils.timezone import ensure_utc, format_pkt_datetime


def _today_attendance_items(db: Session, attendance_date: date) -> list[TodayAttendanceItem]:
    records = (
        db.query(Attendance)
        .options(joinedload(Attendance.employee).joinedload(Employee.department))
        .filter(Attendance.attendance_date == attendance_date)
        .order_by(Attendance.employee_id)
        .all()
    )

    return [
        TodayAttendanceItem(
            id=record.id,
            employee_name=record.employee_name,
            department=record.employee.department_name if record.employee else "",
            status=record.status,
        )
        for record in records
    ]


def _payslip_summary_for_month(db: Session, month: int, year: int) -> PayslipSummary:
    payslips = (
        db.query(Payslip)
        .filter(Payslip.month == month, Payslip.year == year)
        .all()
    )
    sent = sum(1 for payslip in payslips if payslip.sent_at is not None)
    total = len(payslips)
    return PayslipSummary(
        total_this_month=total,
        sent=sent,
        pending=total - sent,
    )


def _build_recent_activity(db: Session, limit: int = 8) -> list[RecentActivityItem]:
    activities: list[RecentActivityItem] = []

    attendance_rows = (
        db.query(Attendance)
        .options(joinedload(Attendance.employee))
        .order_by(Attendance.created_at.desc())
        .limit(limit)
        .all()
    )
    for record in attendance_rows:
        activities.append(
            RecentActivityItem(
                id=record.id,
                message=f"{record.employee_name} marked {record.status}",
                occurred_at=ensure_utc(record.created_at),
            )
        )

    payslip_rows = (
        db.query(Payslip)
        .options(joinedload(Payslip.employee))
        .order_by(Payslip.created_at.desc())
        .limit(limit)
        .all()
    )
    for payslip in payslip_rows:
        if payslip.sent_at:
            message = f"Payslip sent to {payslip.employee_name}"
            occurred_at = payslip.sent_at
        else:
            message = f"Payslip created for {payslip.employee_name}"
            occurred_at = payslip.created_at
        activities.append(
            RecentActivityItem(
                id=10_000 + payslip.id,
                message=message,
                occurred_at=ensure_utc(occurred_at),
            )
        )

    employee_rows = (
        db.query(Employee)
        .options(joinedload(Employee.user))
        .order_by(Employee.id.desc())
        .limit(limit)
        .all()
    )
    for employee in employee_rows:
        occurred_at = (
            ensure_utc(employee.user.created_at)
            if employee.user and employee.user.created_at
            else datetime.now(timezone.utc)
        )
        activities.append(
            RecentActivityItem(
                id=20_000 + employee.id,
                message=f"New employee added: {employee.full_name}",
                occurred_at=occurred_at,
            )
        )

    activities.sort(key=lambda item: item.occurred_at, reverse=True)
    return activities[:limit]


def get_today_attendance(db: Session) -> list[TodayAttendanceItem]:
    return _today_attendance_items(db, date.today())


def get_admin_dashboard(db: Session) -> AdminDashboardResponse:
    today = date.today()
    daily_report = report_service.get_daily_report(db, today)
    payslip_summary = _payslip_summary_for_month(db, today.month, today.year)

    total_employees = (
        db.query(func.count(Employee.id))
        .filter(Employee.is_active.is_(True))
        .scalar()
        or 0
    )

    stats = AdminDashboardStats(
        total_employees=total_employees,
        present_today=daily_report.total_present,
        absent_today=daily_report.total_absent,
        half_day_today=daily_report.total_half_days,
        pending_payslips=payslip_summary.pending,
    )

    return AdminDashboardResponse(
        stats=stats,
        today_attendance=_today_attendance_items(db, today),
        payslip_summary=payslip_summary,
        recent_activity=_build_recent_activity(db),
    )


def _format_last_login(last_login_at: datetime | None) -> str | None:
    return format_pkt_datetime(last_login_at)


def _year_leave_days(db: Session, employee_id: int, year: int) -> int:
    start = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    return (
        db.query(func.count(Attendance.id))
        .filter(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date >= start,
            Attendance.attendance_date < end,
            Attendance.status == "On Leave",
        )
        .scalar()
        or 0
    )


def get_employee_dashboard(db: Session, current_user: User) -> EmployeeDashboardResponse:
    employee = report_service.get_employee_for_user(db, current_user.id)
    today = date.today()

    monthly_report = report_service.get_monthly_report(db, employee.id, today.month, today.year)

    attendance_summary = EmployeeAttendanceSummary(
        total_days=monthly_report.total_days,
        present_days=monthly_report.present_days,
        absent_days=monthly_report.absent_days,
        half_days=monthly_report.half_days,
        attendance_percentage=monthly_report.attendance_percentage,
    )

    recent_records = (
        db.query(Attendance)
        .filter(Attendance.employee_id == employee.id)
        .order_by(Attendance.attendance_date.desc())
        .limit(6)
        .all()
    )
    recent_attendance = [
        RecentAttendanceItem(
            id=record.id,
            date=record.attendance_date,
            status=record.status,
        )
        for record in recent_records
    ]

    payslip_rows = (
        db.query(Payslip)
        .filter(Payslip.employee_id == employee.id)
        .order_by(Payslip.year.desc(), Payslip.month.desc())
        .limit(3)
        .all()
    )
    payslips = [
        EmployeePayslipPreview(
            id=payslip.id,
            month=payslip.month,
            year=payslip.year,
            net_salary=payslip.net_salary,
            status="Sent" if payslip.sent_at else "Pending",
        )
        for payslip in payslip_rows
    ]

    quick_info = EmployeeQuickInfo(
        total_leaves=_year_leave_days(db, employee.id, today.year),
        this_month_attendance=monthly_report.attendance_percentage,
        last_login=_format_last_login(current_user.last_login_at),
    )

    profile = EmployeeProfileSummary(
        full_name=employee.full_name,
        employee_code=employee.employee_code,
        department=employee.department_name,
        designation=employee.designation,
        is_active=employee.is_active,
    )

    return EmployeeDashboardResponse(
        profile=profile,
        attendance_summary=attendance_summary,
        recent_attendance=recent_attendance,
        payslips=payslips,
        quick_info=quick_info,
    )
