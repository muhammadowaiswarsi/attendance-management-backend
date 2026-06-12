import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password
from app.models.password_setup_token import PasswordSetupToken
from app.models.user import User
from app.utils.email_sender import EmailSendError, send_invitation_email

TOKEN_EXPIRY_HOURS = 24
INVALID_TOKEN_MESSAGE = "Invalid or expired token."


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_expiry(expires_at: datetime) -> datetime:
    if expires_at.tzinfo is None:
        return expires_at.replace(tzinfo=timezone.utc)
    return expires_at.astimezone(timezone.utc)


def invalidate_unused_tokens(db: Session, user_id: int) -> None:
    db.query(PasswordSetupToken).filter(
        PasswordSetupToken.user_id == user_id,
        PasswordSetupToken.used.is_(False),
    ).update({PasswordSetupToken.used: True}, synchronize_session=False)


def create_password_setup_token(db: Session, user_id: int) -> PasswordSetupToken:
    invalidate_unused_tokens(db, user_id)

    token = PasswordSetupToken(
        user_id=user_id,
        token=secrets.token_urlsafe(32),
        expires_at=_utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        used=False,
    )
    db.add(token)
    db.flush()
    return token


def get_valid_token(db: Session, token_value: str) -> PasswordSetupToken | None:
    token = (
        db.query(PasswordSetupToken)
        .filter(PasswordSetupToken.token == token_value)
        .first()
    )
    if not token or token.used:
        return None
    if _normalize_expiry(token.expires_at) <= _utcnow():
        return None
    return token


def send_employee_invitation(db: Session, user: User, employee_name: str) -> None:
    token = create_password_setup_token(db, user.id)
    try:
        send_invitation_email(
            recipient_email=user.email,
            employee_name=employee_name,
            token=token.token,
        )
    except EmailSendError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


def resend_employee_invitation(db: Session, user: User, employee_name: str) -> None:
    if user.is_active and user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee has already set a password.",
        )

    send_employee_invitation(db, user, employee_name)
    db.commit()


def set_password_with_token(db: Session, token_value: str, password: str) -> None:
    token = get_valid_token(db, token_value)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_TOKEN_MESSAGE,
        )

    user = (
        db.query(User)
        .options(joinedload(User.employee))
        .filter(User.id == token.user_id)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_TOKEN_MESSAGE,
        )

    user.hashed_password = hash_password(password)
    user.is_active = True
    token.used = True

    if user.employee:
        user.employee.is_active = True

    db.commit()
