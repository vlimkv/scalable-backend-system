import pytest


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "strongpassword123",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["full_name"] == "Test User"
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_login(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "full_name": "Login User",
            "password": "strongpassword123",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "strongpassword123",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["user"]["email"] == "login@example.com"
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_me_with_token(client):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "full_name": "Me User",
            "password": "strongpassword123",
        },
    )

    token = register_response.json()["tokens"]["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"