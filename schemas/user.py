from typing import List
from uuid import UUID
from pydantic import BaseModel, EmailStr


class CustomBaseModel(BaseModel):
    def list_values(
        self,
        mode: str = "python",
    ):
        """List outs all the values of the Pydantic model.

        Args:
            mode (str, optional): json serializable objects or python objects. Defaults to "python".

        Returns:
            List: List of objects.
        """
        return list(self.model_dump(mode=mode).values())


class User(CustomBaseModel):
    username: str
    email: str
    full_name: str | None = None
    disabled: bool | None = None
    scopes: List[str] = []
    email_verified: bool | None = False


class UserFromDB(User):
    hashed_password: str


class UserOut(User):
    id: UUID


class ListUsers(CustomBaseModel):
    size: int
    users: List[UserOut]


class UserCreate(CustomBaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str


class UserUpdate(CustomBaseModel):
    password: str
