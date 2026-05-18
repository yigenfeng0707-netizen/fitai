@echo off
chcp 65001 >nul
echo ==========================================
echo   FitAI 智能健身管理系统 - 启动脚本
echo ==========================================
echo.

:: 启动前端服务
echo [1/2] 启动前端服务...
start "FitAI前端" cmd /k "cd /d d:\fyglx\frontend\dist && python -m http.server 80"

:: 等待2秒
timeout /t 2 /nobreak >nul

:: 启动后端服务
echo [2/2] 启动后端服务...
start "FitAI后端" cmd /k "cd /d d:\fyglx\backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

:: 等待服务启动
echo.
echo 等待服务启动...
timeout /t 5 /nobreak >nul

:: 检查服务状态
echo.
echo ==========================================
echo   检查服务状态
echo ==========================================
netstat -ano | findstr ":80 " | findstr LISTENING
netstat -ano | findstr ":8000 " | findstr LISTENING

echo.
echo ==========================================
echo   启动完成！
echo ==========================================
echo.
echo 请在浏览器中访问：
echo   - 管理后台: http://localhost
echo   - API文档: http://localhost:8000/docs
echo.
echo 测试账号：admin / admin123
echo.
pause
