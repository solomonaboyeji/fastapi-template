import os
import unittest
from uuid import uuid4
import psycopg2
import pytest
from unittest.mock import MagicMock, patch
from schemas.auth import PasswordResetToken
from services.user_service import UserService
from utils.errors import (
    BadReqeustException,
    DuplicateResourceException,
    ResourceNotFoundException,
)
from schemas.user import User, UserCreate, UserFromDB, UserOut


os.environ["TESTING"] = "True"

expected_user = UserOut(
    id=uuid4(),
    username="solomon@gmail.com",
    email="solomon@gmail.com",
    full_name="Solomon",
    disabled=False,
    email_verified=False,
    scopes=[],
)


@pytest.fixture
def mock_db_connection():
    return MagicMock()


def test_get_users_success(mock_db_connection):
    mock_db_connection.reset_mock()

    # Mock the cursor and execute method
    mock_cursor = MagicMock()
    mock_db_connection.cursor.return_value = mock_cursor

    # Set up a mock return value for the execute method
    expected_result = [expected_user.list_values()]
    mock_cursor.fetchall.return_value = expected_result

    # Create a UserService instance
    user_service = UserService(mock_db_connection)

    # Call the method under test with appropriate parameters
    result = user_service.get_users(offset=0, page_count=10)

    # Assertions
    mock_db_connection.cursor.assert_called_once()
    mock_cursor.fetchall.assert_called_once()
    mock_cursor.execute.assert_called()


def test_create_users_success(mock_db_connection):
    mock_db_connection.reset_mock()
    # Mock the token generation function
    with patch("secrets.token_hex", return_value="A_CONFIRM_TOKEN"):

        # Ensure you are importing the function from the UserService file,
        # this would have been imported already in that class/module
        with patch("services.user_service.send_email") as mock_send_mail:
            # Mock the database cursor
            mock_cursor = MagicMock()
            mock_db_connection.cursor.return_value = mock_cursor

            mock_cursor.fetchone.return_value = (str(expected_user.id),)

            # Mock the database execute method for the successful user creation
            mock_cursor.rowcount.return_value = 1
            mock_db_connection.commit.side_effect = (
                None  # Ensure commit does not raise an exception
            )

            # Create a UserService instance
            user_service = UserService(mock_db_connection)
            # the cursor function must have been called on the connection
            # object/class
            mock_db_connection.cursor.assert_called_once()

            # Call the method under test
            result = user_service.create_user(
                UserCreate(
                    **{**expected_user.model_dump(), "password": "secret"},
                )
            )

            # # Assertions
            assert isinstance(result, User)
            assert result.email == expected_user.email
            assert result.username == expected_user.username

            # # Ensure the database cursor and connection were used correctly
            # ensure the commit function was called
            mock_db_connection.commit.assert_called()
            # ensure the last inserted id was gotten
            mock_cursor.fetchone.assert_called_once()
            mock_send_mail.assert_called_once()


def test_create_user_with_duplicate_email_fails(mock_db_connection):
    mock_db_connection.reset_mock()
    # Mock the token generation function
    with patch("secrets.token_hex", return_value="A_CONFIRM_TOKEN"):

        # Ensure you are importing the function from the UserService file,
        # this would have been imported already in that class/module
        with patch("services.user_service.send_email") as mock_send_mail:
            # Mock the database cursor
            mock_cursor = MagicMock()
            mock_db_connection.cursor.return_value = mock_cursor
            mock_db_connection.commit.side_effect = psycopg2.IntegrityError("duplicate")

            user_service = UserService(mock_db_connection)
            mock_db_connection.cursor.assert_called_once()

            # Call the method under test
            result = user_service.create_user(
                UserCreate(
                    **{**expected_user.model_dump(), "password": "secret"},
                )
            )

            # # Assertions
            assert isinstance(result, DuplicateResourceException)

            # # Ensure the database cursor and connection were used correctly
            mock_db_connection.commit.assert_called()
            mock_cursor.fetchone.assert_not_called()
            mock_send_mail.assert_not_called()


def test_get_user(mock_db_connection):
    mock_db_connection.reset_mock()

    mock_cursor = MagicMock()
    mock_db_connection.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = expected_user.list_values(mode="json")
    mock_cursor.rowcount.return_value = 1

    user_service = UserService(mock_db_connection)
    user = user_service.get_user(expected_user.email)
    assert isinstance(user, UserFromDB)
    assert user.email == expected_user.email
    assert user.full_name == expected_user.full_name

    # Assertions
    mock_db_connection.cursor.assert_called_once()
    mock_cursor.fetchone.assert_called_once()
    mock_cursor.execute.assert_called_once()


def test_get_user_with_non_existing_email_fails(mock_db_connection):
    mock_db_connection.reset_mock()

    mock_cursor = MagicMock()
    mock_db_connection.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ()
    mock_cursor.rowcount.return_value = 0

    user_service = UserService(mock_db_connection)
    mock_db_connection.cursor.assert_called_once()

    exception = user_service.get_user(expected_user.email)
    assert isinstance(exception, ResourceNotFoundException)

    # Assertions
    mock_db_connection.cursor.assert_called_once()
    mock_cursor.fetchone.assert_called_once()
    mock_cursor.execute.assert_called_once()


def test_confirm_user_email_is_successful(mock_db_connection):
    mock_db_connection.reset_mock()

    mock_cursor = MagicMock()

    mock_cursor.rowcount = 1
    mock_db_connection.cursor.return_value = mock_cursor

    user_service = UserService(mock_db_connection)
    mock_db_connection.cursor.assert_called_once()

    # Mock the token generation function
    with patch("secrets.token_hex", return_value="A_CONFIRM_TOKEN"):
        user = user_service.confirm_email("A_CONFIRM_TOKEN")
        assert isinstance(user, User)

    # Assertions
    mock_db_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()


def test_confirm_email_with_non_existing_confirmation_code_fails(mock_db_connection):
    mock_db_connection.reset_mock()

    mock_cursor = MagicMock()

    mock_cursor.rowcount = 0
    mock_db_connection.cursor.return_value = mock_cursor

    user_service = UserService(mock_db_connection)
    mock_db_connection.cursor.assert_called_once()

    # Mock the token generation function
    with patch("secrets.token_hex", return_value="A_CONFIRM_TOKEN"):
        user = user_service.confirm_email("A_CONFIRM_TOKEN")
        assert isinstance(user, BadReqeustException)

    # Assertions
    mock_db_connection.cursor.assert_called_once()
    mock_db_connection.commit.assert_not_called()
    mock_cursor.execute.assert_called_once()


def test_request_password_reset_passes(mock_db_connection):

    mock_db_connection.reset_mock()

    mock_cursor = MagicMock()

    mock_cursor.rowcount = 1
    mock_db_connection.cursor.return_value = mock_cursor

    user_service = UserService(mock_db_connection)
    mock_db_connection.cursor.assert_called_once()

    with patch("services.user_service.send_email") as mock_send_mail:
        # Mock the token generation function
        with patch("secrets.choice", return_value="A"):
            user = user_service.request_password_reset(expected_user.email)
            assert isinstance(user, PasswordResetToken)
            mock_send_mail.assert_called_once()

    # Assertions
    mock_db_connection.cursor.assert_called_once()
    mock_db_connection.commit.assert_called_once()
    mock_cursor.execute.assert_called_once()


def test_request_password_reset_with_invalid_email_fails(mock_db_connection):

    mock_db_connection.reset_mock()

    mock_cursor = MagicMock()

    mock_cursor.rowcount = 0
    mock_db_connection.cursor.return_value = mock_cursor

    user_service = UserService(mock_db_connection)
    mock_db_connection.cursor.assert_called_once()

    with patch("services.user_service.send_email") as mock_send_mail:
        # Mock the token generation function
        with patch("secrets.choice", return_value="A"):
            user = user_service.request_password_reset(expected_user.email)
            assert isinstance(user, ResourceNotFoundException)
            mock_send_mail.assert_not_called()

    # Assertions
    mock_db_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    mock_db_connection.commit.assert_not_called()


def test_reset_password_passes(mock_db_connection):

    mock_db_connection.reset_mock()
    mock_cursor = MagicMock()

    mock_cursor.rowcount = 1
    mock_db_connection.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (expected_user.email,)

    user_service = UserService(mock_db_connection)
    mock_db_connection.cursor.assert_called_once()

    user = user_service.reset_password(
        "SOMETHING_rANDOM", new_password="new_password_yah!"
    )

    # Assertions
    assert isinstance(user, User)
    mock_db_connection.cursor.assert_called_once()
    assert mock_cursor.execute.call_count == 2


def test_reset_password_with_invalid_fails(mock_db_connection):
    mock_db_connection.reset_mock()
    mock_cursor = MagicMock()

    mock_cursor.rowcount = 0
    mock_db_connection.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ()

    user_service = UserService(mock_db_connection)
    mock_db_connection.cursor.assert_called_once()

    user = user_service.reset_password(
        "SOMETHING_rANDOM", new_password="new_password_yah!"
    )

    # Assertions
    assert isinstance(user, BadReqeustException)
    mock_db_connection.cursor.assert_called_once()
