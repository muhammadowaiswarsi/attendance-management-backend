from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.employee import Employee
from app.models.user import User
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.utils.timezone import format_pkt_datetime


def _format_last_login(value: datetime | None) -> str | None:
    if not value:
        return "Never"
    return format_pkt_datetime(value)


def get_profile(db: Session, user: User) -> ProfileResponse:
    db_user = (
        db.query(User)
        .options(joinedload(User.employee).joinedload(Employee.department))
        .filter(User.id == user.id)
        .first()
    )
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    employee = db_user.employee

    return ProfileResponse(
        full_name=db_user.full_name,
        email=db_user.email,
        role=db_user.role,
        is_active=db_user.is_active,
        employee_code=employee.employee_code if employee else None,
        department_name=employee.department_name if employee else None,
        designation=employee.designation if employee else None,
        joining_date=employee.joining_date if employee else None,
        phone_number=employee.phone_number if employee else db_user.phone_number,
        address=employee.address if employee else db_user.address,
        last_login=_format_last_login(db_user.last_login_at),
    )


def update_profile(db: Session, user: User, data: ProfileUpdate) -> ProfileResponse:
    db_user = (
        db.query(User)
        .options(joinedload(User.employee))
        .filter(User.id == user.id)
        .first()
    )
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    phone = data.phone_number.strip() if data.phone_number else None
    address = data.address.strip() if data.address else None

    if db_user.employee:
        db_user.employee.phone_number = phone
        db_user.employee.address = address
    else:
        db_user.phone_number = phone
        db_user.address = address

    db.commit()
    return get_profile(db, db_user)


def record_login(db: Session, user: User) -> None:
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
