"""
CRUD - 统一导出
"""
from .member import MemberCRUD
from .coach import CoachCRUD

# 延迟导入避免循环依赖
def get_course_crud():
    from .course import CourseCRUD
    return CourseCRUD

def get_booking_crud():
    from .booking import BookingCRUD
    return BookingCRUD

__all__ = ["MemberCRUD", "CoachCRUD", "get_course_crud", "get_booking_crud"]