#!/bin/bash
# 创建初始管理员账号

docker-compose exec -T backend python -c "
from backend.database import init_db, AsyncSessionLocal
from backend.models.auth import User
from backend.core.security import get_password_hash
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as db:
        # 检查是否已存在
        result = await db.execute(
            'SELECT 1 FROM users WHERE username = \"admin\"'
        )
        if result.fetchone():
            print('管理员账号已存在')
            return
        
        # 创建管理员
        from sqlalchemy import text
        await db.execute(text('''
            INSERT INTO users (username, password_hash, role, is_superuser, is_active)
            VALUES ('admin', :pwd, 'super_admin', true, true)
        '''), {'pwd': get_password_hash('admin123')})
        await db.commit()
        print('✅ 管理员账号创建成功')
        print('   用户名: admin')
        print('   密码: admin123')

asyncio.run(create_admin())
"