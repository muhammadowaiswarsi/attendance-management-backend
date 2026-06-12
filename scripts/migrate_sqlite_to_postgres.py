"""
One-time migration: copy data from SQLite backup into PostgreSQL.

Usage:
  python scripts/migrate_sqlite_to_postgres.py [path/to/source.db]
"""

import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import DATABASE_URL  # noqa: E402

DEFAULT_SOURCE = BACKEND_DIR / "attendance_backup.db"

TABLE_ORDER = [
    "departments",
    "users",
    "employees",
    "holidays",
    "attendance",
    "payslips",
    "password_setup_tokens",
    "password_reset_tokens",
]


def _normalize_row(row: dict, pg_columns: dict) -> dict:
    normalized = dict(row)
    for col, info in pg_columns.items():
        if col not in normalized or normalized[col] is None:
            continue
        col_type = str(info["type"]).upper()
        if "BOOL" in col_type and isinstance(normalized[col], int):
            normalized[col] = bool(normalized[col])
    return normalized


def migrate(source_path: Path) -> None:
    if not source_path.exists():
        raise FileNotFoundError(f"SQLite file not found: {source_path}")

    if not DATABASE_URL.startswith("postgresql"):
        raise RuntimeError("DATABASE_URL must point to PostgreSQL for this migration.")

    sqlite_engine = create_engine(f"sqlite:///{source_path}")
    postgres_engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    with postgres_engine.connect() as conn:
        existing = conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        if existing:
            print(f"PostgreSQL already has {existing} user(s). Aborting to avoid duplicates.")
            return

    pg_inspector = inspect(postgres_engine)

    for table in TABLE_ORDER:
        inspector = inspect(sqlite_engine)
        if table not in inspector.get_table_names():
            print(f"Skip {table} (not in source)")
            continue

        with sqlite_engine.connect() as src, postgres_engine.begin() as dst:
            existing_rows = dst.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0
            if existing_rows:
                print(f"Skip {table} ({existing_rows} row(s) already in PostgreSQL)")
                continue

            rows = src.execute(text(f"SELECT * FROM {table}")).mappings().all()
            if not rows:
                print(f"Skip {table} (empty)")
                continue

            columns = list(rows[0].keys())
            col_list = ", ".join(columns)
            placeholders = ", ".join(f":{col}" for col in columns)
            insert_sql = text(
                f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
            )
            pg_columns = {col["name"]: col for col in pg_inspector.get_columns(table)}

            for row in rows:
                dst.execute(insert_sql, _normalize_row(dict(row), pg_columns))

            # Reset serial sequences for PostgreSQL auto-increment ids
            pk = inspector.get_pk_constraint(table)
            if pk and pk.get("constrained_columns") == ["id"]:
                dst.execute(
                    text(
                        f"""
                        SELECT setval(
                            pg_get_serial_sequence('{table}', 'id'),
                            COALESCE((SELECT MAX(id) FROM {table}), 1),
                            true
                        )
                        """
                    )
                )

            print(f"Migrated {len(rows)} row(s) -> {table}")

    print("Migration complete.")


if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    migrate(source)
