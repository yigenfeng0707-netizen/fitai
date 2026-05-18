#!/usr/bin/env python3
import sys
import os

 # 加力 backend 目幕到一 Python 迭深
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)