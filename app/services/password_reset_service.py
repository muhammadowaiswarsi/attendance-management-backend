import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.utils.email_sender import EmailSendError, send_password_reset_email

RESET_TOKEN_EXPIRY_HOURS = 1
INVALID_TOKEN_MESSAGE = "Invalid or expired token."
FORGOT_PASSWORD_MESSAGE = (
    "If an account exists for this email, a reset link has been sent."
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_expiry(expires_at: datetime) -> datetime:
    if expires_at.tzinfo is None:
        return expires_at.replace(tzinfo=timezone.utc)
    return expires_at.astimezone(timezone.utc)


def invalidate_unused_reset_tokens(db: Session, user_id: int) -> None:
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.used.is_(False),
    ).update({PasswordResetToken.used: True}, synchronize_session=False)


def create_reset_token(db: Session, user_id: int) -> PasswordResetToken:
    invalidate_unused_reset_tokens(db, user_id)

    token = PasswordResetToken(
        user_id=user_id,
        token=secrets.token_urlsafe(32),
        expires_at=_utcnow() + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS),
        used=False,
    )
    db.add(token)
    db.flush()
    return token


def get_valid_reset_token(db: Session, token_value: str) -> PasswordResetToken | None:
    token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == token_value)
        .first()
    )
    if not token or token.used:
        return None
    if _normalize_expiry(token.expires_at) <= _utcnow():
        return None
    return token


def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    if not user.hashed_password or not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    if verify_password(new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current password.",
        )

    user.hashed_password = hash_password(new_password)
    db.commit()


def request_password_reset(db: Session, email: str) -> str:
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active or not user.hashed_password:
        return FORGOT_PASSWORD_MESSAGE

    token = create_reset_token(db, user.id)
    db.commit()
    db.refresh(token)

    try:
        send_password_reset_email(
            recipient_email=user.email,
            full_name=user.full_name,
            token=token.token,
        )
    except EmailSendError:
        pass

    return FORGOT_PASSWORD_MESSAGE


def reset_password_with_token(db: Session, token_value: str, password: str) -> None:
    token = get_valid_reset_token(db, token_value)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_TOKEN_MESSAGE,
        )

    user = db.query(User).filter(User.id == token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_TOKEN_MESSAGE,
        )

    user.hashed_password = hash_password(password)
    user.is_active = True
    token.used = True
    db.commit()
