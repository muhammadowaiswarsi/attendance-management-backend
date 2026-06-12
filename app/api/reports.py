from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.department import get_current_admin
from app.core.config import BACKEND_DIR
from app.database.db import get_db
from app.models.user import User
from app.schemas.report import (
    CompanySummaryResponse,
    DailyReportResponse,
    DepartmentReportResponse,
    MonthlyReportResponse,
)
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/monthly", response_model=MonthlyReportResponse)
def monthly_report(
    employee_id: int = Query(...),
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return report_service.get_monthly_report(db, employee_id, month, year)

    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report",
        )

    employee = report_service.get_employee_for_user(db, current_user.id)
    if employee.id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own monthly report",
        )

    return report_service.get_monthly_report(db, employee_id, month, year)


@router.get("/department", response_model=DepartmentReportResponse)
def department_report(
    department_id: int = Query(...),
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2000),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return report_service.get_department_report(db, department_id, month, year)


@router.get("/company", response_model=CompanySummaryResponse)
def company_summary(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2000),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return report_service.get_company_summary(db, month, year)


@router.get("/daily", response_model=DailyReportResponse)
def daily_report(
    date: date = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return report_service.get_daily_report(db, date)


@router.get("/export/monthly")
def export_monthly_report(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2000),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    relative_path = report_service.export_monthly_report_csv(db, month, year)
    full_path = BACKEND_DIR / relative_path

    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file could not be generated",
        )

    return FileResponse(
        path=full_path,
        media_type="text/csv",
        filename=full_path.name,
    )
