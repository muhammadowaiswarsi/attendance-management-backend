from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.schemas.report import (
    CompanySummaryResponse,
    DailyReportResponse,
    DepartmentReportResponse,
    EmployeeDailyStatus,
    MonthlyReportResponse,
)
from app.services import department_service, employee_service
from app.utils.csv_exporter import export_attendance_csv

STATUS_PRESENT = "Present"
STATUS_ABSENT = "Absent"
STATUS_HALF = "Half Day"
STATUS_LEAVE = "On Leave"
STATUS_HOLIDAY = "Holiday"


def _month_range(month: int, year: int) -> tuple[date, date]:
    start_date = date(year, month, 1)
    end_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start_date, end_date


def _calc_attendance_percentage(present: int, half: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round((present + 0.5 * half) / total * 100, 2)


def _status_counts(db: Session, start: date, end: date, employee_id: int | None = None) -> dict[str, int]:
    query = db.query(Attendance.status, func.count(Attendance.id)).filter(
        Attendance.attendance_date >= start,
        Attendance.attendance_date < end,
    )
    if employee_id is not None:
        query = query.filter(Attendance.employee_id == employee_id)

    rows = query.group_by(Attendance.status).all()
    return {status: count for status, count in rows}


def _counts_to_stats(counts: dict[str, int]) -> dict[str, int]:
    present = counts.get(STATUS_PRESENT, 0)
    absent = counts.get(STATUS_ABSENT, 0)
    half = counts.get(STATUS_HALF, 0)
    leave = counts.get(STATUS_LEAVE, 0)
    holiday = counts.get(STATUS_HOLIDAY, 0)
    total = present + absent + half + leave + holiday
    return {
        "present_days": present,
        "absent_days": absent,
        "half_days": half,
        "leave_days": leave,
        "holiday_days": holiday,
        "total_days": total,
    }


def get_monthly_report(
    db: Session,
    employee_id: int,
    month: int,
    year: int,
) -> MonthlyReportResponse:
    employee = employee_service.get_employee_by_id(db, employee_id)
    start, end = _month_range(month, year)
    counts = _status_counts(db, start, end, employee_id=employee_id)
    stats = _counts_to_stats(counts)

    return MonthlyReportResponse(
        employee_name=employee.full_name,
        total_days=stats["total_days"],
        present_days=stats["present_days"],
        absent_days=stats["absent_days"],
        half_days=stats["half_days"],
        leave_days=stats["leave_days"],
        attendance_percentage=_calc_attendance_percentage(
            stats["present_days"], stats["half_days"], stats["total_days"]
        ),
    )


def get_department_report(
    db: Session,
    department_id: int,
    month: int,
    year: int,
) -> DepartmentReportResponse:
    department = department_service.get_department_by_id(db, department_id)
    employees = (
        db.query(Employee)
        .filter(Employee.department_id == department_id, Employee.is_active.is_(True))
        .all()
    )

    if not employees:
        return DepartmentReportResponse(
            department_name=department.name,
            total_employees=0,
            average_attendance_percentage=0.0,
            best_performing_employee=None,
        )

    start, end = _month_range(month, year)
    percentages: list[tuple[str, float]] = []

    for employee in employees:
        counts = _status_counts(db, start, end, employee_id=employee.id)
        stats = _counts_to_stats(counts)
        percentage = _calc_attendance_percentage(
            stats["present_days"], stats["half_days"], stats["total_days"]
        )
        percentages.append((employee.full_name, percentage))

    avg_percentage = round(sum(p[1] for p in percentages) / len(percentages), 2)
    best_employee = max(percentages, key=lambda item: item[1])[0]

    return DepartmentReportResponse(
        department_name=department.name,
        total_employees=len(employees),
        average_attendance_percentage=avg_percentage,
        best_performing_employee=best_employee,
    )


def get_company_summary(db: Session, month: int, year: int) -> CompanySummaryResponse:
    start, end = _month_range(month, year)
    counts = _status_counts(db, start, end)
    stats = _counts_to_stats(counts)

    total_employees = (
        db.query(func.count(Employee.id))
        .filter(Employee.is_active.is_(True))
        .scalar()
        or 0
    )

    return CompanySummaryResponse(
        total_employees=total_employees,
        total_present=stats["present_days"],
        total_absent=stats["absent_days"],
        total_half_days=stats["half_days"],
        total_leaves=stats["leave_days"],
        overall_attendance_percentage=_calc_attendance_percentage(
            stats["present_days"], stats["half_days"], stats["total_days"]
        ),
    )


def get_daily_report(db: Session, report_date: date) -> DailyReportResponse:
    records = (
        db.query(Attendance)
        .options(joinedload(Attendance.employee))
        .filter(Attendance.attendance_date == report_date)
        .order_by(Attendance.employee_id)
        .all()
    )

    total_present = sum(1 for r in records if r.status == STATUS_PRESENT)
    total_absent = sum(1 for r in records if r.status == STATUS_ABSENT)
    total_half = sum(1 for r in records if r.status == STATUS_HALF)

    employee_statuses = [
        EmployeeDailyStatus(
            employee_id=record.employee_id,
            employee_name=record.employee.full_name if record.employee else "",
            status=record.status,
        )
        for record in records
    ]

    return DailyReportResponse(
        total_present=total_present,
        total_absent=total_absent,
        total_half_days=total_half,
        list_of_employees_status=employee_statuses,
    )


def export_monthly_report_csv(db: Session, month: int, year: int) -> str:
    employees = (
        db.query(Employee)
        .options(joinedload(Employee.department))
        .filter(Employee.is_active.is_(True))
        .order_by(Employee.id)
        .all()
    )

    start, end = _month_range(month, year)
    rows: list[dict] = []

    for employee in employees:
        counts = _status_counts(db, start, end, employee_id=employee.id)
        stats = _counts_to_stats(counts)
        rows.append(
            {
                "employee_id": employee.id,
                "employee_name": employee.full_name,
                "department": employee.department_name,
                "present_days": stats["present_days"],
                "absent_days": stats["absent_days"],
                "half_days": stats["half_days"],
                "leave_days": stats["leave_days"],
                "holiday_days": stats["holiday_days"],
                "total_days": stats["total_days"],
                "attendance_percentage": _calc_attendance_percentage(
                    stats["present_days"], stats["half_days"], stats["total_days"]
                ),
            }
        )

    return export_attendance_csv(rows, month, year)


def get_employee_for_user(db: Session, user_id: int) -> Employee:
    employee = db.query(Employee).filter(Employee.user_id == user_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No employee profile linked to this account",
        )
    return employee
