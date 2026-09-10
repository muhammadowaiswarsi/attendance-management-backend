from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.department import get_current_admin
from app.database.db import get_db
from app.models.user import User
from app.schemas.payslip_field import (
    PayslipFieldCreate,
    PayslipFieldReorderRequest,
    PayslipFieldResponse,
    PayslipFieldUpdate,
)
from app.services import payslip_field_service

router = APIRouter(prefix="/payslip-fields", tags=["Payslip Fields"])


@router.get("/", response_model=list[PayslipFieldResponse])
def list_payslip_fields(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return payslip_field_service.get_payslip_fields(db)


@router.get("/active", response_model=list[PayslipFieldResponse])
def list_active_payslip_fields(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return payslip_field_service.get_active_payslip_fields(db)


@router.post("/", response_model=PayslipFieldResponse, status_code=status.HTTP_201_CREATED)
def create_payslip_field(
    payload: PayslipFieldCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return payslip_field_service.create_payslip_field(db, payload)


@router.put("/reorder", response_model=list[PayslipFieldResponse])
def reorder_payslip_fields(
    payload: PayslipFieldReorderRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    items = [(item.id, item.display_order) for item in payload.fields]
    return payslip_field_service.reorder_payslip_fields(db, items)


@router.put("/{field_id}", response_model=PayslipFieldResponse)
def update_payslip_field(
    field_id: int,
    payload: PayslipFieldUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return payslip_field_service.update_payslip_field(db, field_id, payload)


@router.delete("/{field_id}", status_code=status.HTTP_200_OK)
def delete_payslip_field(
    field_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    payslip_field_service.delete_payslip_field(db, field_id)
    return {"message": "Payslip field deleted successfully."}
