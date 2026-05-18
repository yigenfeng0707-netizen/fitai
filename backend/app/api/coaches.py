from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.coach import get_coach_by_id, create_coach, update_coach, delete_coach, get_coaches, create_coach_schedule, get_coach_schedules, create_teaching_record, get_teaching_records
from app.schemas.coach import CoachCreate, CoachUpdate, CoachResponse, CoachScheduleCreate, CoachScheduleResponse, TeachingRecordCreate, TeachingRecordResponse
from app.auth.security import get_current_user

router = APIRouter()

@router.get("/", response_model=list[CoachResponse])
async def read_coaches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    coaches = get_coaches(db, skip=skip, limit=limit)
    return coaches

@router.get("/{coach_id}", response_model=CoachResponse)
async def read_coach(coach_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    coach = get_coach_by_id(db, coach_id)
    if coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return coach

@router.post("/", response_model=CoachResponse)
async def create_coach_endpoint(coach: CoachCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return create_coach(db, coach)

@router.put("/{coach_id}", response_model=CoachResponse)
async def update_coach_endpoint(coach_id: int, coach_update: CoachUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    coach = update_coach(db, coach_id, coach_update)
    if coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return coach

@router.delete("/{coach_id}", response_model=CoachResponse)
async def delete_coach_endpoint(coach_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    coach = delete_coach(db, coach_id)
    if coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return coach

@router.post("/{coach_id}/schedules", response_model=CoachScheduleResponse)
async def create_coach_schedule_endpoint(coach_id: int, schedule: CoachScheduleCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    coach = get_coach_by_id(db, coach_id)
    if coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return create_coach_schedule(db, schedule)

@router.get("/{coach_id}/schedules", response_model=list[CoachScheduleResponse])
async def read_coach_schedules(coach_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    coach = get_coach_by_id(db, coach_id)
    if coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return get_coach_schedules(db, coach_id)

@router.post("/{coach_id}/teaching-records", response_model=TeachingRecordResponse)
async def create_teaching_record_endpoint(coach_id: int, record: TeachingRecordCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    coach = get_coach_by_id(db, coach_id)
    if coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return create_teaching_record(db, record)

@router.get("/{coach_id}/teaching-records", response_model=list[TeachingRecordResponse])
async def read_teaching_records(coach_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    coach = get_coach_by_id(db, coach_id)
    if coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return get_teaching_records(db, coach_id)