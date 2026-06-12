from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.models.holiday import Holiday
from app.schemas.holiday import HolidayCreate, HolidayUpdate


def get_holiday_by_date(db: Session, holiday_date: date) -> Holiday | None:
    return db.query(Holiday).filter(Holiday.holiday_date == holiday_date).first()


def create_holiday(db: Session, holiday_data: HolidayCreate) -> Holiday:
    if get_holiday_by_date(db, holiday_data.holiday_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Holiday already exists on this date",
        )

    db_holiday = Holiday(
        title=holiday_data.title,
        holiday_date=holiday_data.holiday_date,
        description=holiday_data.description,
    )
    db.add(db_holiday)
    db.commit()
    db.refresh(db_holiday)
    return db_holiday


def get_holidays(db: Session, year: int | None = None) -> list[Holiday]:
    query = db.query(Holiday)

    if year is not None:
        query = query.filter(extract("year", Holiday.holiday_date) == year)

    return query.order_by(Holiday.holiday_date).all()


def get_holiday_by_id(db: Session, holiday_id: int) -> Holiday:
    holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not holiday:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holiday not found",
        )
    return holiday


def update_holiday(
    db: Session,
    holiday_id: int,
    holiday_data: HolidayUpdate,
) -> Holiday:
    holiday = get_holiday_by_id(db, holiday_id)

    if holiday_data.holiday_date and holiday_data.holiday_date != holiday.holiday_date:
        if get_holiday_by_date(db, holiday_data.holiday_date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Holiday already exists on this date",
            )
        holiday.holiday_date = holiday_data.holiday_date

    if holiday_data.title is not None:
        holiday.title = holiday_data.title

    if holiday_data.description is not None:
        holiday.description = holiday_data.description

    db.commit()
    db.refresh(holiday)
    return holiday


def delete_holiday(db: Session, holiday_id: int) -> None:
    holiday = get_holiday_by_id(db, holiday_id)
    db.delete(holiday)
    db.commit()
