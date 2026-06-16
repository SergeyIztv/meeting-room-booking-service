import pytest


PASS = "Strong!Pass1"
PASS2 = "Strong!Pass2"
PASS3 = "Strong!Pass3"


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post(
        "/auth/register", json={"username": "alice", "password": PASS}
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate(client):
    await client.post("/auth/register", json={"username": "alice", "password": PASS})
    response = await client.post(
        "/auth/register", json={"username": "alice", "password": PASS2}
    )
    assert response.status_code == 400
    assert response.json()["code"] == "USERNAME_EXISTS"


@pytest.mark.asyncio
async def test_register_weak_password(client):
    response = await client.post(
        "/auth/register", json={"username": "alice", "password": "secret"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/auth/register", json={"username": "bob", "password": PASS})
    response = await client.post(
        "/auth/login", json={"username": "bob", "password": PASS}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json={"username": "bob", "password": PASS})
    response = await client.post(
        "/auth/login", json={"username": "bob", "password": "wrong"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_promote_to_admin(client):
    reg_resp = await client.post(
        "/auth/register", json={"username": "admin_user", "password": PASS}
    )
    admin_token = reg_resp.json()["access_token"]

    await client.post(
        "/auth/register", json={"username": "target", "password": PASS2}
    )

    response = await client.post(
        "/admins",
        json={"user_id": 2},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert "is now admin" in response.json()["detail"]


@pytest.mark.asyncio
async def test_promote_to_admin_forbidden(client):
    # first user becomes admin
    await client.post(
        "/auth/register", json={"username": "admin_user", "password": PASS}
    )
    # second user is employee
    reg_resp = await client.post(
        "/auth/register", json={"username": "employee", "password": PASS2}
    )
    token = reg_resp.json()["access_token"]

    response = await client.post(
        "/admins",
        json={"user_id": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_promote_to_admin_not_found(client):
    reg_resp = await client.post(
        "/auth/register", json={"username": "admin_user", "password": PASS}
    )
    token = reg_resp.json()["access_token"]

    response = await client.post(
        "/admins",
        json={"user_id": 999},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
