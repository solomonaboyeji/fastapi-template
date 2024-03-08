from typing import List, Union
from fastapi import HTTPException, Depends, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from passlib.context import CryptContext
from psycopg2 import sql

from datetime import datetime, timedelta

from core.config import ALGORITHM, SECRET_KEY
from core.database import get_db
from schemas.auth import TokenData
from schemas.user import User, UserFromDB
from utils.dependencies import has_required_scopes
from psycopg2.extensions import connection as PsycopgConnection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_user_from_db(
    db_instance: PsycopgConnection, email: str
) -> Union[UserFromDB, Exception]:
    db: PsycopgConnection = db_instance
    cursor = db.cursor()
    table_fields = list(UserFromDB.model_fields.keys())
    tables_str = ", ".join(table_fields)
    cursor.execute(
        sql.SQL(f"SELECT {tables_str} FROM users WHERE email = %s"), (email,)
    )
    row = cursor.fetchone()
    if row:
        user_dict = {}

        for index, _table in enumerate(table_fields):
            user_dict[_table] = row[index]

        return UserFromDB(**user_dict)
    return Exception("User not found")


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db=Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username: str = str(payload.get("sub"))

        # ignoring this cause it could be altered!
        scopes: List[str] = payload.get("scopes", [])

        if username is None:
            raise credentials_exception

        user_db = get_user_from_db(db, email=username)

        if isinstance(user_db, UserFromDB):
            user_db_scopes = user_db.scopes
        else:
            raise credentials_exception

        has_required_scopes(security_scopes.scopes, user_db_scopes)

        token_data = TokenData(username=username, scopes=user_db_scopes)
    except JWTError:
        raise credentials_exception
    return token_data


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def verify_password(plain_password, hashed_password):
    _result = pwd_context.verify(plain_password, hashed_password)
    return _result
