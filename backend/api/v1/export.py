"""
API - 数据导出
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User

router = APIRouter()

FILENAME_MAP = {
    "members": "会员数据",
    "orders": "订单数据",
    "bookings": "预约数据",
    "leads": "潜客数据",
}


@router.get("/{resource}")
async def export_data(
    resource: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if resource not in FILENAME_MAP:
        raise HTTPException(status_code=400, detail=f"不支持导出 {resource}，可选: {', '.join(FILENAME_MAP.keys())}")

    from backend.services.export import ExportService

    export_fn = {
        "members": ExportService.export_members,
        "orders": ExportService.export_orders,
        "bookings": ExportService.export_bookings,
        "leads": ExportService.export_leads,
    }[resource]

    data = await export_fn(db, current_user.organization_id)

    date_str = datetime.utcnow().strftime("%Y%m%d")
    filename = f"{FILENAME_MAP[resource]}_{date_str}.xlsx"

    return StreamingResponse(
        io_like_object(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encode_filename(filename)}"},
    )


def io_like_object(data: bytes):
    import io
    return io.BytesIO(data)


def encode_filename(filename: str) -> str:
    from urllib.parse import quote
    return quote(filename)
