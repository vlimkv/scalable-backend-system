import pytest


async def register_and_get_token(client, email="taskuser@example.com"):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Task User",
            "password": "strongpassword123",
        },
    )
    return response.json()["tokens"]["access_token"]


@pytest.mark.asyncio
async def test_create_task(client):
    token = await register_and_get_token(client)

    response = await client.post(
        "/api/v1/tasks",
        json={
            "title": "First task",
            "description": "Test description",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["title"] == "First task"
    assert data["description"] == "Test description"
    assert data["status"] == "todo"


@pytest.mark.asyncio
async def test_list_tasks(client):
    token = await register_and_get_token(client, email="list@example.com")

    await client.post(
        "/api/v1/tasks",
        json={
            "title": "Task 1",
            "description": "Desc 1",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    await client.post(
        "/api/v1/tasks",
        json={
            "title": "Task 2",
            "description": "Desc 2",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await client.get(
        "/api/v1/tasks?mine=true",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_update_task(client):
    token = await register_and_get_token(client, email="update@example.com")

    create_response = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Old title",
            "description": "Old desc",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    task_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "New title"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New title"


@pytest.mark.asyncio
async def test_update_task_status(client):
    token = await register_and_get_token(client, email="status@example.com")

    create_response = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Status task",
            "description": "Status desc",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    task_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"