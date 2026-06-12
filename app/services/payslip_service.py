from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.employee import Employee
from app.models.payslip import Payslip
from app.models.user import User
from app.schemas.payslip import PayslipCreate
from app.services import employee_service
from app.utils.email_sender import EmailSendError, send_payslip_email
from app.utils.pdf_generator import generate_payslip_pdf
from app.core.config import BACKEND_DIR


def _payslip_query(db: Session):
    return db.query(Payslip).options(
        joinedload(Payslip.employee).joinedload(Employee.department)
    )


def _get_duplicate_payslip(
    db: Session,
    employee_id: int,
    month: int,
    year: int,
) -> Payslip | None:
    return (
        db.query(Payslip)
        .filter(
            Payslip.employee_id == employee_id,
            Payslip.month == month,
            Payslip.year == year,
        )
        .first()
    )


def create_payslip(
    db: Session,
    payslip_data: PayslipCreate,
    current_user: User,
) -> Payslip:
    employee = employee_service.get_employee_by_id(db, payslip_data.employee_id)

    if not employee.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee does not have an email address",
        )

    if _get_duplicate_payslip(
        db, payslip_data.employee_id, payslip_data.month, payslip_data.year
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payslip already exists for this employee, month and year",
        )

    net_salary = (
        payslip_data.basic_salary
        + payslip_data.allowances
        - payslip_data.deductions
    )

    db_payslip = Payslip(
        employee_id=payslip_data.employee_id,
        month=payslip_data.month,
        year=payslip_data.year,
        basic_salary=payslip_data.basic_salary,
        allowances=payslip_data.allowances,
        deductions=payslip_data.deductions,
        net_salary=net_salary,
        created_by=current_user.id,
    )
    db.add(db_payslip)
    db.flush()

    try:
        pdf_path = generate_payslip_pdf(db_payslip, employee)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {exc}",
        ) from exc

    db_payslip.pdf_path = pdf_path
    db.commit()

    return _payslip_query(db).filter(Payslip.id == db_payslip.id).first()


def ensure_payslip_pdf(db: Session, payslip: Payslip) -> str:
    employee = payslip.employee
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found for this payslip",
        )
    try:
        pdf_path = generate_payslip_pdf(payslip, employee)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {exc}",
        ) from exc
    payslip.pdf_path = pdf_path
    db.commit()
    db.refresh(payslip)
    return pdf_path


def send_payslip(db: Session, payslip_id: int) -> dict:
    payslip = get_payslip_by_id(db, payslip_id)
    employee = payslip.employee

    try:
        pdf_path = generate_payslip_pdf(payslip, employee)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {exc}",
        ) from exc

    payslip.pdf_path = pdf_path
    db.flush()

    from app.core.config import BACKEND_DIR

    full_path = BACKEND_DIR / payslip.pdf_path
    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found on disk",
        )

    try:
        send_payslip_email(
            recipient_email=employee.email,
            employee_name=employee.full_name,
            pdf_path=payslip.pdf_path,
            month=payslip.month,
            year=payslip.year,
        )
    except EmailSendError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    payslip.sent_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(payslip)

    return {"message": "Payslip emailed successfully."}


def get_payslips(db: Session) -> list[Payslip]:
    return _payslip_query(db).order_by(Payslip.year.desc(), Payslip.month.desc()).all()


def get_payslip_by_id(db: Session, payslip_id: int) -> Payslip:
    payslip = _payslip_query(db).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found",
        )
    return payslip


def get_employee_payslips(db: Session, employee_id: int) -> list[Payslip]:
    employee_service.get_employee_by_id(db, employee_id)
    return (
        _payslip_query(db)
        .filter(Payslip.employee_id == employee_id)
        .order_by(Payslip.year.desc(), Payslip.month.desc())
        .all()
    )


def get_payslips_for_user(db: Session, current_user: User) -> list[Payslip]:
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No employee profile linked to this account",
        )
    return get_employee_payslips(db, employee.id)


def can_user_access_payslip(payslip: Payslip, current_user: User) -> bool:
    if current_user.role == "admin":
        return True
    if current_user.role != "employee":
        return False
    employee = payslip.employee
    return employee is not None and employee.user_id == current_user.id


def _remove_payslip_pdf(pdf_path: str | None) -> None:
    if not pdf_path:
        return

    full_path = Path(pdf_path)
    if not full_path.is_absolute():
        full_path = BACKEND_DIR / pdf_path

    if full_path.exists() and full_path.is_file():
        full_path.unlink()


def delete_payslip(db: Session, payslip_id: int) -> None:
    payslip = get_payslip_by_id(db, payslip_id)
    pdf_path = payslip.pdf_path
    db.delete(payslip)
    db.commit()
    _remove_payslip_pdf(pdf_path)
