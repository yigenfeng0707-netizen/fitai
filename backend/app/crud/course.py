from sqlalchemy.orm import Session
from app.models.course import Course, CourseCategory, Classroom, Schedule
from app.schemas.course import CourseCreate, CourseUpdate, CourseCategoryCreate, ClassroomCreate, ScheduleCreate

def get_course_by_id(db: Session, course_id: int):
    return db.query(Course).filter(Course.id == course_id).first()

def get_courses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Course).offset(skip).limit(limit).all()

def create_course(db: Session, course: CourseCreate):
    db_course = Course(
        name=course.name,
        category_id=course.category_id,
        course_type=course.course_type,
        duration=course.duration,
        price=course.price,
        description=course.description,
        max_capacity=course.max_capacity
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

def update_course(db: Session, course_id: int, course_update: CourseUpdate):
    db_course = get_course_by_id(db, course_id)
    if db_course:
        for key, value in course_update.model_dump(exclude_unset=True).items():
            setattr(db_course, key, value)
        db.commit()
        db.refresh(db_course)
    return db_course

def delete_course(db: Session, course_id: int):
    db_course = get_course_by_id(db, course_id)
    if db_course:
        db.delete(db_course)
        db.commit()
    return db_course

def create_category(db: Session, category: CourseCategoryCreate):
    db_category = CourseCategory(
        name=category.name,
        description=category.description,
        color=category.color
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_categories(db: Session):
    return db.query(CourseCategory).all()

def create_classroom(db: Session, classroom: ClassroomCreate):
    db_classroom = Classroom(
        name=classroom.name,
        capacity=classroom.capacity,
        equipment=classroom.equipment
    )
    db.add(db_classroom)
    db.commit()
    db.refresh(db_classroom)
    return db_classroom

def get_classrooms(db: Session):
    return db.query(Classroom).all()

def create_schedule(db: Session, schedule: ScheduleCreate):
    db_schedule = Schedule(
        course_id=schedule.course_id,
        classroom_id=schedule.classroom_id,
        coach_id=schedule.coach_id,
        date=schedule.date,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        max_capacity=schedule.max_capacity
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def get_schedule_by_id(db: Session, schedule_id: int):
    return db.query(Schedule).filter(Schedule.id == schedule_id).first()

def get_schedules(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Schedule).offset(skip).limit(limit).all()