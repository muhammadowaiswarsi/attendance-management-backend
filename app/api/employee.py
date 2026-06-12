from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.department import get_current_admin
from app.database.db import get_db
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from app.schemas.password_setup import MessageResponse
from app.services import employee_service

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return employee_service.create_employee(db, employee)


@router.get("/", response_model=list[EmployeeResponse])
def list_employees(
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return employee_service.get_employees(db, search=search)


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return employee_service.get_employee_by_id(db, employee_id)


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return employee_service.update_employee(db, employee_id, employee_data)


@router.patch("/{employee_id}/deactivate", response_model=EmployeeResponse)
def deactivate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return employee_service.deactivate_employee(db, employee_id)


@router.patch("/{employee_id}/activate", response_model=EmployeeResponse)
def activate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return employee_service.activate_employee(db, employee_id)


@router.post("/{employee_id}/resend-invitation", response_model=MessageResponse)
def resend_invitation(
    employee_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    employee_service.resend_employee_invitation(db, employee_id)
    return {"message": "Invitation email sent successfully."}


@router.delete("/{employee_id}", response_model=MessageResponse)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    employee_service.delete_employee(db, employee_id)
    return {"message": "Employee deleted successfully."}
