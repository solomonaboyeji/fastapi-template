from typing import List, Union
from uuid import UUID, uuid4
import uuid
from venv import logger

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection as PsycopgConnection
from schemas.auth import PasswordResetToken
from schemas.user import ListUsers, User, UserCreate, UserFromDB, UserOut
from utils.emails import send_email
from utils.errors import (
    EMAIL_CONFIRMATION_ERROR_MESSAGE,
    EMAIL_PASSWORD_RESET_ERROR_MESSAGE,
    BadReqeustException,
    EmailException,
    ResourceNotFoundException,
    log_database_error,
)
from utils.scopes import UserScope
from utils.security import get_password_hash
import secrets, string


class UserService:

    def __init__(self, db, requesting_user: User | None = None) -> None:
        self.db: PsycopgConnection = db
        self.cursor = self.db.cursor()
        self.requesting_user = requesting_user

    def get_users(self, offset: int, page_count: int) -> ListUsers | Exception:
        table_fields = list(UserOut.model_fields.keys())
        tables_str = ", ".join(table_fields)
        try:
            self.cursor.execute(
                sql.SQL(f"SELECT {tables_str} FROM users OFFSET %s LIMIT %s"),
                (
                    offset,
                    page_count,
                ),
            )
            rows = self.cursor.fetchall()

            self.cursor.execute(sql.SQL("SELECT COUNT(*) FROM users"))
            user_size = self.cursor.fetchone()
        except Exception as exception:
            return log_database_error(exception)

        user_size = user_size[0] if user_size else 0
        user_dicts: List[UserOut] = []

        for row in rows:
            datum = {}
            for index, _table in enumerate(table_fields):
                datum[_table] = row[index]

            user_dicts.append(UserOut(**datum))

        return ListUsers(size=user_size, users=user_dicts)

    def get_user(self, email: str) -> Union[UserFromDB, Exception]:
        table_fields = list(UserFromDB.model_fields.keys())
        tables_str = ", ".join(table_fields)
        self.cursor.execute(
            sql.SQL(f"SELECT {tables_str} FROM users WHERE email = %s"), (email,)
        )
        row = self.cursor.fetchone()

        if row:
            user_dict = {}
            for index, _table in enumerate(table_fields):
                user_dict[_table] = row[index]

            return UserFromDB(**user_dict)
        return ResourceNotFoundException("User not found")

    def create_user(self, user: UserCreate) -> Union[User, Exception]:
        hashed_password = get_password_hash(user.password)
        default_scopes = [UserScope.list_.value]
        try:
            # Create confirmation token
            confirmation_token = secrets.token_hex(5).upper()
            self.cursor.execute(
                sql.SQL(
                    """
                        INSERT INTO users (username, email, full_name, disabled, hashed_password, 
                        email_verified, scopes, confirmation_token) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    """
                ),
                (
                    user.username,
                    user.email,
                    user.full_name,
                    False,
                    hashed_password,
                    False,
                    default_scopes,
                    confirmation_token,
                ),
            )
            self.db.commit()

            # Fetch the result (the inserted ID)
            result = self.cursor.fetchone()
            inserted_id = result[0] if result else None

            # Send email for email confirmation
            confirmation_link = (
                f"http://yourapp.com/confirm_email?token={confirmation_token}"
            )
            email_body = f"Please confirm your email by clicking on the link below:\n{confirmation_link}"

            send_email("Confirm Your Email", user.email, email_body)

        except psycopg2.IntegrityError as e:
            self.db.rollback()
            return log_database_error(e, "User with this email already exists")
        except EmailException as e:
            logger.error(e)
            return BadReqeustException(EMAIL_CONFIRMATION_ERROR_MESSAGE)
        except Exception as e:
            logger.error(e)
            return BadReqeustException(str(e))

        return UserOut(
            id=UUID(str(inserted_id)),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
        )

    def confirm_email(self, token: str) -> Union[User, Exception]:
        """Confirms the user's email. Please note returned data will have the email and username hidden

        Args:
            token (str): The token that was sent to the user.

        Returns:
            Union[User, Exception]: If any error occur while updating the records
        """

        try:
            self.cursor.execute(
                sql.SQL(
                    "UPDATE users SET email_verified = TRUE WHERE confirmation_token = %s"
                ),
                (token,),
            )

            if self.cursor.rowcount == 0:
                return BadReqeustException("Invalid confirmation token")
            self.db.commit()
        except psycopg2.DatabaseError as error:
            return log_database_error(error)
        except Exception as e:
            return BadReqeustException(e)

        return User(email_verified=True, email="hidden", username="hidden")

    def request_password_reset(
        self, email: str
    ) -> Union[PasswordResetToken, Exception]:
        # Generate and save reset token
        reset_token = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(16)
        )
        try:
            self.cursor.execute(
                sql.SQL(
                    "UPDATE users SET reset_token = %s, reset_token_expiry = NOW() + INTERVAL '10 minutes' WHERE email = %s"
                ),
                (reset_token, email),
            )
            if self.cursor.rowcount == 0:
                return ResourceNotFoundException("User not found")
            self.db.commit()

            # Send email with reset token
            reset_link = f"http://yourapp.com/reset_password?token={reset_token}"
            email_body = (
                f"Please use the following link to reset your password:\n{reset_link}"
            )
            send_email("Reset Your Password", email, email_body)
            return PasswordResetToken(email=email, token=reset_token)
        except psycopg2.DatabaseError as e:
            return log_database_error(e)
        except EmailException as e:
            return BadReqeustException(EMAIL_PASSWORD_RESET_ERROR_MESSAGE)
        except Exception as e:
            return BadReqeustException(e)

    def reset_password(self, token: str, new_password: str) -> Union[User, Exception]:
        """Resets the user's password. Please note returned data will have the email and username hidden

        Args:
            token (str): The token that was sent to the user.
            new_password (str): The new chosen password of the user.

        Returns:
            Union[User, Exception]: If any error occur while updating the records
        """

        try:
            # Check if token is valid
            self.cursor.execute(
                sql.SQL(
                    "SELECT email FROM users WHERE reset_token = %s AND reset_token_expiry >= NOW()"
                ),
                (token,),
            )
            row = self.cursor.fetchone()

            if not row:
                return BadReqeustException("Invalid or expired token")

            email = row[0]
            # Update password
            hashed_password = get_password_hash(new_password)
            self.cursor.execute(
                sql.SQL(
                    "UPDATE users SET hashed_password = %s, reset_token = NULL, reset_token_expiry = NULL WHERE email = %s"
                ),
                (hashed_password, email),
            )
            self.db.commit()
        except psycopg2.DatabaseError as e:
            return log_database_error(e)
        except Exception as e:
            return BadReqeustException(e)

        return User(email_verified=True, email="hidden", username="hidden")
