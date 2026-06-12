from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.password_reset_token import PasswordResetToken
from app.models.password_setup_token import PasswordSetupToken
from app.models.payslip import Payslip
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services import department_service, invitation_service
from app.services.user_service import get_user_by_email


def _employee_query(db: Session):
    return db.query(Employee).options(
        joinedload(Employee.department),
        joinedload(Employee.user),
    )


def get_employee_by_email(db: Session, email: str) -> Employee | None:
    return db.query(Employee).filter(Employee.email == email).first()


def generate_employee_code(db: Session) -> str:
    employees = db.query(Employee.employee_code).all()
    max_num = 0
    for (code,) in employees:
        if code and code.startswith("EMP-"):
            try:
                max_num = max(max_num, int(code.split("-")[1]))
            except ValueError:
                pass
    return f"EMP-{max_num + 1:04d}"


def create_employee(db: Session, employee_data: EmployeeCreate) -> Employee:
    department_service.get_department_by_id(db, employee_data.department_id)

    if get_user_by_email(db, employee_data.email) or get_employee_by_email(
        db, employee_data.email
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    db_user = User(
        full_name=employee_data.full_name,
        email=employee_data.email,
        hashed_password=None,
        role="employee",
        is_active=False,
    )
    db.add(db_user)
    db.flush()

    db_employee = Employee(
        employee_code=generate_employee_code(db),
        full_name=employee_data.full_name,
        email=employee_data.email,
        phone_number=employee_data.phone_number,
        designation=employee_data.designation,
        salary=employee_data.salary,
        joining_date=employee_data.joining_date,
        address=employee_data.address,
        department_id=employee_data.department_id,
        user_id=db_user.id,
        is_active=False,
    )
    db.add(db_employee)
    db.flush()

    invitation_service.send_employee_invitation(db, db_user, employee_data.full_name)
    db.commit()

    employee = _employee_query(db).filter(Employee.id == db_employee.id).first()
    return employee


def get_employees(db: Session, search: str | None = None) -> list[Employee]:
    query = _employee_query(db)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Employee.full_name.ilike(pattern),
                Employee.employee_code.ilike(pattern),
                Employee.email.ilike(pattern),
            )
        )

    return query.order_by(Employee.id).all()


def get_employee_by_id(db: Session, employee_id: int) -> Employee:
    employee = _employee_query(db).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )
    return employee


def update_employee(
    db: Session,
    employee_id: int,
    employee_data: EmployeeUpdate,
) -> Employee:
    employee = get_employee_by_id(db, employee_id)

    if employee_data.department_id is not None:
        department_service.get_department_by_id(db, employee_data.department_id)
        employee.department_id = employee_data.department_id

    if employee_data.full_name is not None:
        employee.full_name = employee_data.full_name
        employee.user.full_name = employee_data.full_name

    if employee_data.phone_number is not None:
        employee.phone_number = employee_data.phone_number

    if employee_data.designation is not None:
        employee.designation = employee_data.designation

    if employee_data.salary is not None:
        employee.salary = employee_data.salary

    if employee_data.address is not None:
        employee.address = employee_data.address

    db.commit()
    return get_employee_by_id(db, employee_id)


def deactivate_employee(db: Session, employee_id: int) -> Employee:
    employee = get_employee_by_id(db, employee_id)
    employee.is_active = False
    employee.user.is_active = False
    db.commit()
    return get_employee_by_id(db, employee_id)


def activate_employee(db: Session, employee_id: int) -> Employee:
    employee = get_employee_by_id(db, employee_id)
    if not employee.user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee must set a password before activation.",
        )
    employee.is_active = True
    employee.user.is_active = True
    db.commit()
    return get_employee_by_id(db, employee_id)


def resend_employee_invitation(db: Session, employee_id: int) -> None:
    employee = get_employee_by_id(db, employee_id)
    invitation_service.resend_employee_invitation(
        db,
        employee.user,
        employee.full_name,
    )


def delete_employee(db: Session, employee_id: int) -> None:
    employee = get_employee_by_id(db, employee_id)
    user_id = employee.user_id

    db.query(Attendance).filter(Attendance.employee_id == employee_id).delete(
        synchronize_session=False
    )
    db.query(Payslip).filter(Payslip.employee_id == employee_id).delete(
        synchronize_session=False
    )
    db.query(PasswordSetupToken).filter(PasswordSetupToken.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).delete(
        synchronize_session=False
    )

    db.delete(employee)
    db.flush()

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)

    db.commit()
