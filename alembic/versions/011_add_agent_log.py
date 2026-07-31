"""add agent interaction log table

Revision ID: 011_add_agent_log
Revises: 010_add_coupons
Create Date: 2026-07-31 00:00:00.000000

Creates the agent_interaction_log table to store Agent chat history,
tool calls, and iteration metadata for long-term memory and audit.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '011_add_agent_log'
down_revision = '010_add_coupons'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'agent_interaction_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False, comment='Tenant isolation'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='User who initiated the interaction'),
        sa.Column('member_id', sa.Integer(), nullable=True, comment='Related member ID for context'),
        sa.Column('persona', sa.String(50), nullable=True, comment='Agent persona used'),
        sa.Column('user_input', sa.Text(), nullable=False, comment='User natural language input'),
        sa.Column('agent_answer', sa.Text(), nullable=True, comment='Agent final response'),
        sa.Column('tool_calls', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                  comment='JSON array of tool call records'),
        sa.Column('iterations', sa.Integer(), nullable=True, comment='Number of ReAct loop iterations'),
        sa.Column('model', sa.String(100), nullable=True, comment='LLM model used'),
        sa.Column('tokens_used', sa.Integer(), nullable=True, comment='Total tokens consumed'),
        sa.Column('latency_ms', sa.Integer(), nullable=True, comment='Response time in milliseconds'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_log_org_created', 'agent_interaction_log',
                    ['organization_id', 'created_at'])
    op.create_index('ix_agent_log_member', 'agent_interaction_log',
                    ['organization_id', 'member_id'])
    op.create_index('ix_agent_log_persona', 'agent_interaction_log',
                    ['organization_id', 'persona'])


def downgrade() -> None:
    op.drop_index('ix_agent_log_persona', table_name='agent_interaction_log')
    op.drop_index('ix_agent_log_member', table_name='agent_interaction_log')
    op.drop_index('ix_agent_log_org_created', table_name='agent_interaction_log')
    op.drop_table('agent_interaction_log')
