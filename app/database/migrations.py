from sqlalchemy import inspect, text

from app.database.base import Base
from app.database.db import engine


def run_migrations() -> None:
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return

    columns = {column["name"]: column for column in inspector.get_columns("users")}
    password_column = columns.get("hashed_password")
    if password_column and password_column.get("nullable") is False:
        _migrate_users_nullable_password()
        columns = {column["name"]: column for column in inspect(engine).get_columns("users")}

    _add_user_profile_columns(columns)


def _add_user_profile_columns(columns: dict) -> None:
    additions = {
        "phone_number": "VARCHAR",
        "address": "VARCHAR",
        "last_login_at": "DATETIME",
    }

    with engine.begin() as conn:
        for column_name, column_type in additions.items():
            if column_name not in columns:
                conn.execute(
                    text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                )


def _migrate_users_nullable_password() -> None:
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))

        conn.execute(
            text(
                """
                CREATE TABLE users_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    full_name VARCHAR NOT NULL,
                    email VARCHAR NOT NULL UNIQUE,
                    hashed_password VARCHAR,
                    role VARCHAR NOT NULL DEFAULT 'employee',
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO users_new (id, full_name, email, hashed_password, role, is_active, created_at)
                SELECT id, full_name, email, hashed_password, role, is_active, created_at
                FROM users
                """
            )
        )
        conn.execute(text("DROP TABLE users"))
        conn.execute(text("ALTER TABLE users_new RENAME TO users"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id)"))

        conn.execute(text("PRAGMA foreign_keys=ON"))
