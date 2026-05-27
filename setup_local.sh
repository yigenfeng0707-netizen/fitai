#!/bin/bash
# 本地开发环境设置脚本

set -e

echo "📦 安装 Python 依赖..."

# 创建虚拟环境
python3 -m venv venv || {
    echo "⚠️  venv 不可用，使用系统 Python"
}

# 安装依赖
if [ -d "venv" ]; then
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ 依赖安装完成"
echo ""
echo "📝 下一步:"
echo "   1. 安装 PostgreSQL (如果未安装): sudo apt install postgresql postgresql-contrib"
echo "   2. 创建数据库: sudo -u postgres psql -c \"CREATE USER fituser WITH PASSWORD 'fitpass123';\""
echo "   3. 创建数据库: sudo -u postgres psql -c \"CREATE DATABASE fit_saas OWNER fituser;\""
echo "   4. 运行迁移: alembic upgrade head"
echo "   5. 启动服务: uvicorn backend.main:app --reload"