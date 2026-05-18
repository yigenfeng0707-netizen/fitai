from fastapi import APIRouter
from app.api.members import router as members_router
from app.api.courses import router as courses_router
from app.api.bookings import router as bookings_router
from app.api.coaches import router as coaches_router
from app.api.auth import router as auth_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["认证"])
router.include_router(members_router, prefix="/members", tags=["会员管理"])
router.include_router(courses_router, prefix="/courses", tags=["课程管理"])
router.include_router(bookings_router, prefix="/bookings", tags=["预约签到"])
router.include_router(coaches_router, prefix="/coaches", tags=["教练管理"])