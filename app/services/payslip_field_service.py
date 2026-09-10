import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.payslip_field import PayslipField
from app.schemas.payslip_field import PayslipFieldCreate, PayslipFieldUpdate

SYSTEM_FIELD_KEYS = ("basic_salary", "allowances", "deductions")
REQUIRED_SYSTEM_KEYS = ("basic_salary",)
FIELD_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

DEFAULT_PAYSLIP_FIELDS = [
    {
        "name": "Basic Salary",
        "field_key": "basic_salary",
        "field_type": "amount",
        "category": "earning",
        "is_active": True,
        "display_order": 1,
        "is_system": True,
    },
    {
        "name": "Allowances",
        "field_key": "allowances",
        "field_type": "amount",
        "category": "earning",
        "is_active": True,
        "display_order": 2,
        "is_system": True,
    },
    {
        "name": "Deductions",
        "field_key": "deductions",
        "field_type": "amount",
        "category": "deduction",
        "is_active": True,
        "display_order": 3,
        "is_system": True,
    },
    {
        "name": "Tax",
        "field_key": "tax",
        "field_type": "amount",
        "category": "deduction",
        "is_active": True,
        "display_order": 4,
        "is_system": False,
    },
]


def slugify_field_key(name: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    key = re.sub(r"_+", "_", key)
    return key


def _validate_field_key(field_key: str) -> str:
    key = field_key.strip().lower()
    if not FIELD_KEY_PATTERN.match(key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field key must start with a letter and contain only lowercase letters, numbers, and underscores",
        )
    return key


def get_payslip_fields(db: Session) -> list[PayslipField]:
    return (
        db.query(PayslipField)
        .order_by(PayslipField.display_order.asc(), PayslipField.id.asc())
        .all()
    )


def get_active_payslip_fields(db: Session) -> list[PayslipField]:
    return (
        db.query(PayslipField)
        .filter(PayslipField.is_active.is_(True))
        .order_by(PayslipField.display_order.asc(), PayslipField.id.asc())
        .all()
    )


def get_payslip_field_by_id(db: Session, field_id: int) -> PayslipField:
    field = db.query(PayslipField).filter(PayslipField.id == field_id).first()
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip field not found",
        )
    return field


def get_payslip_field_by_key(db: Session, field_key: str) -> PayslipField | None:
    return db.query(PayslipField).filter(PayslipField.field_key == field_key).first()


def _next_display_order(db: Session) -> int:
    current = (
        db.query(PayslipField.display_order)
        .order_by(PayslipField.display_order.desc())
        .first()
    )
    return (current[0] + 1) if current else 1


def create_payslip_field(db: Session, data: PayslipFieldCreate) -> PayslipField:
    name = data.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field name is required",
        )

    field_key = _validate_field_key(data.field_key or slugify_field_key(name))
    if not field_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not generate a valid field key from the name",
        )

    if get_payslip_field_by_key(db, field_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A payslip field with this key already exists",
        )

    field = PayslipField(
        name=name,
        field_key=field_key,
        field_type=data.field_type,
        category=data.category,
        is_active=data.is_active,
        display_order=_next_display_order(db),
        is_system=False,
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


def update_payslip_field(
    db: Session,
    field_id: int,
    data: PayslipFieldUpdate,
) -> PayslipField:
    field = get_payslip_field_by_id(db, field_id)

    if data.name is not None:
        name = data.name.strip()
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Field name is required",
            )
        field.name = name

    if data.category is not None and not field.is_system:
        field.category = data.category

    if data.is_active is not None:
        if field.field_key in REQUIRED_SYSTEM_KEYS and not data.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Basic Salary cannot be disabled",
            )
        field.is_active = data.is_active

    if data.display_order is not None:
        field.display_order = data.display_order

    db.commit()
    db.refresh(field)
    return field


def reorder_payslip_fields(
    db: Session,
    items: list[tuple[int, int]],
) -> list[PayslipField]:
    fields = get_payslip_fields(db)
    by_id = {field.id: field for field in fields}

    if {field_id for field_id, _ in items} != set(by_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reorder payload must include every payslip field exactly once",
        )

    for field_id, display_order in items:
        by_id[field_id].display_order = display_order

    db.commit()
    return get_payslip_fields(db)


def delete_payslip_field(db: Session, field_id: int) -> None:
    field = get_payslip_field_by_id(db, field_id)
    if field.is_system or field.field_key in SYSTEM_FIELD_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System payslip fields cannot be deleted",
        )
    db.delete(field)
    db.commit()


def seed_default_payslip_fields(db: Session) -> None:
    if db.query(PayslipField).first():
        return
    for item in DEFAULT_PAYSLIP_FIELDS:
        db.add(PayslipField(**item))
    db.commit()


def build_field_value_snapshots(
    db: Session,
    submitted_values: list,
    basic_salary: float,
    allowances: float,
    deductions: float,
) -> list[dict]:
    active_fields = get_active_payslip_fields(db)
    if not active_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active payslip fields are configured",
        )

    active_by_key = {field.field_key: field for field in active_fields}
    submitted: dict[str, float] = {}

    for item in submitted_values or []:
        key = item.field_key.strip().lower()
        if key in submitted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate payslip field '{key}'",
            )
        field = active_by_key.get(key) or get_payslip_field_by_key(db, key)
        if field is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown payslip field '{key}'",
            )
        if not field.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payslip field '{field.name}' is not active",
            )
        if item.value < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field.name} cannot be negative",
            )
        submitted[key] = float(item.value)

    if "basic_salary" in active_by_key and "basic_salary" not in submitted:
        submitted["basic_salary"] = float(basic_salary)
    if "allowances" in active_by_key and "allowances" not in submitted:
        submitted["allowances"] = float(allowances)
    if "deductions" in active_by_key and "deductions" not in submitted:
        submitted["deductions"] = float(deductions)

    snapshots = []
    for field in active_fields:
        value = float(submitted.get(field.field_key, 0))
        if field.field_key == "basic_salary" and value <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Basic salary must be greater than 0",
            )
        snapshots.append(
            {
                "field_id": field.id,
                "field_key": field.field_key,
                "name": field.name,
                "field_type": field.field_type,
                "category": field.category,
                "value": value,
            }
        )
    return snapshots


def calculate_net_salary(snapshots: list[dict]) -> float:
    earnings = 0.0
    deductions_total = 0.0
    for item in snapshots:
        value = float(item.get("value") or 0)
        if item.get("category") == "deduction":
            deductions_total += value
        else:
            earnings += value
    return earnings - deductions_total


def snapshot_column_values(snapshots: list[dict]) -> tuple[float, float, float]:
    values = {item["field_key"]: float(item.get("value") or 0) for item in snapshots}
    return (
        values.get("basic_salary", 0.0),
        values.get("allowances", 0.0),
        values.get("deductions", 0.0),
    )


def split_line_items(snapshots: list[dict] | None) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    earnings: list[tuple[str, float]] = []
    deductions: list[tuple[str, float]] = []
    for item in snapshots or []:
        name = item.get("name") or item.get("field_key") or "Field"
        value = float(item.get("value") or 0)
        if item.get("category") == "deduction":
            deductions.append((name, value))
        else:
            earnings.append((name, value))
    return earnings, deductions
