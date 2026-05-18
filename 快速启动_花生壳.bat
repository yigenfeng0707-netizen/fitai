@echo off
chcp 65001 >nul
echo ========================================
echo   FitAI - 快速启动脚本
echo ========================================
echo.

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python
    pause
    exit /b 1
)
echo [OK] Python已安装
echo.

echo [2/3] 切换到前端目录...
cd /d "%~dp0frontend\dist"
if not exist "FitAI-Standalone.html" (
    echo [错误] 未找到前端文件
    pause
    exit /b 1
)
echo [OK] 前端目录正确
echo.

echo [3/3] 启动HTTP服务器...
echo.
echo ========================================
echo   服务已启动！
echo ========================================
echo.
echo 本地访问地址:
echo   http://127.0.0.1:8080
echo.
echo 花生壳配置:
echo   内网端口: 8080
echo   内网IP:   127.0.0.1
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

python -m http.server 8080

pause
