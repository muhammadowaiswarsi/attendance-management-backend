from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate


def get_department_by_name(db: Session, name: str) -> Department | None:
    return db.query(Department).filter(Department.name == name).first()


def create_department(db: Session, department: DepartmentCreate) -> Department:
    if get_department_by_name(db, department.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department name already exists",
        )

    db_department = Department(
        name=department.name,
        description=department.description,
    )
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department


def get_departments(db: Session) -> list[Department]:
    return db.query(Department).order_by(Department.id).all()


def get_department_by_id(db: Session, department_id: int) -> Department:
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )
    return department


def update_department(
    db: Session,
    department_id: int,
    department_data: DepartmentUpdate,
) -> Department:
    department = get_department_by_id(db, department_id)

    if department_data.name and department_data.name != department.name:
        if get_department_by_name(db, department_data.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department name already exists",
            )
        department.name = department_data.name

    if department_data.description is not None:
        department.description = department_data.description

    db.commit()
    db.refresh(department)
    return department


def delete_department(db: Session, department_id: int) -> None:
    department = get_department_by_id(db, department_id)
    db.delete(department)
    db.commit()
