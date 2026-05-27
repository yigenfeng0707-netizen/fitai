"""添加会员卡交易记录表

Revision ID: 005_add_card_transactions
Revises: 004_add_leads
Create Date: 2026-05-27 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '005_add_card_transactions'
down_revision = '004_add_leads'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('card_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.Enum('recharge', 'renew', 'upgrade', 'consume', 'refund', 'freeze', 'unfreeze', name='transactiontype'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('count_change', sa.Integer(), nullable=True),
        sa.Column('balance_before', sa.Float(), nullable=True),
        sa.Column('balance_after', sa.Float(), nullable=True),
        sa.Column('count_before', sa.Integer(), nullable=True),
        sa.Column('count_after', sa.Integer(), nullable=True),
        sa.Column('card_type_before', sa.String(20), nullable=True),
        sa.Column('card_type_after', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('operator_id', sa.Integer(), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_card_transactions_id'), 'card_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_card_transactions_member_id'), 'card_transactions', ['member_id'], unique=False)
    op.create_index(op.f('ix_card_transactions_organization_id'), 'card_transactions', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_card_transactions_organization_id'), table_name='card_transactions')
    op.drop_index(op.f('ix_card_transactions_member_id'), table_name='card_transactions')
    op.drop_index(op.f('ix_card_transactions_id'), table_name='card_transactions')
    op.drop_table('card_transactions')
