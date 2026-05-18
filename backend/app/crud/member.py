from sqlalchemy.orm import Session
from app.models.member import Member, MemberCard, BodyTestRecord, MemberLevel
from app.schemas.member import MemberCreate, MemberUpdate, MemberCardCreate, BodyTestRecordCreate
from datetime import datetime
import uuid

def generate_member_no() -> str:
    return "M" + datetime.now().strftime("%Y%m%d") + str(uuid.uuid4())[:4].upper()

def get_member_by_id(db: Session, member_id: int):
    return db.query(Member).filter(Member.id == member_id).first()

def get_member_by_phone(db: Session, phone: str):
    return db.query(Member).filter(Member.phone == phone).first()

def get_members(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Member).offset(skip).limit(limit).all()

def create_member(db: Session, member: MemberCreate):
    member_no = generate_member_no()
    db_member = Member(
        member_no=member_no,
        name=member.name,
        phone=member.phone,
        email=member.email,
        avatar=member.avatar,
        level_id=member.level_id,
        points=member.points,
        tags=member.tags,
        notes=member.notes
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

def update_member(db: Session, member_id: int, member_update: MemberUpdate):
    db_member = get_member_by_id(db, member_id)
    if db_member:
        for key, value in member_update.model_dump(exclude_unset=True).items():
            setattr(db_member, key, value)
        db.commit()
        db.refresh(db_member)
    return db_member

def delete_member(db: Session, member_id: int):
    db_member = get_member_by_id(db, member_id)
    if db_member:
        db.delete(db_member)
        db.commit()
    return db_member

def create_member_card(db: Session, member_id: int, card: MemberCardCreate):
    db_card = MemberCard(
        card_no=card.card_no,
        member_id=member_id,
        card_type=card.card_type,
        total_hours=card.total_hours,
        balance=card.balance,
        start_date=card.start_date,
        end_date=card.end_date
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

def get_member_cards(db: Session, member_id: int):
    return db.query(MemberCard).filter(MemberCard.member_id == member_id).all()

def create_body_test_record(db: Session, member_id: int, record: BodyTestRecordCreate):
    db_record = BodyTestRecord(
        member_id=member_id,
        test_date=record.test_date,
        height=record.height,
        weight=record.weight,
        body_fat_rate=record.body_fat_rate,
        muscle_rate=record.muscle_rate,
        bmi=record.bmi,
        waist=record.waist,
        hip=record.hip,
        notes=record.notes
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_body_test_records(db: Session, member_id: int):
    return db.query(BodyTestRecord).filter(BodyTestRecord.member_id == member_id).all()