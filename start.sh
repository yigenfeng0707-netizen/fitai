#!/bin/bash
# 健身瑜伽教培管理系统 - 快速启动脚本

set -e

echo "🚀 健身瑜伽教培管理系统 - 快速启动"
echo "===================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装"
    exit 1
fi

# 创建环境变量文件
if [ ! -f .env ]; then
    echo "📝 创建 .env 文件..."
    cp .env.example .env
    echo "⚠️  请检查并修改 .env 文件中的配置"
fi

# 启动服务
echo "🐳 启动 Docker 容器..."
docker-compose up -d

# 等待数据库就绪
echo "⏳ 等待数据库就绪..."
sleep 5

# 执行数据库迁移
echo "📊 执行数据库迁移..."
docker-compose exec -T backend alembic upgrade head

echo ""
echo "✅ 启动完成!"
echo ""
echo "📍 访问地址:"
echo "   后端 API: http://localhost:8000"
echo "   API 文档: http://localhost:8000/docs"
echo "   前端:    http://localhost:3000 (需要启动前端容器)"
echo ""
echo "🔑 默认管理员账号:"
echo "   用户名: admin"
echo "   密码: admin123 (请在登录后修改)"
echo ""
echo "📖 常用命令:"
echo "   查看日志:    docker-compose logs -f"
echo "   停止服务:    docker-compose down"
echo "   重启服务:    docker-compose restart"
echo "   数据库 Shell: docker-compose exec postgres psql -U fituser -d fit_saas"