@echo off
chcp 65001 >nul
echo ========================================
echo   FitAI - 一键推送到Gitee
echo ========================================
echo.

:: 检查Git是否安装
git --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Git未安装！
    echo 请先安装Git: https://git-scm.com/download/win
    pause
    exit /b 1
)

:: 检查是否在项目目录
if not exist "backend" (
    echo [错误] 请在项目根目录运行此脚本！
    echo 当前目录: %CD%
    pause
    exit /b 1
)

:: 获取Gitee用户名和仓库名
set /p GITEE_USERNAME="请输入你的Gitee用户名: "
set /p REPO_NAME="请输入仓库名称(留空默认fitai): "

if "%REPO_NAME%"=="" set REPO_NAME=fitai

echo.
echo ========================================
echo   配置信息
echo ========================================
echo   Gitee用户名: %GITEE_USERNAME%
echo   仓库名称: %REPO_NAME%
echo ========================================
echo.

:: 配置Git用户信息
echo 请配置Git用户信息（首次使用需要）:
set /p GIT_NAME="你的名字: "
set /p GIT_EMAIL="你的邮箱: "

git config user.name "%GIT_NAME%"
git config user.email "%GIT_EMAIL%"

:: 初始化Git仓库
echo.
echo [1/5] 初始化Git仓库...
if not exist ".git" (
    git init
) else (
    echo Git仓库已存在，跳过初始化
)

:: 添加远程仓库
echo.
echo [2/5] 配置远程仓库...
git remote remove origin >nul 2>&1
git remote add origin https://gitee.com/%GITEE_USERNAME%/%REPO_NAME%.git

:: 添加文件到暂存区
echo.
echo [3/5] 添加文件到暂存区...
git add .

:: 提交代码
echo.
echo [4/5] 提交代码...
git commit -m "FitAI商用级健身管理系统 v1.0 - %date% %time%"

:: 推送到Gitee
echo.
echo [5/5] 推送到Gitee...
echo.
echo 提示: 如果是首次推送，可能需要输入Gitee用户名和密码
echo.

git push -u origin master --force

echo.
echo ========================================
echo   推送完成！
echo ========================================
echo.
echo 请访问以下链接查看你的仓库:
echo https://gitee.com/%GITEE_USERNAME%/%REPO_NAME%
echo.
pause
