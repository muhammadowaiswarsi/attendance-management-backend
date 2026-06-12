from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.department import get_current_admin
from app.database.db import get_db
from app.models.user import User
from app.schemas.holiday import HolidayCreate, HolidayResponse, HolidayUpdate
from app.services import holiday_service

router = APIRouter(prefix="/holidays", tags=["Holidays"])


@router.post("/", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
def create_holiday(
    holiday: HolidayCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return holiday_service.create_holiday(db, holiday)


@router.get("/", response_model=list[HolidayResponse])
def list_holidays(
    year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return holiday_service.get_holidays(db, year=year)


@router.get("/{holiday_id}", response_model=HolidayResponse)
def get_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return holiday_service.get_holiday_by_id(db, holiday_id)


@router.put("/{holiday_id}", response_model=HolidayResponse)
def update_holiday(
    holiday_id: int,
    holiday_data: HolidayUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return holiday_service.update_holiday(db, holiday_id, holiday_data)


@router.delete("/{holiday_id}", status_code=status.HTTP_200_OK)
def delete_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    holiday_service.delete_holiday(db, holiday_id)
    return {"message": "Holiday deleted successfully"}
