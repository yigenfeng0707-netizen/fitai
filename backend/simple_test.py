print("Test 1: Importing basic modules")
import sys
import os
print("OK")

print("Test 2: Setting path")
os.chdir('d:/fyglx/backend')
sys.path.insert(0, '.')
print("OK")

print("Test 3: Importing FastAPI")
from fastapi import FastAPI
print("OK")

print("Test 4: Importing settings")
from app.settings import settings
print("Settings:", settings.project_name)

print("Test 5: Importing database")
from app.database import engine, Base
print("OK")

print("Test 6: Creating tables")
Base.metadata.create_all(bind=engine)
print("OK")

print("Test 7: Importing router")
from app.api import router
print("OK")

print("Test 8: Creating app")
app = FastAPI(title=settings.project_name)
app.include_router(router, prefix="/api/v1")
print("OK")

print("\nAll tests passed!")