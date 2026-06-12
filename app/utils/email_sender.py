import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.core.config import (
    EMAIL_HOST,
    EMAIL_PASSWORD,
    EMAIL_PORT,
    EMAIL_USERNAME,
    FRONTEND_URL,
)


class EmailSendError(Exception):
    pass


def send_payslip_email(
    recipient_email: str,
    employee_name: str,
    pdf_path: str,
    month: int,
    year: int,
) -> None:
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        raise EmailSendError(
            "Email credentials not configured. Set EMAIL_USERNAME and EMAIL_PASSWORD."
        )

    full_path = Path(pdf_path)
    if not full_path.is_absolute():
        from app.core.config import resolve_storage_path

        full_path = resolve_storage_path(pdf_path)

    if not full_path.exists():
        raise EmailSendError(f"PDF file not found: {pdf_path}")

    message = EmailMessage()
    message["Subject"] = f"Payslip for {month}/{year}"
    message["From"] = EMAIL_USERNAME
    message["To"] = recipient_email
    message.set_content(
        f"Dear {employee_name},\n\n"
        f"Please find attached your payslip for {month}/{year}.\n\n"
        f"Regards,\n"
        f"HR Department"
    )

    with open(full_path, "rb") as pdf_file:
        message.add_attachment(
            pdf_file.read(),
            maintype="application",
            subtype="pdf",
            filename=full_path.name,
        )

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(message)
    except smtplib.SMTPException as exc:
        raise EmailSendError(f"Failed to send email: {exc}") from exc


def send_invitation_email(
    recipient_email: str,
    employee_name: str,
    token: str,
) -> None:
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        raise EmailSendError(
            "Email credentials not configured. Set EMAIL_USERNAME and EMAIL_PASSWORD."
        )

    setup_url = f"{FRONTEND_URL.rstrip('/')}/set-password/{token}"

    message = EmailMessage()
    message["Subject"] = "Welcome to the Company – Set Your Password"
    message["From"] = EMAIL_USERNAME
    message["To"] = recipient_email
    message.set_content(
        f"Hello {employee_name},\n\n"
        f"Your employee account has been created.\n\n"
        f"Please click the link below to set your password:\n\n"
        f"{setup_url}\n\n"
        f"This link will expire in 24 hours.\n\n"
        f"Regards,\n"
        f"HR Department"
    )

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(message)
    except smtplib.SMTPException as exc:
        raise EmailSendError(f"Failed to send email: {exc}") from exc


def send_password_reset_email(
    recipient_email: str,
    full_name: str,
    token: str,
) -> None:
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        raise EmailSendError(
            "Email credentials not configured. Set EMAIL_USERNAME and EMAIL_PASSWORD."
        )

    reset_url = f"{FRONTEND_URL.rstrip('/')}/reset-password/{token}"

    message = EmailMessage()
    message["Subject"] = "Reset Your Password"
    message["From"] = EMAIL_USERNAME
    message["To"] = recipient_email
    message.set_content(
        f"Hello {full_name},\n\n"
        f"We received a request to reset your password.\n\n"
        f"Please click the link below to choose a new password:\n\n"
        f"{reset_url}\n\n"
        f"This link will expire in 1 hour.\n\n"
        f"If you did not request this, you can safely ignore this email.\n\n"
        f"Regards,\n"
        f"HR Department"
    )

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(message)
    except smtplib.SMTPException as exc:
        raise EmailSendError(f"Failed to send email: {exc}") from exc


def send_password_reset_email(
    recipient_email: str,
    full_name: str,
    token: str,
) -> None:
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        raise EmailSendError(
            "Email credentials not configured. Set EMAIL_USERNAME and EMAIL_PASSWORD."
        )

    reset_url = f"{FRONTEND_URL.rstrip('/')}/reset-password/{token}"

    message = EmailMessage()
    message["Subject"] = "Reset Your Password"
    message["From"] = EMAIL_USERNAME
    message["To"] = recipient_email
    message.set_content(
        f"Hello {full_name},\n\n"
        f"We received a request to reset your password.\n\n"
        f"Please click the link below to choose a new password:\n\n"
        f"{reset_url}\n\n"
        f"This link will expire in 1 hour.\n\n"
        f"If you did not request this, you can safely ignore this email.\n\n"
        f"Regards,\n"
        f"HR Department"
    )

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(message)
    except smtplib.SMTPException as exc:
        raise EmailSendError(f"Failed to send email: {exc}") from exc
