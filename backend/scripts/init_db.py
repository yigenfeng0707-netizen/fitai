from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import Role, User
from app.models.member import MemberLevel
from app.settings import settings
from app.crud.user import get_password_hash

engine = create_engine(settings.database_url_local)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        if not db.query(Role).first():
            roles = [
                {"id": 1, "name": "superadmin", "description": "超级管理员", "permissions": "all"},
                {"id": 2, "name": "admin", "description": "店长/老板", "permissions": "member,booking,course,coach"},
                {"id": 3, "name": "frontdesk", "description": "前台", "permissions": "member,booking"},
                {"id": 4, "name": "coach", "description": "教练", "permissions": "booking"},
                {"id": 5, "name": "finance", "description": "财务", "permissions": "finance"}
            ]
            for role_data in roles:
                role = Role(**role_data)
                db.add(role)
            db.commit()
        
        if not db.query(MemberLevel).first():
            levels = [
                {"id": 1, "name": "普通会员", "min_points": 0, "discount": 1.0},
                {"id": 2, "name": "银卡会员", "min_points": 1000, "discount": 0.95},
                {"id": 3, "name": "金卡会员", "min_points": 5000, "discount": 0.9},
                {"id": 4, "name": "钻石会员", "min_points": 10000, "discount": 0.85}
            ]
            for level_data in levels:
                level = MemberLevel(**level_data)
                db.add(level)
            db.commit()
        
        if not db.query(User).filter(User.username == "admin").first():
            admin_user = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                name="超级管理员",
                role_id=1,
                store_id=1
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created: username=admin, password=admin123")
        
        print("Database initialization completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()