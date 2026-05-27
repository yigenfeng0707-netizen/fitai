"""更新审计日志表字段类型

Revision ID: 007_update_audit_logs
Revises: 006_add_notifications
Create Date: 2026-05-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '007_update_audit_logs'
down_revision = '006_add_notifications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('audit_logs', sa.Column('detail', sa.Text(), nullable=True))
    op.alter_column('audit_logs', 'old_value',
                    existing_type=sa.String(length=500),
                    type_=postgresql.JSON(astext_type=sa.Text()),
                    postgresql_using='old_value::json')
    op.alter_column('audit_logs', 'new_value',
                    existing_type=sa.String(length=500),
                    type_=postgresql.JSON(astext_type=sa.Text()),
                    postgresql_using='new_value::json')


def downgrade() -> None:
    op.alter_column('audit_logs', 'new_value',
                    existing_type=postgresql.JSON(astext_type=sa.Text()),
                    type_=sa.String(length=500))
    op.alter_column('audit_logs', 'old_value',
                    existing_type=postgresql.JSON(astext_type=sa.Text()),
                    type_=sa.String(length=500))
    op.drop_column('audit_logs', 'detail')
