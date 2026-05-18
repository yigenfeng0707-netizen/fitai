@echo off
cd /d D:\fyglx
echo FitAI - Git Push Tool
echo.
echo Pushing to Gitee...
echo.
git add .
git commit -m "FitAI Fitness Management System v1.0"
git push -u origin master --force
echo.
echo Done!
pause
