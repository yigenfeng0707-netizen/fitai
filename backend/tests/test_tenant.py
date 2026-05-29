import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.organization import Organization
from backend.core.security import create_access_token


@pytest.mark.asyncio
async def test_register_auto_assigns_org(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "username": "user_a",
        "email": "user_a@example.com",
        "password": "Pass1234",
        "role": "receptionist",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "organization_id" in data


@pytest.mark.asyncio
async def test_token_contains_org_id(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "username": "user_b",
        "email": "user_b@example.com",
        "password": "Pass1234",
        "role": "receptionist",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "user_b",
        "password": "Pass1234",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    from backend.core.security import verify_token
    payload = verify_token(token)
    assert payload is not None
    assert "org_id" in payload


@pytest.mark.asyncio
async def test_tenant_isolation_members(client: AsyncClient, db: AsyncSession):
    org_a = Organization(name="OrgA", slug="org-aa")
    org_b = Organization(name="OrgB", slug="org-bb")
    db.add_all([org_a, org_b])
    await db.flush()

    from backend.crud.auth import UserCRUD
    user_a = await UserCRUD.create(db, "admin_a", "admin_a@example.com", "pass123", "super_admin", organization_id=org_a.id)
    _user_b = await UserCRUD.create(db, "admin_b", "admin_b@example.com", "pass123", "super_admin", organization_id=org_b.id)

    from backend.models.member import Member
    member_a = Member(name="UserA", phone="13800001001", organization_id=org_a.id)
    member_b = Member(name="UserB", phone="13800001002", organization_id=org_b.id)
    db.add_all([member_a, member_b])
    await db.commit()

    token_a = create_access_token(data={"sub": str(user_a.id), "role": "super_admin", "org_id": org_a.id})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    resp = await client.get("/api/v1/members/", headers=headers_a)
    assert resp.status_code == 200
    data = resp.json()["data"]
    names = [m["name"] for m in data]
    assert "UserA" in names
    assert "UserB" not in names


@pytest.mark.asyncio
async def test_tenant_isolation_orders(client: AsyncClient, db: AsyncSession):
    org_a = Organization(name="OrgC", slug="org-cc")
    org_b = Organization(name="OrgD", slug="org-dd")
    db.add_all([org_a, org_b])
    await db.flush()

    from backend.crud.auth import UserCRUD
    user_a = await UserCRUD.create(db, "admin_c", "admin_c@example.com", "pass123", "super_admin", organization_id=org_a.id)

    from backend.models.member import Member
    from backend.models.order import Order

    member_a = Member(name="M1", phone="13800002001", organization_id=org_a.id)
    member_b = Member(name="M2", phone="13800002002", organization_id=org_b.id)
    db.add_all([member_a, member_b])
    await db.flush()

    order_a = Order(order_no="ORD_A", member_id=member_a.id, amount=100,
                    actual_amount=100, organization_id=org_a.id)
    order_b = Order(order_no="ORD_B", member_id=member_b.id, amount=200,
                    actual_amount=200, organization_id=org_b.id)
    db.add_all([order_a, order_b])
    await db.commit()

    token_a = create_access_token(data={"sub": str(user_a.id), "role": "super_admin", "org_id": org_a.id})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    resp = await client.get("/api/v1/orders/", headers=headers_a)
    assert resp.status_code == 200
    order_nos = [o["order_no"] for o in resp.json()["data"]]
    assert "ORD_A" in order_nos
    assert "ORD_B" not in order_nos
