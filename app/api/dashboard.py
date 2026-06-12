from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.department import get_current_admin
from app.database.db import get_db
from app.models.user import User
from app.schemas.dashboard import AdminDashboardResponse, EmployeeDashboardResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/admin", response_model=AdminDashboardResponse)
def admin_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return dashboard_service.get_admin_dashboard(db)


@router.get("/employee", response_model=EmployeeDashboardResponse)
def employee_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee access only",
        )
    return dashboard_service.get_employee_dashboard(db, current_user)
