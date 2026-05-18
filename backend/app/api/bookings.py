from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.booking import create_booking, get_booking_by_id, get_bookings_by_member, get_bookings_by_schedule, update_booking, cancel_booking, create_attendance, get_attendance_by_id
from app.schemas.booking import BookingCreate, BookingUpdate, BookingResponse, AttendanceCreate, AttendanceResponse
from app.auth.security import get_current_user

router = APIRouter()

@router.post("/", response_model=BookingResponse)
async def create_booking_endpoint(booking: BookingCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return create_booking(db, booking)

@router.get("/{booking_id}", response_model=BookingResponse)
async def read_booking(booking_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    booking = get_booking_by_id(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@router.get("/member/{member_id}", response_model=list[BookingResponse])
async def read_bookings_by_member(member_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return get_bookings_by_member(db, member_id)

@router.get("/schedule/{schedule_id}", response_model=list[BookingResponse])
async def read_bookings_by_schedule(schedule_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return get_bookings_by_schedule(db, schedule_id)

@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking_endpoint(booking_id: int, booking_update: BookingUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    booking = update_booking(db, booking_id, booking_update)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@router.post("/{booking_id}/cancel")
async def cancel_booking_endpoint(booking_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    booking = cancel_booking(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": "Booking canceled successfully", "booking": booking}

@router.post("/attendance", response_model=AttendanceResponse)
async def create_attendance_endpoint(attendance: AttendanceCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    booking = get_booking_by_id(db, attendance.booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return create_attendance(db, attendance)