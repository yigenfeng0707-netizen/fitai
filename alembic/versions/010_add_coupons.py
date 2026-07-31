"""add coupons tables

Revision ID: 010_add_coupons
Revises: 009_add_user_email
Create Date: 2026-05-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '010_add_coupons'
down_revision = '009_add_user_email'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('coupons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('coupon_type', sa.String(length=20), nullable=False, server_default='fixed'),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('min_amount', sa.Float(), nullable=True, server_default='0'),
        sa.Column('max_discount', sa.Float(), nullable=True),
        sa.Column('total_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('used_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_coupons_id'), 'coupons', ['id'], unique=False)
    op.create_index(op.f('ix_coupons_organization_id'), 'coupons', ['organization_id'], unique=False)
    op.create_index(op.f('ix_coupons_is_active'), 'coupons', ['is_active'], unique=False)

    op.create_table('coupon_usages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('coupon_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('discount_amount', sa.Float(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_coupon_usages_id'), 'coupon_usages', ['id'], unique=False)
    op.create_index(op.f('ix_coupon_usages_coupon_id'), 'coupon_usages', ['coupon_id'], unique=False)
    op.create_index(op.f('ix_coupon_usages_member_id'), 'coupon_usages', ['member_id'], unique=False)


def downgrade() -> None:
    op.drop_table('coupon_usages')
    op.drop_table('coupons')
