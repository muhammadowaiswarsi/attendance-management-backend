from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.department import get_current_admin
from app.core.config import resolve_storage_path
from app.database.db import get_db
from app.models.user import User
from app.schemas.payslip import PayslipCreate, PayslipResponse
from app.services import payslip_service

router = APIRouter(prefix="/payslips", tags=["Payslips"])


def get_current_employee_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee access only",
        )
    return current_user


@router.post("/", response_model=PayslipResponse, status_code=status.HTTP_201_CREATED)
def create_payslip(
    payslip: PayslipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return payslip_service.create_payslip(db, payslip, current_user)


@router.post("/{payslip_id}/send-email", status_code=status.HTTP_200_OK)
def send_payslip_email(
    payslip_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return payslip_service.send_payslip(db, payslip_id)


@router.get("/", response_model=list[PayslipResponse])
def list_payslips(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return payslip_service.get_payslips(db)


@router.get("/my-payslips", response_model=list[PayslipResponse])
def my_payslips(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_employee_user),
):
    return payslip_service.get_payslips_for_user(db, current_user)


@router.get("/download/{payslip_id}")
def download_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payslip = payslip_service.get_payslip_by_id(db, payslip_id)

    if not payslip_service.can_user_access_payslip(payslip, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download this payslip",
        )

    pdf_path = payslip_service.ensure_payslip_pdf(db, payslip)
    full_path = resolve_storage_path(pdf_path)
    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found on disk",
        )

    return FileResponse(
        path=full_path,
        media_type="application/pdf",
        filename=full_path.name,
    )


@router.get("/{payslip_id}", response_model=PayslipResponse)
def get_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return payslip_service.get_payslip_by_id(db, payslip_id)


@router.delete("/{payslip_id}", status_code=status.HTTP_200_OK)
def delete_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    payslip_service.delete_payslip(db, payslip_id)
    return {"message": "Payslip deleted successfully."}
