from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.member import get_member_by_id, get_member_by_phone, create_member, update_member, delete_member, get_members, create_member_card, get_member_cards, create_body_test_record, get_body_test_records
from app.schemas.member import MemberCreate, MemberUpdate, MemberResponse, MemberCardCreate, MemberCardResponse, BodyTestRecordCreate, BodyTestRecordResponse
from app.auth.security import get_current_user

router = APIRouter()

@router.get("/", response_model=list[MemberResponse])
async def read_members(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    members = get_members(db, skip=skip, limit=limit)
    return members

@router.get("/{member_id}", response_model=MemberResponse)
async def read_member(member_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    member = get_member_by_id(db, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

@router.post("/", response_model=MemberResponse)
async def create_member_endpoint(member: MemberCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_member = get_member_by_phone(db, phone=member.phone)
    if db_member:
        raise HTTPException(status_code=400, detail="Member with this phone already exists")
    return create_member(db, member)

@router.put("/{member_id}", response_model=MemberResponse)
async def update_member_endpoint(member_id: int, member_update: MemberUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    member = update_member(db, member_id, member_update)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

@router.delete("/{member_id}", response_model=MemberResponse)
async def delete_member_endpoint(member_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    member = delete_member(db, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

@router.post("/{member_id}/cards", response_model=MemberCardResponse)
async def create_member_card_endpoint(member_id: int, card: MemberCardCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    member = get_member_by_id(db, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return create_member_card(db, member_id, card)

@router.get("/{member_id}/cards", response_model=list[MemberCardResponse])
async def get_member_cards_endpoint(member_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    member = get_member_by_id(db, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return get_member_cards(db, member_id)

@router.post("/{member_id}/body-tests", response_model=BodyTestRecordResponse)
async def create_body_test_record_endpoint(member_id: int, record: BodyTestRecordCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    member = get_member_by_id(db, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return create_body_test_record(db, member_id, record)

@router.get("/{member_id}/body-tests", response_model=list[BodyTestRecordResponse])
async def get_body_test_records_endpoint(member_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    member = get_member_by_id(db, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return get_body_test_records(db, member_id)