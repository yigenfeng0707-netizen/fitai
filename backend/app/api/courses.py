from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.course import get_course_by_id, create_course, update_course, delete_course, get_courses, create_category, get_categories, create_classroom, get_classrooms, create_schedule, get_schedules, get_schedule_by_id
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse, CourseCategoryCreate, CourseCategoryResponse, ClassroomCreate, ClassroomResponse, ScheduleCreate, ScheduleResponse
from app.auth.security import get_current_user

router = APIRouter()

@router.get("/", response_model=list[CourseResponse])
async def read_courses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    courses = get_courses(db, skip=skip, limit=limit)
    return courses

@router.get("/{course_id}", response_model=CourseResponse)
async def read_course(course_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    course = get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.post("/", response_model=CourseResponse)
async def create_course_endpoint(course: CourseCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return create_course(db, course)

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course_endpoint(course_id: int, course_update: CourseUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    course = update_course(db, course_id, course_update)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.delete("/{course_id}", response_model=CourseResponse)
async def delete_course_endpoint(course_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    course = delete_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.get("/categories/", response_model=list[CourseCategoryResponse])
async def read_categories(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return get_categories(db)

@router.post("/categories/", response_model=CourseCategoryResponse)
async def create_category_endpoint(category: CourseCategoryCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return create_category(db, category)

@router.get("/classrooms/", response_model=list[ClassroomResponse])
async def read_classrooms(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return get_classrooms(db)

@router.post("/classrooms/", response_model=ClassroomResponse)
async def create_classroom_endpoint(classroom: ClassroomCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return create_classroom(db, classroom)

@router.get("/schedules/", response_model=list[ScheduleResponse])
async def read_schedules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    schedules = get_schedules(db, skip=skip, limit=limit)
    return schedules

@router.post("/schedules/", response_model=ScheduleResponse)
async def create_schedule_endpoint(schedule: ScheduleCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return create_schedule(db, schedule)