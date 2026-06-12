from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.user import User
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceUpdate,
    BulkAttendanceCreate,
    MonthlyAttendanceSummary,
)
from app.services import employee_service

STATUS_COUNTS = {
    "Present": "present_days",
    "Absent": "absent_days",
    "Half Day": "half_days",
    "On Leave": "leave_days",
    "Holiday": "holidays",
}


def _attendance_query(db: Session):
    return db.query(Attendance).options(joinedload(Attendance.employee))


def _validate_active_employee(db: Session, employee_id: int) -> Employee:
    employee = employee_service.get_employee_by_id(db, employee_id)
    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee is inactive",
        )
    return employee


def _check_duplicate(db: Session, employee_id: int, attendance_date: date) -> None:
    existing = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date == attendance_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already exists for this employee on the given date",
        )


def mark_attendance(
    db: Session,
    attendance_data: AttendanceCreate,
    current_user: User,
) -> Attendance:
    _validate_active_employee(db, attendance_data.employee_id)
    _check_duplicate(db, attendance_data.employee_id, attendance_data.attendance_date)

    db_attendance = Attendance(
        employee_id=attendance_data.employee_id,
        attendance_date=attendance_data.attendance_date,
        status=attendance_data.status,
        remarks=attendance_data.remarks,
        marked_by=current_user.id,
    )
    db.add(db_attendance)
    db.commit()

    return _attendance_query(db).filter(Attendance.id == db_attendance.id).first()


def bulk_mark_attendance(
    db: Session,
    bulk_data: BulkAttendanceCreate,
    current_user: User,
) -> list[Attendance]:
    employee_ids = [record.employee_id for record in bulk_data.records]
    if len(employee_ids) != len(set(employee_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate employee entries in bulk request",
        )

    for record in bulk_data.records:
        _validate_active_employee(db, record.employee_id)
        _check_duplicate(db, record.employee_id, bulk_data.attendance_date)

    created_ids = []
    for record in bulk_data.records:
        db_attendance = Attendance(
            employee_id=record.employee_id,
            attendance_date=bulk_data.attendance_date,
            status=record.status,
            remarks=record.remarks,
            marked_by=current_user.id,
        )
        db.add(db_attendance)
        db.flush()
        created_ids.append(db_attendance.id)

    db.commit()

    return (
        _attendance_query(db)
        .filter(Attendance.id.in_(created_ids))
        .order_by(Attendance.id)
        .all()
    )


def get_attendance_by_employee(db: Session, employee_id: int) -> list[Attendance]:
    employee_service.get_employee_by_id(db, employee_id)
    return (
        _attendance_query(db)
        .filter(Attendance.employee_id == employee_id)
        .order_by(Attendance.attendance_date.desc())
        .all()
    )


def get_attendance_by_date(db: Session, attendance_date: date) -> list[Attendance]:
    return (
        _attendance_query(db)
        .filter(Attendance.attendance_date == attendance_date)
        .order_by(Attendance.employee_id)
        .all()
    )


def get_attendance_for_user(db: Session, current_user: User) -> list[Attendance]:
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No employee profile linked to this account",
        )
    return get_attendance_by_employee(db, employee.id)


def get_monthly_summary(
    db: Session,
    employee_id: int,
    month: int,
    year: int,
) -> MonthlyAttendanceSummary:
    employee = employee_service.get_employee_by_id(db, employee_id)

    start_date = date(year, month, 1)
    end_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    records = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date < end_date,
        )
        .all()
    )

    counts = {
        "present_days": 0,
        "absent_days": 0,
        "half_days": 0,
        "leave_days": 0,
        "holidays": 0,
    }
    for record in records:
        field = STATUS_COUNTS.get(record.status)
        if field:
            counts[field] += 1

    return MonthlyAttendanceSummary(
        employee_id=employee.id,
        employee_name=employee.full_name,
        present_days=counts["present_days"],
        absent_days=counts["absent_days"],
        half_days=counts["half_days"],
        leave_days=counts["leave_days"],
        holidays=counts["holidays"],
        total_records=len(records),
    )


def get_attendance_by_id(db: Session, attendance_id: int) -> Attendance:
    attendance = _attendance_query(db).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found",
        )
    return attendance


def update_attendance(
    db: Session,
    attendance_id: int,
    update_data: AttendanceUpdate,
) -> Attendance:
    attendance = get_attendance_by_id(db, attendance_id)

    if update_data.status is not None:
        attendance.status = update_data.status

    if update_data.remarks is not None:
        attendance.remarks = update_data.remarks

    db.commit()
    return get_attendance_by_id(db, attendance_id)


def delete_attendance(db: Session, attendance_id: int) -> None:
    attendance = get_attendance_by_id(db, attendance_id)
    db.delete(attendance)
    db.commit()
