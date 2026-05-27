"""添加多租户组织和订单表

Revision ID: 002_add_organizations
Revises: 001_initial
Create Date: 2026-05-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_add_organizations'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 organizations 表
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('plan', sa.String(length=20), nullable=False, server_default='trial'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('contact_name', sa.String(length=50), nullable=True),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('contact_email', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # 插入默认组织
    op.execute(
        """
        INSERT INTO organizations (id, name, slug, plan, status, is_active, created_at, updated_at)
        VALUES (1, '默认组织', 'default', 'trial', 'active', true, now(), now())
        """
    )

    # 重置序列起始值
    op.execute("SELECT setval('organizations_id_seq', 2, false)")

    # 为所有业务表添加 organization_id 列
    tables = ['members', 'coaches', 'courses', 'course_schedules', 'bookings', 'users', 'audit_logs']
    for table in tables:
        op.add_column(
            table,
            sa.Column('organization_id', sa.Integer(), nullable=False, server_default='1')
        )
        op.create_foreign_key(
            f'fk_{table}_organization',
            table, 'organizations',
            ['organization_id'], ['id']
        )
        op.create_index(
            op.f(f'ix_{table}_organization_id'),
            table, ['organization_id'],
            unique=False
        )

    # 创建 orders 表（Phase 2 预留）
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_no', sa.String(length=30), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('discount', sa.Float(), nullable=True, server_default='0'),
        sa.Column('actual_amount', sa.Float(), nullable=False),
        sa.Column('payment_method', sa.String(length=20), nullable=True),
        sa.Column('payment_status', sa.String(length=20), nullable=True, server_default='pending'),
        sa.Column('transaction_id', sa.String(length=100), nullable=True),
        sa.Column('product_type', sa.String(length=20), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_order_no'), 'orders', ['order_no'], unique=True)
    op.create_foreign_key('fk_orders_member', 'orders', 'members', ['member_id'], ['id'])
    op.create_foreign_key('fk_orders_organization', 'orders', 'organizations', ['organization_id'], ['id'])
    op.create_index(op.f('ix_orders_organization_id'), 'orders', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_table('orders')
    tables = ['members', 'coaches', 'courses', 'course_schedules', 'bookings', 'users', 'audit_logs']
    for table in reversed(tables):
        op.drop_index(op.f(f'ix_{table}_organization_id'), table_name=table)
        op.drop_constraint(f'fk_{table}_organization', table, type_='foreignkey')
        op.drop_column(table, 'organization_id')
    op.drop_table('organizations')
