"""add campaign and automation tables

Revision ID: 008_add_campaign_and_automation
Revises: 007_update_audit_logs
Create Date: 2026-05-28 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '008_add_campaign_and_automation'
down_revision = '007_update_audit_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # campaign status enum
    campaign_status = sa.Enum('draft', 'active', 'paused', 'completed', 'cancelled', name='campaignstatus')
    campaign_status.create(op.get_bind())

    # campaign channel enum
    campaign_channel = sa.Enum('sms', 'wechat', 'call', 'social', 'email', 'offline', name='campaignchannel')
    campaign_channel.create(op.get_bind())

    # automation trigger type enum
    trigger_type = sa.Enum(
        'member_created', 'card_expiring', 'booking_cancelled', 'lead_created',
        'lead_status_changed', 'member_inactive', 'birthday',
        name='automationtriggertype',
    )
    trigger_type.create(op.get_bind())

    # automation action type enum
    action_type = sa.Enum('send_notification', name='automationactiontype')
    action_type.create(op.get_bind())

    # campaigns table
    op.create_table('campaigns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('campaign_type', sa.String(length=50), nullable=False, server_default='promotion'),
        sa.Column('status', campaign_status, nullable=True, server_default='draft'),
        sa.Column('channels', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('target_audience', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('target_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('budget', sa.Float(), nullable=True, server_default='0'),
        sa.Column('actual_cost', sa.Float(), nullable=True, server_default='0'),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('sent_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('opened_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('converted_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('converted_revenue', sa.Float(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_campaigns_id'), 'campaigns', ['id'], unique=False)
    op.create_index(op.f('ix_campaigns_organization_id'), 'campaigns', ['organization_id'], unique=False)
    op.create_index(op.f('ix_campaigns_status'), 'campaigns', ['status'], unique=False)

    # automation_rules table
    op.create_table('automation_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('trigger_type', trigger_type, nullable=False),
        sa.Column('trigger_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('action_type', action_type, nullable=False),
        sa.Column('action_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('execution_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_executed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_automation_rules_id'), 'automation_rules', ['id'], unique=False)
    op.create_index(op.f('ix_automation_rules_organization_id'), 'automation_rules', ['organization_id'], unique=False)
    op.create_index(op.f('ix_automation_rules_is_active'), 'automation_rules', ['is_active'], unique=False)
    op.create_index(op.f('ix_automation_rules_trigger_type'), 'automation_rules', ['trigger_type'], unique=False)

    # automation_logs table
    op.create_table('automation_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('trigger_entity_type', sa.String(length=50), nullable=False),
        sa.Column('trigger_entity_id', sa.Integer(), nullable=True),
        sa.Column('action_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['rule_id'], ['automation_rules.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_automation_logs_id'), 'automation_logs', ['id'], unique=False)
    op.create_index(op.f('ix_automation_logs_organization_id'), 'automation_logs', ['organization_id'], unique=False)
    op.create_index(op.f('ix_automation_logs_rule_id'), 'automation_logs', ['rule_id'], unique=False)


def downgrade() -> None:
    op.drop_table('automation_logs')
    op.drop_table('automation_rules')
    op.drop_table('campaigns')

    sa.Enum(name='automationactiontype').drop(op.get_bind())
    sa.Enum(name='automationtriggertype').drop(op.get_bind())
    sa.Enum(name='campaignchannel').drop(op.get_bind())
    sa.Enum(name='campaignstatus').drop(op.get_bind())
