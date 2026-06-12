from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Payslip(Base):
    __tablename__ = "payslips"
    __table_args__ = (
        UniqueConstraint("employee_id", "month", "year", name="uq_employee_payslip_period"),
    )

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    basic_salary = Column(Float, nullable=False)
    allowances = Column(Float, default=0, nullable=False)
    deductions = Column(Float, default=0, nullable=False)
    net_salary = Column(Float, nullable=False)
    pdf_path = Column(String, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    employee = relationship("Employee", back_populates="payslips")
    creator = relationship("User", back_populates="created_payslips")

    @property
    def employee_name(self) -> str:
        return self.employee.full_name if self.employee else ""
