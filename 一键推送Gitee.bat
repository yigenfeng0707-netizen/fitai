@echo off
chcp 65001 >nul
title FitAI - 一键推送到Gitee
color 0A

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║         FitAI 一键推送到Gitee                    ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: 切换到项目目录
cd /d "%~dp0"

:: 检查Git
echo [1/4] 检查Git环境...
git --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Git未安装！请先安装Git: https://git-scm.com
    pause
    exit /b 1
)
echo [OK] Git已安装
echo.

:: 检查是否有提交
echo [2/4] 检查代码提交状态...
git status >nul 2>&1
if errorlevel 1 (
    echo [错误] 不是Git仓库！
    pause
    exit /b 1
)
echo [OK] Git仓库正常
echo.

:: 显示待推送内容
echo [3/4] 待推送内容：
git log --oneline -3
echo.
echo 文件状态:
git status --short
echo.

:: 推送到Gitee
echo [4/4] 推送到Gitee...
echo.
echo 请确保已在Gitee创建仓库: https://gitee.com/fengyigen/fitai
echo 如果仓库不存在，请先创建！
echo.
echo 正在推送，请稍候...
echo.

:: 执行推送
git push -u origin master --force

echo.
if errorlevel 1 (
    echo ╔══════════════════════════════════════════════════╗
    echo ║  [失败] 推送失败！                                 ║
    echo ║  可能原因：                                        ║
    echo ║  1. 仓库不存在（请先在Gitee创建仓库）              ║
    echo ║  2. 需要登录认证                                    ║
    echo ║  3. 网络问题                                        ║
    echo ╚══════════════════════════════════════════════════╝
) else (
    echo ╔══════════════════════════════════════════════════╗
    echo ║  [成功] 代码已推送！                               ║
    echo ║                                                   ║
    echo ║  访问你的仓库: https://gitee.com/fengyigen/fitai  ║
    echo ╚══════════════════════════════════════════════════╝
)

echo.
pause
