# Git Gitee 推送指南

## 第一步：在Gitee上创建仓库

1. 访问 https://gitee.com 并登录
2. 点击右上角 "+" 号，选择 "新建仓库"
3. 填写仓库信息：
   - 仓库名称：`fitai` 或 `fitness-management-system`
   - 路径：`fitai`（会自动生成）
   - 归属：选择你的个人账号或组织
   - 私有限制：建议选择"私有"（防止代码泄露）
   - 勾选"使用Readme初始化仓库"：否（我们已有代码）
   - 勾选"添加.gitignore"：Python
4. 点击"创建"

## 第二步：在本地初始化Git仓库

在项目根目录执行以下命令：

```bash
cd d:\fyglx

# 初始化Git仓库
git init

# 添加远程仓库（将下面的URL替换为你Gitee仓库的URL）
git remote add origin https://gitee.com/你的用户名/fitai.git

# 添加所有文件到暂存区
git add .

# 提交代码
git commit -m "Initial commit: FitAI商用级健身管理系统 v1.0

功能模块:
- 会员管理
- 课程管理
- 预约管理
- 教练管理
- 财务管理
- 数据分析
- AI智能助手
- 系统设置

技术栈:
- 后端: FastAPI + SQLAlchemy
- 前端: React + Ant Design
- 数据库: PostgreSQL
- 缓存: Redis
- 认证: JWT + RBAC
"

# 推送代码到Gitee
git push -u origin master
```

## 第三步：验证推送成功

1. 刷新Gitee仓库页面
2. 应该能看到所有文件已上传
3. 点击 README.md 预览

## 完整推送脚本

你可以创建一个一键推送脚本 `push.sh`：

```bash
#!/bin/bash

# 配置
GITEE_USERNAME="你的Gitee用户名"
REPO_NAME="fitai"

echo "开始推送代码到Gitee..."

# 初始化（如果是新项目）
if [ ! -d .git ]; then
    echo "初始化Git仓库..."
    git init
fi

# 配置用户信息（如果是首次）
git config user.name "Your Name"
git config user.email "your@email.com"

# 添加远程仓库
git remote remove origin 2>/dev/null
git remote add origin https://gitee.com/${GITEE_USERNAME}/${REPO_NAME}.git

# 添加文件
echo "添加文件到暂存区..."
git add .

# 提交
echo "提交代码..."
git commit -m "FitAI商用级健身管理系统 v1.0 - $(date +'%Y-%m-%d %H:%M:%S')"

# 推送
echo "推送到Gitee..."
git push -u origin master --force

echo "推送完成！"
```

## 常见问题

### Q1: 推送时提示需要登录
```
! [rejected] master -> master (fetch first)
```
解决方法：
```bash
git pull origin master --rebase
git push origin master
```

### Q2: 大文件导致推送失败
Gitee单文件限制50MB，需要先移除大文件：
```bash
# 查看大文件
git verify-pack -v .git/objects/pack/*.idx | sort -k 3 -n | tail -10

# 移除大文件
git filter-branch --tree-filter 'rm -f path/to/large-file' HEAD
```

### Q3: 中文文件名乱码
```bash
git config --global core.quotepath false
```

### Q4: 想要更新代码
```bash
# 编辑代码后
git add .
git commit -m "你的更新说明"
git push origin master
```

## Gitee仓库设置

创建仓库后，建议进行以下设置：

### 1. 添加协作者（可选）
- 仓库页面 -> 设置 -> 仓库成员管理
- 添加团队成员

### 2. 配置分支保护
- 设置 -> 分支 -> 添加保护分支
- master分支设置为"需要审核"（可选）

### 3. 启用issues
- 用于Bug反馈和功能请求

### 4. 配置Webhook（可选）
- 仓库页面 -> 设置 -> Webhooks
- 可以配置钉钉、企业微信等通知

## CI/CD 集成（可选）

如果你想自动部署，可以在Gitee上配置：

1. 访问 Gitee Go (流水线)
2. 创建流水线
3. 配置自动化测试和部署

示例流水线配置：
```yaml
# gitee.yml
name: Build and Deploy

on:
  push:
    branches:
      - master

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker Image
        run: |
          docker-compose build
          
      - name: Run Tests
        run: |
          docker-compose run backend pytest
          
      - name: Deploy
        if: success()
        run: |
          # 部署命令
          echo "部署到生产服务器"
```

## 备份建议

定期在本地备份Git仓库：
```bash
# 克隆仓库到本地备份
git clone --mirror https://gitee.com/你的用户名/fitai.git fitai-backup.git

# 定期更新备份
cd fitai-backup.git
git fetch --all
```

---

按照以上步骤操作，你的代码就会成功上传到Gitee！
