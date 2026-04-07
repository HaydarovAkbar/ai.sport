import pytest


@pytest.mark.asyncio
async def test_login_success(client, admin_user):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "testadmin", "password": "Test@123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "testadmin", "password": "WrongPass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client, admin_token):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testadmin"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_me_unauthorized(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client, admin_token):
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
