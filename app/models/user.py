from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    role = Column(String, default="employee", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    employee = relationship("Employee", back_populates="user", uselist=False)
    password_setup_tokens = relationship(
        "PasswordSetupToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    marked_attendance = relationship("Attendance", back_populates="marker")
    created_payslips = relationship("Payslip", back_populates="creator")
