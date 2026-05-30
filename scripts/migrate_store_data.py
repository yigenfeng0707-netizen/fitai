"""
数据迁移脚本：单门店 → 多门店
将现有数据关联到默认门店
"""
import asyncio
from sqlalchemy import text
from backend.database import async_engine, AsyncSessionLocal

async def migrate():
    async with async_engine.begin() as conn:
        # 1. Create default store for each organization
        await conn.execute(text("""
            INSERT INTO stores (name, code, organization_id, is_active, created_at, updated_at)
            SELECT '默认门店', 'DEFAULT', id, true, NOW(), NOW()
            FROM organizations
            WHERE NOT EXISTS (SELECT 1 FROM stores WHERE code = 'DEFAULT' AND stores.organization_id = organizations.id)
        """))

        # 2. Set store_id on members without store
        await conn.execute(text("""
            UPDATE members SET store_id = (
                SELECT s.id FROM stores s WHERE s.organization_id = members.organization_id AND s.code = 'DEFAULT'
            ) WHERE store_id IS NULL
        """))

        # 3. Set store_id on coaches
        await conn.execute(text("""
            UPDATE coaches SET store_id = (
                SELECT s.id FROM stores s WHERE s.organization_id = coaches.organization_id AND s.code = 'DEFAULT'
            ) WHERE store_id IS NULL
        """))

        # 4. Set store_id on bookings
        await conn.execute(text("""
            UPDATE bookings SET store_id = (
                SELECT s.id FROM stores s WHERE s.organization_id = bookings.organization_id AND s.code = 'DEFAULT'
            ) WHERE store_id IS NULL
        """))

        # 5. Set store_id on orders
        await conn.execute(text("""
            UPDATE orders SET store_id = (
                SELECT s.id FROM stores s WHERE s.organization_id = orders.organization_id AND s.code = 'DEFAULT'
            ) WHERE store_id IS NULL
        """))

        # 6. Set store_id on course_schedules
        await conn.execute(text("""
            UPDATE course_schedules SET store_id = (
                SELECT s.id FROM stores s WHERE s.organization_id = course_schedules.organization_id AND s.code = 'DEFAULT'
            ) WHERE store_id IS NULL
        """))

        # 7. Set store_id on leads
        await conn.execute(text("""
            UPDATE leads SET store_id = (
                SELECT s.id FROM stores s WHERE s.organization_id = leads.organization_id AND s.code = 'DEFAULT'
            ) WHERE store_id IS NULL
        """))

        # 8. Set store_id on card_transactions
        await conn.execute(text("""
            UPDATE card_transactions SET store_id = (
                SELECT s.id FROM stores s WHERE s.organization_id = card_transactions.organization_id AND s.code = 'DEFAULT'
            ) WHERE store_id IS NULL
        """))

        print("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate())
