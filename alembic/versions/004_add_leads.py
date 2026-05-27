"""添加潜客 CRM 表

Revision ID: 004_add_leads
Revises: 003_add_ai_tables
Create Date: 2026-05-27 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '004_add_leads'
down_revision = '003_add_ai_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('gender', sa.String(length=10), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('source', sa.Enum('CALL', 'VISIT', 'REFERRAL', 'AD', 'SOCIAL', 'OTHER', name='leadsource'), nullable=True),
        sa.Column('status', sa.Enum('NEW', 'CONTACTED', 'QUALIFIED', 'CONVERTED', 'LOST', name='leadstatus'), nullable=True),
        sa.Column('intent', sa.Enum('FITNESS', 'YOGA', 'TRAINING', 'REHAB', 'OTHER', name='leadintent'), nullable=True),

        sa.Column('expected_budget', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('follow_up_count', sa.Integer(), nullable=True),
        sa.Column('last_contacted_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('converted_member_id', sa.Integer(), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ),
        sa.ForeignKeyConstraint(['converted_member_id'], ['members.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_leads_id'), 'leads', ['id'])
    op.create_index(op.f('ix_leads_phone'), 'leads', ['phone'])
    op.create_index(op.f('ix_leads_status'), 'leads', ['status'])


def downgrade() -> None:
    op.drop_index(op.f('ix_leads_status'), table_name='leads')
    op.drop_index(op.f('ix_leads_phone'), table_name='leads')
    op.drop_index(op.f('ix_leads_id'), table_name='leads')
    op.drop_table('leads')
    op.execute('DROP TYPE IF EXISTS leadsource')
    op.execute('DROP TYPE IF EXISTS leadstatus')
    op.execute('DROP TYPE IF EXISTS leadintent')
