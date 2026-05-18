@echo off
chcp 65001 >nul
echo ==========================================
echo   FitAI 一键部署脚本
echo   健身/瑜伽/教培 AI智能管理系统
echo ==========================================
echo.

:: 检查Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker未安装
    echo 请先安装Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker Compose未安装
    pause
    exit /b 1
)

echo [OK] Docker环境检查完成
echo.

:: 创建数据目录
echo [1/4] 创建数据目录...
if not exist "data\postgres" mkdir data\postgres
if not exist "data\redis" mkdir data\redis
if not exist "data\uploads" mkdir data\uploads
if not exist "logs" mkdir logs

:: 复制环境配置
if not exist ".env" (
    echo [2/4] 创建环境配置文件...
    copy .env.example .env >nul
    echo [提示] 请编辑 .env 文件配置您的参数
)

:: 启动服务
echo [3/4] 启动服务...
docker-compose up -d --build

:: 等待服务启动
echo [4/4] 等待服务启动...
timeout /t 10 /nobreak >nul

:: 检查服务状态
echo.
echo ==========================================
echo   服务状态检查
echo ==========================================
docker-compose ps

echo.
echo [OK] 部署完成！
echo.
echo 访问地址：
echo   - 管理后台: http://localhost
echo   - API服务:  http://localhost:8000
echo   - API文档:  http://localhost:8000/docs
echo.
echo 默认账号：admin / admin123
echo.
echo 常用命令：
echo   - 查看日志: docker-compose logs -f
echo   - 停止服务: docker-compose down
echo   - 重启服务: docker-compose restart
echo.
pause
