"""Tests for the auth registration endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_creates_org_and_user(client: AsyncClient) -> None:
    """POST /api/v1/auth/register should create organization, user, and return tokens."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "org_name": "Acme Inc",
            "slug": "acme-inc",
            "email": "admin@acme.com",
            "password": "SecurePass123!",
            "name": "John Doe",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]
    assert data["user"]["email"] == "admin@acme.com"
    assert data["user"]["name"] == "John Doe"
    assert data["organization"]["slug"] == "acme-inc"
    assert data["organization"]["type"] == "business"


@pytest.mark.asyncio
async def test_register_duplicate_slug_fails(client: AsyncClient) -> None:
    """Registering with an existing slug should return 409."""
    payload = {
        "org_name": "Unique Co",
        "slug": "unique-co",
        "email": "user@unique.com",
        "password": "SecurePass123!",
        "name": "Jane Doe",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
