"""生成初始数据库迁移

Revision ID: 001_initial
Revises: 
Create Date: 2026-05-09 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级迁移 - 创建所有表"""
    
    # 创建枚举类型
    card_type_enum = postgresql.ENUM('single', 'monthly', 'quarterly', 'yearly', 'stored', name='cardtype')
    card_type_enum.create(op.get_bind())
    
    member_status_enum = postgresql.ENUM('active', 'frozen', 'suspended', 'cancelled', name='memberstatus')
    member_status_enum.create(op.get_bind())
    
    course_type_enum = postgresql.ENUM('group', 'private', 'semi_private', name='coursetype')
    course_type_enum.create(op.get_bind())
    
    booking_status_enum = postgresql.ENUM('pending', 'confirmed', 'checked_in', 'cancelled', 'no_show', 'completed', name='bookingstatus')
    booking_status_enum.create(op.get_bind())
    
    # 会员表
    op.create_table('members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('gender', sa.String(length=10), nullable=True),
        sa.Column('birthday', sa.DateTime(), nullable=True),
        sa.Column('card_type', card_type_enum, nullable=True),
        sa.Column('card_start_date', sa.DateTime(), nullable=True),
        sa.Column('card_end_date', sa.DateTime(), nullable=True),
        sa.Column('card_remaining_count', sa.Integer(), nullable=True, default=0),
        sa.Column('card_balance', sa.Float(), nullable=True, default=0.0),
        sa.Column('level', sa.Integer(), nullable=True, default=1),
        sa.Column('total_consumption', sa.Float(), nullable=True, default=0.0),
        sa.Column('status', member_status_enum, nullable=True, default='active'),
        sa.Column('body_test_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('coach_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_members_id'), 'members', ['id'], unique=False)
    op.create_index(op.f('ix_members_phone'), 'members', ['phone'], unique=True)
    
    # 教练表
    op.create_table('coaches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('certificates', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('specialization', sa.String(length=100), nullable=True),
        sa.Column('introduction', sa.Text(), nullable=True),
        sa.Column('work_schedule', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_hours', sa.Float(), nullable=True, default=0.0),
        sa.Column('total_students', sa.Integer(), nullable=True, default=0),
        sa.Column('avg_rating', sa.Float(), nullable=True, default=0.0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_coaches_id'), 'coaches', ['id'], unique=False)
    op.create_index(op.f('ix_coaches_phone'), 'coaches', ['phone'], unique=True)
    
    # 添加外键约束 - 会员表
    op.create_foreign_key('fk_members_coach', 'members', 'coaches', ['coach_id'], ['id'])
    
    # 课程表
    op.create_table('courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('course_type', course_type_enum, nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True, default=60),
        sa.Column('room', sa.String(length=50), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('package_price', sa.Float(), nullable=True),
        sa.Column('coach_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('max_attendees', sa.Integer(), nullable=True, default=10),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_courses_id'), 'courses', ['id'], unique=False)
    op.create_foreign_key('fk_courses_coach', 'courses', 'coaches', ['coach_id'], ['id'])
    
    # 课程排期表
    op.create_table('course_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, default='scheduled'),
        sa.Column('enrolled_count', sa.Integer(), nullable=True, default=0),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_course_schedules_id'), 'course_schedules', ['id'], unique=False)
    op.create_index(op.f('ix_course_schedules_start_time'), 'course_schedules', ['start_time'], unique=False)
    op.create_foreign_key('fk_course_schedules_course', 'course_schedules', 'courses', ['course_id'], ['id'])
    
    # 预约表
    op.create_table('bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('status', booking_status_enum, nullable=True, default='pending'),
        sa.Column('check_in_time', sa.DateTime(), nullable=True),
        sa.Column('check_in_method', sa.String(length=20), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_by', sa.Integer(), nullable=True),
        sa.Column('cancel_reason', sa.String(length=200), nullable=True),
        sa.Column('notes', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookings_id'), 'bookings', ['id'], unique=False)
    op.create_foreign_key('fk_bookings_member', 'bookings', 'members', ['member_id'], ['id'])
    op.create_foreign_key('fk_bookings_schedule', 'bookings', 'course_schedules', ['schedule_id'], ['id'])
    
    # 用户表
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, default='receptionist'),
        sa.Column('member_id', sa.Integer(), nullable=True),
        sa.Column('coach_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, default=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_foreign_key('fk_users_member', 'users', 'members', ['member_id'], ['id'])
    op.create_foreign_key('fk_users_coach', 'users', 'coaches', ['coach_id'], ['id'])
    
    # 操作日志表
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('old_value', sa.String(length=500), nullable=True),
        sa.Column('new_value', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_foreign_key('fk_audit_logs_user', 'audit_logs', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    """降级迁移 - 删除所有表"""
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('bookings')
    op.drop_table('course_schedules')
    op.drop_table('courses')
    op.drop_table('members')
    op.drop_table('coaches')
    
    # 删除枚举类型
    card_type_enum = postgresql.ENUM(name='cardtype')
    card_type_enum.drop(op.get_bind())
    
    member_status_enum = postgresql.ENUM(name='memberstatus')
    member_status_enum.drop(op.get_bind())
    
    course_type_enum = postgresql.ENUM(name='coursetype')
    course_type_enum.drop(op.get_bind())
    
    booking_status_enum = postgresql.ENUM(name='bookingstatus')
    booking_status_enum.drop(op.get_bind())