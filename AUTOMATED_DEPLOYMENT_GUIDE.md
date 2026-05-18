# FitAI 自动化部署指南

## 目录

1. [方案概述](#方案概述)
2. [安全特性](#安全特性)
3. [快速开始](#快速开始)
4. [配置步骤](#配置步骤)
5. [部署方式](#部署方式)
6. [监控与维护](#监控与维护)
7. [故障排除](#故障排除)

---

## 方案概述

### 核心优势

- **🛡️ 安全可靠**：环境变量隔离、HTTPS 支持、密码加密
- **🔄 自动化部署**：GitHub Actions CI/CD，一键部署
- **📊 健康监控**：自动健康检查、故障自动恢复
- **🔒 权限隔离**：最小权限原则、密钥管理
- **📝 完整日志**：所有操作可追溯

### 技术架构

```
GitHub Repository
    ↓
GitHub Actions CI/CD Pipeline
    ↓
Docker Images (Backend + Frontend)
    ↓
Docker Compose (Production)
    ↓
Nginx Reverse Proxy
    ↓
Internet (HTTPS)
```

---

## 安全特性

### 1. 密钥管理

所有敏感信息通过 GitHub Secrets 管理：
- **DEPLOY_HOST**: 服务器地址
- **DEPLOY_USER**: SSH 用户名
- **DEPLOY_SSH_KEY**: SSH 私钥
- **DATABASE_URL**: 数据库连接字符串
- **SECRET_KEY**: 应用密钥

### 2. 网络安全

- Nginx 反向代理
- HTTPS 自动跳转
- API 限流保护
- CORS 配置

### 3. 容器安全

- 非 root 用户运行
- 只读文件系统（可选）
- 资源限制（CPU/内存）

---

## 快速开始

### 方式一：Zeabur 一键部署（推荐）

1. **访问 Zeabur**: https://zeabur.com
2. **登录**: 使用 GitHub 账号登录
3. **导入仓库**: 选择 `yigenfeng0707-netizen/fitai`
4. **添加数据库**: PostgreSQL
5. **配置环境变量**:
   ```
   DATABASE_URL=自动填充
   SECRET_KEY=随机生成的安全密钥
   DEEPSEEK_API_KEY=你的API密钥
   ```
6. **部署**: 点击 Deploy 按钮

### 方式二：传统服务器部署

```bash
# 1. 克隆仓库
git clone https://github.com/yigenfeng0707-netizen/fitai.git
cd fitai

# 2. 配置环境变量
cp .env.production .env
nano .env  # 修改密码和密钥

# 3. 一键部署
chmod +x deploy.sh
sudo ./deploy.sh
```

---

## 配置步骤

### 第一步：配置 GitHub Secrets

1. 打开 GitHub 仓库：https://github.com/yigenfeng0707-netizen/fitai/settings/secrets/actions
2. 添加以下 Secrets：

#### 必需
- `DEPLOY_HOST`: 你的服务器 IP 或域名
- `DEPLOY_USER`: 服务器用户名（如 `root`、`ubuntu`）
- `DEPLOY_SSH_KEY`: SSH 私钥

#### 可选（如果使用自动部署）
- `POSTGRES_PASSWORD`: 数据库密码
- `REDIS_PASSWORD`: Redis 密码
- `DEEPSEEK_API_KEY`: AI API 密钥

### 第二步：生成 SSH 密钥

```bash
# 在本地生成 SSH 密钥对
ssh-keygen -t ed25519 -C "fitai-deploy"

# 将公钥添加到服务器
ssh-copy-id user@your-server-ip

# 将私钥添加到 GitHub Secrets
cat ~/.ssh/id_ed25519
```

### 第三步：配置服务器

```bash
# 在服务器上安装 Docker 和 Docker Compose
curl -fsSL https://get.docker.com | sh
sudo systemctl start docker
sudo systemctl enable docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 创建应用目录
sudo mkdir -p /opt/fitai
sudo chown $USER:$USER /opt/fitai
```

---

## 部署方式

### 方式 1：自动部署（GitHub Actions）

```bash
# 1. 推送代码到 main 分支
git checkout main
git merge master
git push origin main

# 2. 或者手动触发部署
# 在 GitHub 仓库页面 → Actions → Deploy to Production → Run workflow
```

**优点**：
- ✅ 完全自动化
- ✅ 代码审查后部署
- ✅ 回滚简单

**缺点**：
- ⚠️ 需要配置服务器访问

### 方式 2：手动部署脚本

```bash
# 在服务器上执行
cd /opt/fitai
./deploy.sh
```

**优点**：
- ✅ 简单直接
- ✅ 可控制每一步

**缺点**：
- ⚠️ 需要手动操作

### 方式 3：Docker Compose 直接部署

```bash
# 构建镜像
docker-compose -f docker-compose.production.yml build

# 启动服务
docker-compose -f docker-compose.production.yml up -d

# 查看状态
docker-compose -f docker-compose.production.yml ps
```

---

## 监控与维护

### 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.production.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.production.yml logs -f backend

# 查看最近 100 行日志
docker-compose -f docker-compose.production.yml logs --tail=100
```

### 健康检查

```bash
# 检查服务状态
docker-compose -f docker-compose.production.yml ps

# 测试 API 健康端点
curl http://localhost:8000/health

# 检查数据库连接
docker exec fitai_postgres pg_isready -U fitai

# 检查 Redis 连接
docker exec fitai_redis redis-cli ping
```

### 备份数据

```bash
# 备份数据库
docker exec fitai_postgres pg_dump -U fitai fitai > backup_$(date +%Y%m%d).sql

# 备份 Redis
docker exec fitai_redis redis-cli SAVE

# 备份整个数据卷
docker run --rm -v fitai_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### 更新服务

```bash
# 方式 1：使用部署脚本
./deploy.sh

# 方式 2：手动更新
git pull origin master
docker-compose -f docker-compose.production.yml up -d --build

# 方式 3：使用 GitHub Actions
# 在 GitHub 仓库的 Actions 页面手动触发
```

### 回滚版本

```bash
# 查看容器历史
docker ps --filter "name=fitai_backend" --format "{{.ID}} {{.CreatedAt}}"

# 回滚到之前的镜像
docker-compose -f docker-compose.production.yml down
docker pull ghcr.io/yigenfeng0707-netizen/fitai-backend:previous-tag
docker-compose -f docker-compose.production.yml up -d
```

---

## 故障排除

### 常见问题

#### 1. 数据库连接失败

```bash
# 检查数据库状态
docker-compose -f docker-compose.production.yml logs postgres

# 重启数据库
docker-compose -f docker-compose.production.yml restart postgres

# 检查连接字符串
docker exec fitai_backend env | grep DATABASE
```

#### 2. 端口被占用

```bash
# 检查端口占用
netstat -tulpn | grep :80
netstat -tulpn | grep :443

# 修改端口映射
# 编辑 docker-compose.production.yml 中的 ports 配置
```

#### 3. 内存不足

```bash
# 检查 Docker 内存使用
docker stats

# 增加 Swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. SSL 证书问题

```bash
# 使用 Let's Encrypt 自动生成证书
docker-compose -f docker-compose.production.yml down
# 编辑 nginx/nginx.conf 添加 SSL 配置
docker-compose -f docker-compose.production.yml up -d
```

### 日志分析

```bash
# 查找错误
docker-compose -f docker-compose.production.yml logs | grep -i error

# 查找警告
docker-compose -f docker-compose.production.yml logs | grep -i warn

# 实时监控错误
docker-compose -f docker-compose.production.yml logs -f | grep -E "(ERROR|WARN)"
```

### 性能优化

```bash
# 1. 增加内存限制
# 编辑 docker-compose.production.yml 中的 deploy.resources.limits

# 2. 启用 Redis 缓存
# 确保 REDIS_URL 配置正确

# 3. 优化数据库
docker exec fitai_postgres psql -U fitai -c "VACUUM ANALYZE;"

# 4. 配置 Nginx 缓存
# 编辑 nginx/nginx.conf 添加缓存配置
```

---

## 安全建议

### 生产环境必做

1. ✅ 使用 HTTPS（Let's Encrypt）
2. ✅ 更改所有默认密码
3. ✅ 配置防火墙（仅开放 80/443 端口）
4. ✅ 启用 Docker 日志轮转
5. ✅ 定期更新系统和 Docker
6. ✅ 配置自动备份
7. ✅ 启用应用日志记录
8. ✅ 配置监控告警

### 定期维护

```bash
# 每周
- 检查日志错误
- 备份数据
- 检查磁盘空间

# 每月
- 更新 Docker 镜像
- 安全更新
- 性能评估

# 每季度
- 安全审计
- 灾难恢复演练
- 依赖项更新
```

---

## 联系方式

- **GitHub Issues**: https://github.com/yigenfeng0707-netizen/fitai/issues
- **技术支持**: support@fitai.example.com

---

**文档版本**: 1.0
**最后更新**: 2026-05-17
**维护者**: FitAI Team
