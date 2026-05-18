from sqlalchemy.orm import Session
from app.models.booking import Booking, Attendance
from app.schemas.booking import BookingCreate, BookingUpdate, AttendanceCreate
from datetime import datetime

def create_booking(db: Session, booking: BookingCreate):
    db_booking = Booking(
        schedule_id=booking.schedule_id,
        member_id=booking.member_id,
        notes=booking.notes
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def get_booking_by_id(db: Session, booking_id: int):
    return db.query(Booking).filter(Booking.id == booking_id).first()

def get_bookings_by_member(db: Session, member_id: int):
    return db.query(Booking).filter(Booking.member_id == member_id).all()

def get_bookings_by_schedule(db: Session, schedule_id: int):
    return db.query(Booking).filter(Booking.schedule_id == schedule_id).all()

def update_booking(db: Session, booking_id: int, booking_update: BookingUpdate):
    db_booking = get_booking_by_id(db, booking_id)
    if db_booking:
        for key, value in booking_update.model_dump(exclude_unset=True).items():
            setattr(db_booking, key, value)
        db.commit()
        db.refresh(db_booking)
    return db_booking

def cancel_booking(db: Session, booking_id: int):
    db_booking = get_booking_by_id(db, booking_id)
    if db_booking:
        db_booking.status = "canceled"
        db_booking.canceled_at = datetime.utcnow()
        db.commit()
        db.refresh(db_booking)
    return db_booking

def create_attendance(db: Session, attendance: AttendanceCreate):
    db_attendance = Attendance(
        booking_id=attendance.booking_id,
        check_in_time=datetime.utcnow()
    )
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def get_attendance_by_id(db: Session, attendance_id: int):
    return db.query(Attendance).filter(Attendance.id == attendance_id).first()