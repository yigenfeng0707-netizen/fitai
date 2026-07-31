"""
CRUD - 门店
"""
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.store import Store
from backend.models.user_store import UserStore
from backend.schemas.store import StoreCreate, StoreUpdate


class StoreCRUD:
    """门店 CRUD"""

    @staticmethod
    async def create(db: AsyncSession, obj_in: StoreCreate, organization_id: int) -> Store:
        import uuid
        code = obj_in.code or uuid.uuid4().hex[:8].upper()
        store = Store(
            name=obj_in.name,
            code=code,
            address=obj_in.address,
            city=obj_in.city,
            district=obj_in.district,
            phone=obj_in.phone,
            manager_id=obj_in.manager_id,
            is_active=obj_in.is_active,
            business_hours=obj_in.business_hours,
            facilities=obj_in.facilities,
            max_capacity=obj_in.max_capacity,
            settings=obj_in.settings,
            longitude=obj_in.longitude,
            latitude=obj_in.latitude,
            organization_id=organization_id,
        )
        db.add(store)
        await db.flush()
        return store

    @staticmethod
    async def get(db: AsyncSession, store_id: int, organization_id: int) -> Optional[Store]:
        result = await db.execute(
            select(Store).where(Store.id == store_id, Store.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(db: AsyncSession, code: str, organization_id: int) -> Optional[Store]:
        result = await db.execute(
            select(Store).where(Store.code == code, Store.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_multi(
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Store], int]:
        query = select(Store).where(Store.organization_id == organization_id)
        if is_active is not None:
            query = query.where(Store.is_active == is_active)
        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()
        result = await db.execute(query.offset(skip).limit(limit).order_by(Store.created_at.desc()))
        return list(result.scalars().all()), total or 0

    @staticmethod
    async def update(db: AsyncSession, store: Store, obj_in: StoreUpdate) -> Store:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(store, field, value)
        await db.flush()
        return store

    @staticmethod
    async def delete(db: AsyncSession, store: Store) -> None:
        await db.delete(store)

    @staticmethod
    async def get_staff(
        db: AsyncSession, store_id: int, organization_id: int,
    ) -> list[dict]:
        query = (
            select(UserStore, Store)
            .join(Store, UserStore.store_id == Store.id)
            .where(UserStore.store_id == store_id, UserStore.organization_id == organization_id)
        )
        result = await db.execute(query)
        staff_list = []
        for row in result:
            us = row[0]
            staff_list.append({
                "user_id": us.user_id,
                "username": "",
                "role_at_store": us.role_at_store,
                "is_primary": us.is_primary,
                "joined_at": us.joined_at,
            })
        # Enrich with usernames
        from backend.models.auth import User
        for item in staff_list:
            user_result = await db.execute(select(User).where(User.id == item["user_id"]))
            user = user_result.scalar_one_or_none()
            if user:
                item["username"] = user.username
        return staff_list

    @staticmethod
    async def assign_staff(
        db: AsyncSession, store_id: int, user_id: int,
        role_at_store: Optional[str] = None, is_primary: bool = False,
        organization_id: int = 1,
    ) -> UserStore:
        existing = await db.execute(
            select(UserStore).where(
                UserStore.user_id == user_id,
                UserStore.store_id == store_id,
                UserStore.organization_id == organization_id,
            )
        )
        us = existing.scalar_one_or_none()
        if us:
            if role_at_store is not None:
                us.role_at_store = role_at_store
            if is_primary:
                us.is_primary = is_primary
            await db.flush()
            return us
        us = UserStore(
            user_id=user_id,
            store_id=store_id,
            role_at_store=role_at_store,
            is_primary=is_primary,
            organization_id=organization_id,
        )
        db.add(us)
        await db.flush()
        return us

    @staticmethod
    async def remove_staff(
        db: AsyncSession, store_id: int, user_id: int, organization_id: int,
    ) -> None:
        result = await db.execute(
            select(UserStore).where(
                UserStore.user_id == user_id,
                UserStore.store_id == store_id,
                UserStore.organization_id == organization_id,
            )
        )
        us = result.scalar_one_or_none()
        if us:
            await db.delete(us)

    @staticmethod
    async def get_staff_stores(
        db: AsyncSession, user_id: int, organization_id: int,
    ) -> list[Store]:
        query = (
            select(Store)
            .join(UserStore, UserStore.store_id == Store.id)
            .where(UserStore.user_id == user_id, UserStore.organization_id == organization_id)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def set_primary_store(
        db: AsyncSession, user_id: int, store_id: int, organization_id: int,
    ) -> None:
        # Clear existing primary
        result = await db.execute(
            select(UserStore).where(
                UserStore.user_id == user_id,
                UserStore.organization_id == organization_id,
                UserStore.is_primary.is_(True),
            )
        )
        for us in result.scalars().all():
            us.is_primary = False
        # Set new primary
        result = await db.execute(
            select(UserStore).where(
                UserStore.user_id == user_id,
                UserStore.store_id == store_id,
                UserStore.organization_id == organization_id,
            )
        )
        us = result.scalar_one_or_none()
        if us:
            us.is_primary = True
        await db.flush()
