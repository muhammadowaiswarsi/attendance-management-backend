import csv
from pathlib import Path

from app.core.config import REPORTS_DIR


def export_attendance_csv(data: list[dict], month: int, year: int) -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"report_{year}_{month:02d}.csv"
    file_path = REPORTS_DIR / filename
    relative_path = f"reports/{filename}"

    if not data:
        fieldnames = [
            "employee_id",
            "employee_name",
            "department",
            "present_days",
            "absent_days",
            "half_days",
            "leave_days",
            "holiday_days",
            "total_days",
            "attendance_percentage",
        ]
        with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
    else:
        fieldnames = list(data[0].keys())
        with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    return relative_path
