from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database.db import get_db
from app.models.user import User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)
from app.services import department_service

router = APIRouter(prefix="/departments", tags=["Departments"])


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return department_service.create_department(db, department)


@router.get("/", response_model=list[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return department_service.get_departments(db)


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return department_service.get_department_by_id(db, department_id)


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return department_service.update_department(db, department_id, department_data)


@router.delete("/{department_id}", status_code=status.HTTP_200_OK)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    department_service.delete_department(db, department_id)
    return {"message": "Department deleted successfully"}
