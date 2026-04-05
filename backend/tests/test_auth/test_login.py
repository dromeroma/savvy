"""Tests for the auth login endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Login with valid credentials should return token pair."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": "Login Corp",
            "slug": "login-corp",
            "email": "user@login.com",
            "password": "SecurePass123!",
            "name": "Test User",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@login.com",
            "password": "SecurePass123!",
            "org_slug": "login-corp",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """Login with incorrect password should return 401."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": "Wrong PW Corp",
            "slug": "wrong-pw",
            "email": "user@wrong.com",
            "password": "CorrectPass123!",
            "name": "Test User",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@wrong.com",
            "password": "WrongPassword!",
            "org_slug": "wrong-pw",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_org(client: AsyncClient) -> None:
    """Login to a non-existent organization should return 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nobody@nowhere.com",
            "password": "Whatever123!",
            "org_slug": "does-not-exist",
        },
    )
    assert response.status_code == 401
