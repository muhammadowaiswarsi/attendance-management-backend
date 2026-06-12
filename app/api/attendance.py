from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.department import get_current_admin
from app.database.db import get_db
from app.models.user import User
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
    BulkAttendanceCreate,
    MonthlyAttendanceSummary,
)
from app.schemas.dashboard import TodayAttendanceItem
from app.services import attendance_service, dashboard_service

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def get_current_employee_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee access only",
        )
    return current_user


@router.post("/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def mark_attendance(
    attendance: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return attendance_service.mark_attendance(db, attendance, current_user)


@router.post("/bulk", response_model=list[AttendanceResponse], status_code=status.HTTP_201_CREATED)
def bulk_mark_attendance(
    bulk_data: BulkAttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return attendance_service.bulk_mark_attendance(db, bulk_data, current_user)


@router.get("/my-attendance", response_model=list[AttendanceResponse])
def my_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_employee_user),
):
    return attendance_service.get_attendance_for_user(db, current_user)


@router.get("/today", response_model=list[TodayAttendanceItem])
def today_attendance(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return dashboard_service.get_today_attendance(db)


@router.get("/employee/{employee_id}", response_model=list[AttendanceResponse])
def get_employee_attendance(
    employee_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return attendance_service.get_attendance_by_employee(db, employee_id)


@router.get("/date/{attendance_date}", response_model=list[AttendanceResponse])
def get_date_attendance(
    attendance_date: date,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return attendance_service.get_attendance_by_date(db, attendance_date)


@router.get("/summary/{employee_id}", response_model=MonthlyAttendanceSummary)
def get_monthly_summary(
    employee_id: int,
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2000),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return attendance_service.get_monthly_summary(db, employee_id, month, year)


@router.put("/{attendance_id}", response_model=AttendanceResponse)
def update_attendance(
    attendance_id: int,
    update_data: AttendanceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return attendance_service.update_attendance(db, attendance_id, update_data)


@router.delete("/{attendance_id}", status_code=status.HTTP_200_OK)
def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    attendance_service.delete_attendance(db, attendance_id)
    return {"message": "Attendance record deleted successfully"}
