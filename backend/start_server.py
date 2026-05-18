import uvicorn
import sys

try:
    from app.main import app
    print("✅ App imported successfully")
    
    print("🚀 Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)