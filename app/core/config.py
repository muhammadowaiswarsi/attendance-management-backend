import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PAYSLIPS_DIR = BACKEND_DIR / "payslips"

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
