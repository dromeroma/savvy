"""Tests for the organization endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_current_organization(client: AsyncClient, auth_headers: dict) -> None:
    """GET /api/v1/organizations/me returns the user's organization."""
    response = await client.get("/api/v1/organizations/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "test-corp"
    assert data["name"] == "Test Corp"
    assert data["type"] == "business"


@pytest.mark.asyncio
async def test_update_organization(client: AsyncClient, auth_headers: dict) -> None:
    """PATCH /api/v1/organizations/me updates org details."""
    response = await client.patch(
        "/api/v1/organizations/me",
        headers=auth_headers,
        json={"name": "Test Corp Updated"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Corp Updated"


@pytest.mark.asyncio
async def test_list_members(client: AsyncClient, auth_headers: dict) -> None:
    """GET /api/v1/organizations/members returns member list."""
    response = await client.get("/api/v1/organizations/members", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["role"] == "owner"
    assert data[0]["name"] == "Test Owner"
