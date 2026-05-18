import sys
sys.path.insert(0, '.')

try:
    from app.main import app
    import uvicorn
    
    print("Starting FitAI API Service...")
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
except Exception as e:
    print("Error:", str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)