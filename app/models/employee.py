from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    salary = Column(Numeric(12, 2), nullable=False)
    joining_date = Column(Date, nullable=False)
    address = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    department = relationship("Department", back_populates="employees")
    user = relationship("User", back_populates="employee")
    attendance_records = relationship("Attendance", back_populates="employee")
    payslips = relationship("Payslip", back_populates="employee")

    @property
    def department_name(self) -> str:
        return self.department.name if self.department else ""

    @property
    def password_set(self) -> bool:
        return bool(self.user and self.user.hashed_password)
