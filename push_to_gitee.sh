#!/bin/bash

# FitAI - 一键推送到Gitee (Linux/Mac版)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  FitAI - 一键推送到Gitee"
echo "========================================"
echo ""

# 检查Git是否安装
if ! command -v git &> /dev/null; then
    echo -e "${RED}[错误] Git未安装！${NC}"
    echo "请先安装Git: https://git-scm.com"
    exit 1
fi

# 检查是否在项目目录
if [ ! -d "backend" ]; then
    echo -e "${RED}[错误] 请在项目根目录运行此脚本！${NC}"
    echo "当前目录: $(pwd)"
    exit 1
fi

# 获取Gitee用户名和仓库名
read -p "请输入你的Gitee用户名: " GITEE_USERNAME
read -p "请输入仓库名称(留空默认fitai): " REPO_NAME
REPO_NAME=${REPO_NAME:-fitai}

echo ""
echo "========================================"
echo "  配置信息"
echo "========================================"
echo "  Gitee用户名: $GITEE_USERNAME"
echo "  仓库名称: $REPO_NAME"
echo "========================================"
echo ""

# 配置Git用户信息
echo "请配置Git用户信息（首次使用需要）:"
read -p "你的名字: " GIT_NAME
read -p "你的邮箱: " GIT_EMAIL

git config user.name "$GIT_NAME"
git config user.email "$GIT_EMAIL"

# 初始化Git仓库
echo ""
echo -e "${YELLOW}[1/5] 初始化Git仓库...${NC}"
if [ ! -d ".git" ]; then
    git init
else
    echo "Git仓库已存在，跳过初始化"
fi

# 添加远程仓库
echo ""
echo -e "${YELLOW}[2/5] 配置远程仓库...${NC}"
git remote remove origin > /dev/null 2>&1
git remote add origin "https://gitee.com/$GITEE_USERNAME/$REPO_NAME.git"

# 添加文件到暂存区
echo ""
echo -e "${YELLOW}[3/5] 添加文件到暂存区...${NC}"
git add .

# 提交代码
echo ""
echo -e "${YELLOW}[4/5] 提交代码...${NC}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
git commit -m "FitAI商用级健身管理系统 v1.0 - $TIMESTAMP"

# 推送到Gitee
echo ""
echo -e "${YELLOW}[5/5] 推送到Gitee...${NC}"
echo ""
echo "提示: 如果是首次推送，可能需要输入Gitee用户名和密码（或Access Token）"
echo ""

git push -u origin master --force

echo ""
echo "========================================"
echo -e "${GREEN}  推送完成！${NC}"
echo "========================================"
echo ""
echo "请访问以下链接查看你的仓库:"
echo -e "${GREEN}https://gitee.com/$GITEE_USERNAME/$REPO_NAME${NC}"
echo ""
