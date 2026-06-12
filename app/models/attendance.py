from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("employee_id", "attendance_date", name="uq_employee_attendance_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    attendance_date = Column(Date, nullable=False, index=True)
    status = Column(String, nullable=False)
    remarks = Column(String, nullable=True)
    marked_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    employee = relationship("Employee", back_populates="attendance_records")
    marker = relationship("User", back_populates="marked_attendance")

    @property
    def employee_name(self) -> str:
        return self.employee.full_name if self.employee else ""
