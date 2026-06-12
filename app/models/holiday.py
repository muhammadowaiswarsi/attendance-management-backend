from sqlalchemy import Column, Date, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database.base import Base


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    holiday_date = Column(Date, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
