from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.attendance import router as attendance_router
from app.api.auth import router as auth_router
from app.api.department import router as department_router
from app.api.employee import router as employee_router
from app.api.holiday import router as holiday_router
from app.api.payslip import router as payslip_router
from app.api.dashboard import router as dashboard_router
from app.api.reports import router as reports_router
from app.database.base import Base
from app.database.migrations import run_migrations
from app.database.db import engine
import app.models.attendance  # noqa: F401
import app.models.department  # noqa: F401
import app.models.employee  # noqa: F401
import app.models.holiday  # noqa: F401
import app.models.password_reset_token  # noqa: F401
import app.models.password_setup_token  # noqa: F401
import app.models.payslip  # noqa: F401
import app.models.user  # noqa: F401

app = FastAPI(title="Attendance System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
run_migrations()

app.include_router(auth_router)
app.include_router(department_router)
app.include_router(employee_router)
app.include_router(attendance_router)
app.include_router(holiday_router)
app.include_router(payslip_router)
app.include_router(reports_router)
app.include_router(dashboard_router)


@app.get("/")
def home():
    return {"message": "Attendance System Running"}
