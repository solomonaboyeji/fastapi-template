from typing import List
from pydantic import BaseModel
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    scopes: List[str] = []


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: datetime | None = None
    scopes: List[str] = []


class PasswordResetToken(BaseModel):
    email: str
    token: str
