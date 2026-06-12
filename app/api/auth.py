from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import ALGORITHM, SECRET_KEY
from app.core.security import create_access_token
from app.database.db import get_db
from app.models.user import User
from app.schemas.password_setup import MessageResponse, SetPasswordRequest
from app.schemas.profile import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ProfileResponse,
    ProfileUpdate,
    ResetPasswordRequest,
)
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.services import invitation_service, password_reset_service, profile_service, user_service

router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, user)


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    existing_user = user_service.get_user_by_email(db, user_data.email)
    if existing_user and not existing_user.is_active:
        if not existing_user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please set your password using the invitation email.",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive. Please contact your administrator.",
        )

    user = user_service.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    profile_service.record_login(db, user)
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/set-password", response_model=MessageResponse)
def set_password(payload: SetPasswordRequest, db: Session = Depends(get_db)):
    invitation_service.set_password_with_token(db, payload.token, payload.password)
    return {"message": "Password set successfully."}


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    password_reset_service.change_password(
        db,
        current_user,
        payload.current_password,
        payload.new_password,
    )
    return {"message": "Password changed successfully."}


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    message = password_reset_service.request_password_reset(db, payload.email)
    return {"message": message}


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    password_reset_service.reset_password_with_token(db, payload.token, payload.password)
    return {"message": "Password reset successfully."}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/profile", response_model=ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return profile_service.get_profile(db, current_user)


@router.put("/profile", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return profile_service.update_profile(db, current_user, payload)
