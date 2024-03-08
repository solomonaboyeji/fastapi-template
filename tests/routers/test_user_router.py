from os import path
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from pytest import fixture
from schemas.user import ListUsers, UserFromDB, UserOut

from services.user_service import UserService

from main import app
from utils.scopes import UserScope


client = TestClient(app)


expected_user = UserFromDB(
    username="solomon@gmail.com",
    email="solomon@gmail.com",
    full_name="Solomon",
    disabled=False,
    email_verified=False,
    scopes=[UserScope.list_],
    hashed_password="",
)


@fixture
@patch("utils.security.pwd_context.verify", return_value=True)
@patch.object(UserService, "get_user", return_value=expected_user)
@patch("jose.jwt.decode", return_value={"sub": "solomon", "scopes": [UserScope.list_]})
@patch("utils.security.get_user_from_db", return_value=expected_user)
def valid_auth_headers(_, _____, ____, __):
    response = client.post(
        "/auth/token",
        data={
            "username": "simple-email@gmail.com",
            "password": "simple-password",
        },
    )
    # Add a print statement to check if the method is called
    assert response.status_code == 200, response.json()
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_read_item(valid_auth_headers):

    # allows the user to be able to make the request with the correct scope.
    with patch("utils.security.get_user_from_db", return_value=expected_user):
        response = client.get("/users", headers=valid_auth_headers)
        assert response.status_code == 200, response.json()
        assert ListUsers.model_validate(response.json()).size > 0
        assert len(ListUsers.model_validate(response.json()).users) > 0

    # Mock UserService.get_user to return None
    with patch.object(UserService, "get_user", return_value=None):
        # Make a request to the endpoint
        response = client.get("/users/1")
        assert response.status_code == 404
