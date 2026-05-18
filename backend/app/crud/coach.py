from sqlalchemy.orm import Session
from app.models.coach import Coach, CoachSchedule, TeachingRecord
from app.schemas.coach import CoachCreate, CoachUpdate, CoachScheduleCreate, TeachingRecordCreate
from datetime import datetime
import uuid

def generate_coach_no() -> str:
    return "C" + datetime.now().strftime("%Y%m%d") + str(uuid.uuid4())[:4].upper()

def get_coach_by_id(db: Session, coach_id: int):
    return db.query(Coach).filter(Coach.id == coach_id).first()

def get_coaches(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Coach).offset(skip).limit(limit).all()

def create_coach(db: Session, coach: CoachCreate):
    coach_no = generate_coach_no()
    db_coach = Coach(
        coach_no=coach_no,
        name=coach.name,
        phone=coach.phone,
        email=coach.email,
        avatar=coach.avatar,
        qualifications=coach.qualifications,
        specialties=coach.specialties,
        hourly_rate=coach.hourly_rate
    )
    db.add(db_coach)
    db.commit()
    db.refresh(db_coach)
    return db_coach

def update_coach(db: Session, coach_id: int, coach_update: CoachUpdate):
    db_coach = get_coach_by_id(db, coach_id)
    if db_coach:
        for key, value in coach_update.model_dump(exclude_unset=True).items():
            setattr(db_coach, key, value)
        db.commit()
        db.refresh(db_coach)
    return db_coach

def delete_coach(db: Session, coach_id: int):
    db_coach = get_coach_by_id(db, coach_id)
    if db_coach:
        db.delete(db_coach)
        db.commit()
    return db_coach

def create_coach_schedule(db: Session, schedule: CoachScheduleCreate):
    db_schedule = CoachSchedule(
        coach_id=schedule.coach_id,
        day_of_week=schedule.day_of_week,
        start_time=schedule.start_time,
        end_time=schedule.end_time
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def get_coach_schedules(db: Session, coach_id: int):
    return db.query(CoachSchedule).filter(CoachSchedule.coach_id == coach_id).all()

def create_teaching_record(db: Session, record: TeachingRecordCreate):
    db_record = TeachingRecord(
        coach_id=record.coach_id,
        schedule_id=record.schedule_id,
        date=record.date,
        duration=record.duration,
        attendees=record.attendees,
        rating=record.rating,
        notes=record.notes
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_teaching_records(db: Session, coach_id: int):
    return db.query(TeachingRecord).filter(TeachingRecord.coach_id == coach_id).all()