"""
API v1 路由总览
"""
from fastapi import APIRouter

from backend.api.v1 import auth, members, courses, bookings, coaches, orders, subscriptions, ai, leads, analytics, cards, notifications, audit, export, settings, campaign, automation, coupons

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(members.router, prefix="/members", tags=["会员"])
api_router.include_router(courses.router, prefix="/courses", tags=["课程"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["预约"])
api_router.include_router(coaches.router, prefix="/coaches", tags=["教练"])
api_router.include_router(orders.router, prefix="/orders", tags=["订单"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["订阅"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI 智能"])
api_router.include_router(leads.router, prefix="/leads", tags=["潜客 CRM"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["经营分析"])
api_router.include_router(cards.router, prefix="/cards", tags=["会员卡管理"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["消息通知"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["操作日志"])
api_router.include_router(export.router, prefix="/export", tags=["数据导出"])
api_router.include_router(settings.router, prefix="/settings", tags=["系统设置"])
api_router.include_router(campaign.router, prefix="/campaigns", tags=["营销活动"])
api_router.include_router(automation.router, prefix="/automations", tags=["营销自动化"])
api_router.include_router(coupons.router, prefix="/coupons", tags=["优惠券"])

__all__ = ["api_router", "auth", "members", "courses", "bookings", "coaches", "orders", "subscriptions", "ai", "leads", "analytics", "cards", "notifications", "audit", "export", "settings", "campaign", "automation", "coupons"]