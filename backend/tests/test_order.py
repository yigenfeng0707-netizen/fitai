import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_order(client: AsyncClient, token: str):
    resp = await client.post("/api/v1/members/", json={
        "name": "TestMember", "phone": "13800000001",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    member_id = resp.json()["id"]

    resp = await client.post("/api/v1/orders/", json={
        "member_id": member_id,
        "amount": 199.0,
        "actual_amount": 199.0,
        "product_type": "card",
        "subject": "月卡购买",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["order_no"].startswith("ORD")
    assert data["amount"] == 199.0
    assert data["payment_status"] == "pending"
    assert data["member_id"] == member_id


@pytest.mark.asyncio
async def test_get_order(client: AsyncClient, token: str):
    await client.post("/api/v1/members/", json={
        "name": "M", "phone": "13800000002",
    }, headers={"Authorization": f"Bearer {token}"})
    member_resp = await client.post("/api/v1/members/", json={
        "name": "M", "phone": "13800000003",
    }, headers={"Authorization": f"Bearer {token}"})
    member_id = member_resp.json()["id"]

    order_resp = await client.post("/api/v1/orders/", json={
        "member_id": member_id, "amount": 99, "actual_amount": 99,
    }, headers={"Authorization": f"Bearer {token}"})
    order_id = order_resp.json()["id"]

    resp = await client.get(f"/api/v1/orders/{order_id}",
                            headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == order_id


@pytest.mark.asyncio
async def test_pay_order(client: AsyncClient, token: str):
    await client.post("/api/v1/members/", json={
        "name": "M2", "phone": "13800000004",
    }, headers={"Authorization": f"Bearer {token}"})
    member_resp = await client.post("/api/v1/members/", json={
        "name": "M2", "phone": "13800000005",
    }, headers={"Authorization": f"Bearer {token}"})

    order_resp = await client.post("/api/v1/orders/", json={
        "member_id": member_resp.json()["id"], "amount": 199, "actual_amount": 199,
    }, headers={"Authorization": f"Bearer {token}"})

    resp = await client.post(
        f"/api/v1/orders/{order_resp.json()['id']}/pay?payment_method=alipay",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_cancel_order(client: AsyncClient, token: str):
    member_resp = await client.post("/api/v1/members/", json={
        "name": "M3", "phone": "13800000006",
    }, headers={"Authorization": f"Bearer {token}"})

    order_resp = await client.post("/api/v1/orders/", json={
        "member_id": member_resp.json()["id"], "amount": 99, "actual_amount": 99,
    }, headers={"Authorization": f"Bearer {token}"})

    resp = await client.post(
        f"/api/v1/orders/{order_resp.json()['id']}/cancel?reason=测试取消",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["payment_status"] == "cancelled"


@pytest.mark.asyncio
async def test_order_list(client: AsyncClient, token: str):
    member_resp = await client.post("/api/v1/members/", json={
        "name": "M4", "phone": "13800000007",
    }, headers={"Authorization": f"Bearer {token}"})
    member_id = member_resp.json()["id"]

    for i in range(3):
        await client.post("/api/v1/orders/", json={
            "member_id": member_id, "amount": float(50 + i), "actual_amount": float(50 + i),
        }, headers={"Authorization": f"Bearer {token}"})

    resp = await client.get("/api/v1/orders/",
                            headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["data"]) == 3
