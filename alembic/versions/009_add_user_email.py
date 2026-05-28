"""add user email field

Revision ID: 009_add_user_email
Revises: 008_add_campaign_and_automation
Create Date: 2026-05-28 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '009_add_user_email'
down_revision = '008_add_campaign_and_automation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(length=120), nullable=True))
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_column('users', 'email')
