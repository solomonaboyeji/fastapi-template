from typing import Union
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from core.database import get_db
from schemas.auth import PasswordResetToken, Token
from schemas.user import User, UserCreate
from services.user_service import UserService
from utils.security import create_access_token, verify_password
from psycopg2.extensions import connection as PsycopgConnection

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: PsycopgConnection = Depends(get_db),
):
    """Authenticates the user."""

    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": user.scopes},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


def authenticate_user(
    db: PsycopgConnection,
    username: str,
    password: str,
) -> Union[User, None]:
    user = UserService(db, requesting_user=None).get_user(username)
    if isinstance(user, User):
        if not verify_password(password, user.hashed_password):
            return None
        return user
    return None


@router.post("/users/", response_model=User)
async def create_user(
    user: UserCreate,
    db: PsycopgConnection = Depends(get_db),
):
    """Creates a new user in the database."""
    user_or_exception = UserService(db).create_user(user)
    if isinstance(user_or_exception, User):
        return user_or_exception
    else:
        raise user_or_exception


@router.get("/confirm_email/")
async def confirm_email(
    token: str,
    db: PsycopgConnection = Depends(get_db),
):
    """Confirms the user's email."""

    result = UserService(db).confirm_email(token)
    if isinstance(result, User):
        return {"message": "Email confirmed successfully"}
    else:
        raise HTTPException(status_code=400, detail=str(result))


@router.post("/request_password_reset/")
async def request_password_reset(
    email: str,
    db: PsycopgConnection = Depends(get_db),
):
    """Permits the user to request for a password reset."""

    result = UserService(db).request_password_reset(email)
    if not isinstance(result, PasswordResetToken):
        print(f"We don't know the user with such email {email}")

    return {
        "message": "If an account is associated with that email, a password reset email was sent successfully"
    }


@router.post("/reset_password/")
async def reset_password(
    token: str,
    new_password: str,
    db: PsycopgConnection = Depends(get_db),
):
    """Performs the actual resetting of the user's password."""
    result = UserService(db).reset_password(token, new_password)
    if isinstance(result, User):
        return {"message": "Password reset successful"}
    else:
        raise HTTPException(status_code=400, detail=str(result))
