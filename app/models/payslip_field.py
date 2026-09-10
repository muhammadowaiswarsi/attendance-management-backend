from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class PayslipField(Base):
    __tablename__ = "payslip_fields"
    __table_args__ = (
        UniqueConstraint("field_key", name="uq_payslip_fields_field_key"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    field_key = Column(String, nullable=False, index=True)
    field_type = Column(String, nullable=False, default="amount")
    category = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=0)
    is_system = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
