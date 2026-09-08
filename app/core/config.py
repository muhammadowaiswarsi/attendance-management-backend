import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./attendance.db",
)

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


def _writable_base_dir() -> Path:
    custom_dir = os.getenv("WRITABLE_DIR")
    if custom_dir:
        return Path(custom_dir)

    # Vercel/Lambda only allow writes under /tmp
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return Path("/tmp")

    return BACKEND_DIR


WRITABLE_DIR = _writable_base_dir()
PAYSLIPS_DIR = WRITABLE_DIR / "payslips"
REPORTS_DIR = WRITABLE_DIR / "reports"


def resolve_storage_path(relative_path: str) -> Path:
    """Map stored relative paths to the active writable storage directory."""
    path = Path(relative_path)
    if path.parts and path.parts[0] == "payslips":
        return PAYSLIPS_DIR / path.name
    if path.parts and path.parts[0] == "reports":
        return REPORTS_DIR / path.name
    return WRITABLE_DIR / relative_path


EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

PRODUCTION_FRONTEND_URL = "https://attendance-management-frontend-five.vercel.app"
LOCAL_FRONTEND_URL = "http://localhost:5173"


def _is_deployed() -> bool:
    return bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


def _is_local_url(url: str) -> bool:
    lowered = url.lower()
    return "localhost" in lowered or "127.0.0.1" in lowered


def _frontend_url() -> str:
    configured = (os.getenv("FRONTEND_URL") or "").strip().rstrip("/")
    if _is_deployed():
        if configured and not _is_local_url(configured):
            return configured
        return PRODUCTION_FRONTEND_URL
    return configured or LOCAL_FRONTEND_URL


FRONTEND_URL = _frontend_url()
