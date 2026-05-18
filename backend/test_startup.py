import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("Testing startup...")

try:
    print("1. Importing settings...")
    from app.settings import settings
    print("   OK - Settings loaded: %s v%s" % (settings.project_name, settings.project_version))
except Exception as e:
    print("   ERROR -", str(e))
    sys.exit(1)

try:
    print("2. Creating database engine...")
    from app.database import engine, Base
    print("   OK - Database engine created")
except Exception as e:
    print("   ERROR -", str(e))
    sys.exit(1)

try:
    print("3. Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("   OK - Tables created")
except Exception as e:
    print("   ERROR -", str(e))
    sys.exit(1)

try:
    print("4. Importing API router...")
    from app.api import router
    print("   OK - Router imported")
except Exception as e:
    print("   ERROR -", str(e))
    sys.exit(1)

try:
    print("5. Creating FastAPI app...")
    from fastapi import FastAPI
    app = FastAPI(title=settings.project_name, version=settings.project_version)
    app.include_router(router, prefix="/api/v1")
    print("   OK - App created")
except Exception as e:
    print("   ERROR -", str(e))
    sys.exit(1)

print("\nAll checks passed! Service is ready to start.")
print("Database:", settings.database_url)
print("API docs: http://localhost:8000/docs")