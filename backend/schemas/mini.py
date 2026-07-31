"""
Pydantic Schema - 小程序
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# ==================== 认证相关 ====================

class WxLoginRequest(BaseModel):
    """微信小程序登录请求"""
    code: str = Field(..., min_length=1, description="微信登录code")


class PhoneLoginRequest(BaseModel):
    """手机号登录请求"""
    phone: str = Field(..., min_length=11, max_length=20, description="手机号")
    verification_code: str = Field(..., min_length=4, max_length=6, description="验证码")


# ==================== 会员相关 ====================

class MiniMemberProfile(BaseModel):
    """小程序会员资料"""
    id: int
    name: str
    phone: str
    gender: Optional[str] = None
    birthday: Optional[date] = None
    card_type: Optional[str] = None
    card_end_date: Optional[date] = None
    card_remaining_count: Optional[int] = None
    card_balance: Optional[float] = None
    level: Optional[str] = None
    status: str
    store_name: Optional[str] = None

    model_config = {"from_attributes": True}


class MiniMemberCard(BaseModel):
    """小程序会员卡信息"""
    id: int
    card_type: Optional[str] = None
    card_start_date: Optional[datetime] = None
    card_end_date: Optional[datetime] = None
    card_remaining_count: Optional[int] = None
    card_balance: Optional[float] = None
    level: int
    status: str

    model_config = {"from_attributes": True}


# ==================== 课程相关 ====================

class MiniCourseItem(BaseModel):
    """小程序课程列表项"""
    id: int
    name: str
    course_type: str
    description: Optional[str] = None
    duration_minutes: int
    price: Optional[float] = None
    coach_name: Optional[str] = None
    max_attendees: int

    model_config = {"from_attributes": True}


class MiniScheduleItem(BaseModel):
    """小程序排课列表项"""
    id: int
    course_id: int
    course_name: str
    coach_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    enrolled_count: int
    max_attendees: int
    available_slots: int
    is_booked: bool = False

    model_config = {"from_attributes": True}


class MiniCoachItem(BaseModel):
    """小程序教练列表项"""
    id: int
    name: str
    phone: Optional[str] = None
    specialty: Optional[str] = None
    avatar: Optional[str] = None

    model_config = {"from_attributes": True}


# ==================== 预约相关 ====================

class MiniBookingItem(BaseModel):
    """小程序预约列表项"""
    id: int
    schedule_id: int
    course_name: str
    coach_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: str
    check_in_time: Optional[datetime] = None
    can_cancel: bool = False
    can_checkin: bool = False

    model_config = {"from_attributes": True}


class MiniBookingCreate(BaseModel):
    """小程序创建预约"""
    schedule_id: int = Field(..., gt=0, description="排课ID")


# ==================== 订单/支付相关 ====================

class MiniOrderCreate(BaseModel):
    """小程序创建订单"""
    product_type: str = Field(..., description="商品类型: membership, course_package, private_class")
    product_id: int = Field(..., gt=0, description="商品ID")
    amount: float = Field(..., ge=0, description="订单金额")
    payment_method: str = Field(default="wechat", description="支付方式")


class MiniOrderResponse(BaseModel):
    """小程序订单响应"""
    id: int
    order_no: str
    amount: float
    actual_amount: float
    payment_status: str
    product_type: str
    subject: str
    created_at: datetime
    paid_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WxPayParams(BaseModel):
    """微信支付参数"""
    timeStamp: str
    nonceStr: str
    package: str
    signType: str
    paySign: str


class PaymentConfirmRequest(BaseModel):
    """支付确认请求"""
    transaction_id: str = Field(..., min_length=1, description="微信支付交易号")


# ==================== 通知相关 ====================

class MiniNotificationItem(BaseModel):
    """小程序通知列表项"""
    id: int
    notification_type: str
    title: str
    content: Optional[str] = None
    is_read: bool = False
    link: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
