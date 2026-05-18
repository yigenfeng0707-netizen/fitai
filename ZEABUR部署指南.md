# FitAI - Zeabur 部署指南

## 🎯 为什么选择 Zeabur？

- ✅ **亚太节点**：香港、日本等节点，国内访问极快
- ✅ **支持 Gitee**：完美适配你的代码仓库
- ✅ **免费额度**：每月有免费部署额度
- ✅ **自动 HTTPS**：无需配置证书
- ✅ **简单易用**：5分钟部署完成

---

## 📝 部署步骤

### 第一步：准备 GitHub 仓库

由于 Zeabur 主要支持 GitHub，需要先把 Gitee 仓库同步到 GitHub：

1. 访问 https://github.com 注册账号（如果还没有）
2. 登录后访问：https://github.com/new/import
3. 填写信息：
   - **Your old repository's clone URL**: `https://gitee.com/fengyigen/fitai`
   - **Owner**: 选择你的 GitHub 用户名
   - **Repository name**: `fitai`
   - **Privacy**: 选择 **Public**（公开）
4. 点击 **Begin import** 等待同步完成

### 第二步：注册 Zeabur

1. 访问 https://zeabur.com
2. 点击 **Sign Up**
3. 使用 **GitHub** 账号登录（最方便）
4. 授权 Zeabur 访问你的 GitHub 仓库

### 第三步：创建项目

1. 在 Zeabur 控制台点击 **New Project**
2. 选择 **Deploy from GitHub repo**
3. 选择你刚同步的 `fitai` 仓库
4. Zeabur 会自动检测项目类型

### 第四步：配置环境变量

在 Zeabur 项目设置中添加以下环境变量：

```env
# 应用配置
APP_ENV=production
APP_DEBUG=false
APP_SECRET_KEY=your-super-secret-key-change-this

# 数据库（Zeabur会自动提供）
DATABASE_URL=${postgres.DATABASE_URL}

# Redis（Zeabur会自动提供）
REDIS_URL=${redis.REDIS_URL}

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=120

# AI服务（可选）
DEEPSEEK_API_KEY=your-api-key
```

### 第五步：添加数据库

1. 在项目中点击 **+**
2. 选择 **Add a service**
3. 选择 **PostgreSQL**
4. 选择区域：**Hong Kong** 或 **Singapore**（国内访问快）
5. 点击创建

### 第六步：添加 Redis（可选）

1. 再次点击 **+**
2. 选择 **Redis**
3. 选择区域：**Hong Kong**
4. 点击创建

### 第七步：部署

1. 点击 **Deploy**
2. 等待构建和部署完成（约3-5分钟）
3. 部署成功后，点击 **Generate Domain** 获取访问地址

---

## 🌐 访问你的应用

部署完成后，你会获得一个免费域名：
```
https://fitai-xxxx.zeabur.app
```

你可以用这个地址访问你的系统！

---

## 🔧 自定义域名（可选）

如果你有自己的域名：

1. 在 Zeabur 项目设置中点击 **Domains**
2. 点击 **Add Domain**
3. 输入你的域名
4. 在你的域名 DNS 中添加 CNAME 记录指向 Zeabur

---

## 💰 费用说明

- ** Hobby 计划**：免费
  - 每月 100GB 流量
  - 512MB 内存
  - 10GB 存储
- **Pro 计划**：$5/月起
  - 无限流量
  - 更多资源

对于公测，Hobby 计划足够使用！

---

## 🚀 国内访问速度测试

部署完成后，可以用以下工具测试访问速度：
- https://ping.pe/ （检测全球节点）
- https://www.webkaka.com/ping.aspx （国内测速）

---

## 🔧 常见问题

### Q1: 部署失败怎么办？
检查日志：
1. 点击失败的服务
2. 查看 Logs 标签
3. 根据错误信息调整配置

### Q2: 数据库连接失败？
确保：
1. 环境变量 `DATABASE_URL` 正确
2. 数据库已创建并运行
3. 尝试重启服务

### Q3: 如何更新代码？
只需推送到 GitHub，Zeabur 会自动重新部署！

---

## 📞 获取帮助

- Zeabur 文档：https://zeabur.com/docs
- GitHub Issues：https://github.com/zeabur/zeabur

---

**部署完成后，记得测试国内访问速度！** 🚀
