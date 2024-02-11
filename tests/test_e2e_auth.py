from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import select

from src.conf import messages
from src.models.users import UserModel
from tests.conftest import TestingSessionLocal

user_data = {"username": "test_user_auth@example.com", "password": "qaz12EDC"}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr(
        "src.routers.auth.email_service.send_verification_mail", mock_send_email
    )
    response = client.post("api/auth/signup", json=user_data)

    assert response.status_code == 201, response.text
    data = response.json()

    assert data["username"] == user_data["username"]
    assert "password" not in data
    assert mock_send_email.called
    assert "avatar" in data


def test_repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr(
        "src.routers.auth.email_service.send_verification_mail", mock_send_email
    )
    response = client.post("api/auth/signup", json=user_data)

    assert response.status_code == 409, response.text
    data = response.json()

    assert data["detail"] == messages.ACCOUNT_EXIST


def test_not_confirmed_login(client, monkeypatch):

    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())

    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )

    assert response.status_code == 401, response.text
    data = response.json()

    assert data["detail"] == messages.EMAIL_NOT_CONFIRMED


@pytest.mark.asyncio
async def test_confirmed_login(client, monkeypatch):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(UserModel).where(UserModel.username == user_data.get("username"))
        )
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())

    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data


def test_wrong_password_login(client, monkeypatch):
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())

    response = client.post(
        "api/auth/login",
        data={"username": user_data.get("username"), "password": "wrong_password"},
    )

    assert response.status_code == 401, response.text
    data = response.json()

    assert data["detail"] == messages.INVALID_PASSWORD


def test_wrong_email_login(client, monkeypatch):
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())

    response = client.post(
        "api/auth/login",
        data={"username": "wrong_username", "password": user_data.get("password")},
    )

    assert response.status_code == 401, response.text
    data = response.json()

    assert data["detail"] == messages.INVALID_USERNAME


def test_validation_error_login(client, monkeypatch):
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())

    response = client.post(
        "api/auth/login", data={"password": user_data.get("password")}
    )

    assert response.status_code == 422, response.text
    data = response.json()
    print(response.text)
    assert "detail" in data


def test_refresh_token(client, monkeypatch):
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())

    response_login = client.post(
        "api/auth/login",
        data={"username": user_data["username"], "password": user_data["password"]},
    )
    login_data = response_login.json()

    refresh_token = login_data.get("refresh_token")

    response = client.get(
        "api/auth/refresh_token/", headers={"Authorization": f"Bearer {refresh_token}"}
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
