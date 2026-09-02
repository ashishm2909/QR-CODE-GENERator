"""add is_admin to user

Revision ID: 4cd0c03c05bd
Revises: 
Create Date: 2026-03-18 17:14:15.075878

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4cd0c03c05bd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('users'):
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(length=120), nullable=False),
            sa.Column('password_hash', sa.String(length=256), nullable=False),
            sa.Column('phone', sa.String(length=20), nullable=True),
            sa.Column('plan', sa.String(length=20), nullable=True),
            sa.Column('subscription_status', sa.String(length=50), nullable=True),
            sa.Column('plan_expires_at', sa.DateTime(), nullable=True),
            sa.Column('is_admin', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
        )
        op.create_table(
            'payments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('razorpay_order_id', sa.String(length=255), nullable=True),
            sa.Column('razorpay_payment_id', sa.String(length=255), nullable=True),
            sa.Column('plan', sa.String(length=20), nullable=False),
            sa.Column('amount', sa.Integer(), nullable=False),
            sa.Column('currency', sa.String(length=10), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_payments_user_id', 'payments', ['user_id'], unique=False)
        op.create_table(
            'qr_codes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('type', sa.String(length=50), nullable=False),
            sa.Column('data', sa.Text(), nullable=False),
            sa.Column('image_path', sa.String(length=255), nullable=True),
            sa.Column('svg_content', sa.Text(), nullable=True),
            sa.Column('is_artistic', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_qr_codes_user_id', 'qr_codes', ['user_id'], unique=False)
        return

    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'is_admin' not in columns:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('users'):
        return

    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'is_admin' in columns:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_column('is_admin')
