"""添加 AI 功能相关表

Revision ID: 003_add_ai_tables
Revises: 002_add_organizations
Create Date: 2026-05-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '003_add_ai_tables'
down_revision = '002_add_organizations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 体测记录表
    op.create_table('body_test_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('body_fat_percentage', sa.Float(), nullable=True),
        sa.Column('muscle_mass', sa.Float(), nullable=True),
        sa.Column('bmi', sa.Float(), nullable=True),
        sa.Column('bone_mass', sa.Float(), nullable=True),
        sa.Column('body_water', sa.Float(), nullable=True),
        sa.Column('visceral_fat', sa.Float(), nullable=True),
        sa.Column('basal_metabolism', sa.Float(), nullable=True),
        sa.Column('body_age', sa.Integer(), nullable=True),
        sa.Column('protein', sa.Float(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),

        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('operator_id', sa.Integer(), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_body_test_records_id'), 'body_test_records', ['id'])
    op.create_index(op.f('ix_body_test_records_member_id'), 'body_test_records', ['member_id'])
    op.create_index(op.f('ix_body_test_records_organization_id'), 'body_test_records', ['organization_id'])

    # AI 推荐记录表
    op.create_table('ai_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recommendation_type', sa.String(length=50), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        sa.Column('related_entity_type', sa.String(length=50), nullable=True),
        sa.Column('related_entity_id', sa.Integer(), nullable=True),

        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('action_url', sa.String(length=500), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),

        sa.Column('is_read', sa.Integer(), nullable=True),
        sa.Column('is_applied', sa.Integer(), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_recommendations_id'), 'ai_recommendations', ['id'])
    op.create_index(op.f('ix_ai_recommendations_recommendation_type'), 'ai_recommendations', ['recommendation_type'])
    op.create_index(op.f('ix_ai_recommendations_member_id'), 'ai_recommendations', ['member_id'])
    op.create_index(op.f('ix_ai_recommendations_organization_id'), 'ai_recommendations', ['organization_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_recommendations_organization_id'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_member_id'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_recommendation_type'), table_name='ai_recommendations')
    op.drop_index(op.f('ix_ai_recommendations_id'), table_name='ai_recommendations')
    op.drop_table('ai_recommendations')

    op.drop_index(op.f('ix_body_test_records_organization_id'), table_name='body_test_records')
    op.drop_index(op.f('ix_body_test_records_member_id'), table_name='body_test_records')
    op.drop_index(op.f('ix_body_test_records_id'), table_name='body_test_records')
    op.drop_table('body_test_records')
