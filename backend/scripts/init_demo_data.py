import sys
import os
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.crud.user import create_user
from app.crud.member import create_member, create_member_card
from app.crud.course import create_course, create_course_category, create_classroom, create_schedule
from app.crud.coach import create_coach
from app.schemas.user import UserCreate
from app.schemas.member import MemberCreate, MemberCardCreate
from app.schemas.course import CourseCreate, CourseCategoryCreate, ClassroomCreate, ScheduleCreate
from app.schemas.coach import CoachCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_data():
    db = SessionLocal()
    
    print("Creating admin user...")
    admin_user = UserCreate(
        username="admin",
        password="admin123",
        name="超级管理员",
        phone="13800138000",
        role_id=1,
        store_id=1
    )
    create_user(db, admin_user)
    
    print("Creating test user for receptionist...")
    reception_user = UserCreate(
        username="reception",
        password="123456",
        name="前台小张",
        phone="13800138001",
        role_id=3,
        store_id=1
    )
    create_user(db, reception_user)
    
    print("Creating test user for coach...")
    coach_user = UserCreate(
        username="coach001",
        password="123456",
        name="李教练",
        phone="13800138002",
        role_id=4,
        store_id=1
    )
    create_user(db, coach_user)
    
    print("Creating course categories...")
    cat1 = create_course_category(db, CourseCategoryCreate(name="瑜伽", description="各类瑜伽课程"))
    cat2 = create_course_category(db, CourseCategoryCreate(name="普拉提", description="普拉提训练课程"))
    cat3 = create_course_category(db, CourseCategoryCreate(name="力量训练", description="力量训练课程"))
    
    print("Creating classrooms...")
    room1 = create_classroom(db, ClassroomCreate(name="阳光瑜伽室", capacity=20, location="一楼A区"))
    room2 = create_classroom(db, ClassroomCreate(name="力量训练室", capacity=15, location="二楼B区"))
    
    print("Creating courses...")
    course1 = create_course(db, CourseCreate(
        name="基础瑜伽",
        category_id=cat1.id,
        course_type="group",
        duration=60,
        price=120,
        description="适合初学者的基础瑜伽课程",
        max_participants=15
    ))
    course2 = create_course(db, CourseCreate(
        name="高温瑜伽",
        category_id=cat1.id,
        course_type="group",
        duration=60,
        price=150,
        description="高温环境下的瑜伽练习",
        max_participants=12
    ))
    course3 = create_course(db, CourseCreate(
        name="私教普拉提",
        category_id=cat2.id,
        course_type="private",
        duration=45,
        price=300,
        description="一对一普拉提训练",
        max_participants=1
    ))
    
    print("Creating coaches...")
    coach1 = create_coach(db, CoachCreate(
        name="李教练",
        phone="13800138002",
        email="li@fitai.com",
        certificate="高级瑜伽教练认证",
        specialty="瑜伽、普拉提",
        hourly_rate=200,
        user_id=3
    ))
    coach2 = create_coach(db, CoachCreate(
        name="王教练",
        phone="13800138003",
        email="wang@fitai.com",
        certificate="国家级健身教练",
        specialty="力量训练、功能性训练",
        hourly_rate=250
    ))
    
    print("Creating schedules...")
    from datetime import date, time
    create_schedule(db, ScheduleCreate(
        course_id=course1.id,
        coach_id=coach1.id,
        classroom_id=room1.id,
        date=date.today().isoformat(),
        start_time="09:00",
        end_time="10:00",
        status="available"
    ))
    create_schedule(db, ScheduleCreate(
        course_id=course1.id,
        coach_id=coach1.id,
        classroom_id=room1.id,
        date=date.today().isoformat(),
        start_time="14:00",
        end_time="15:00",
        status="available"
    ))
    create_schedule(db, ScheduleCreate(
        course_id=course2.id,
        coach_id=coach1.id,
        classroom_id=room1.id,
        date=date.today().isoformat(),
        start_time="19:00",
        end_time="20:00",
        status="available"
    ))
    
    print("Creating members...")
    member1 = create_member(db, MemberCreate(
        name="张小明",
        phone="13900139001",
        gender="male",
        birthday="1990-01-15",
        email="zhang@test.com",
        address="北京市朝阳区xxx街道"
    ))
    member2 = create_member(db, MemberCreate(
        name="李小红",
        phone="13900139002",
        gender="female",
        birthday="1995-05-20",
        email="li@test.com",
        address="北京市海淀区xxx街道"
    ))
    member3 = create_member(db, MemberCreate(
        name="王小华",
        phone="13900139003",
        gender="male",
        birthday="1988-11-30",
        email="wang@test.com",
        address="北京市西城区xxx街道"
    ))
    
    print("Creating member cards...")
    create_member_card(db, MemberCardCreate(
        member_id=member1.id,
        card_type="monthly",
        total_classes=30,
        remaining_classes=25,
        amount=1980,
        start_date=date.today().isoformat(),
        end_date=(date.today().replace(month=date.today().month+1) if date.today().month < 12 else date.today().replace(year=date.today().year+1, month=1)).isoformat()
    ))
    create_member_card(db, MemberCardCreate(
        member_id=member2.id,
        card_type="yearly",
        total_classes=100,
        remaining_classes=85,
        amount=9800,
        start_date=date.today().isoformat(),
        end_date=(date.today().replace(year=date.today().year+1)).isoformat()
    ))
    
    db.close()
    print("\n✅ Demo data initialization completed!")
    print("\nTest accounts:")
    print("  - admin / admin123 (超级管理员)")
    print("  - reception / 123456 (前台)")
    print("  - coach001 / 123456 (教练)")

if __name__ == "__main__":
    init_data()