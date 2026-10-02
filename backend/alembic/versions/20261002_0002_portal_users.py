"""portal users: link a login to one employee or one customer

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Postgres (Neon) gets real foreign keys. SQLite, used only for local previews and tests,
    # cannot add a constraint to an existing table, so there the columns are added without one.
    with_keys = op.get_bind().dialect.name != 'sqlite'
    for column, target in (('employee_id', 'employees.id'), ('customer_id', 'customers.id')):
        extra = [sa.ForeignKey(target)] if with_keys else []
        op.add_column('users', sa.Column(column, sa.Uuid(), *extra, nullable=True))
    op.create_index(op.f('ix_users_employee_id'), 'users', ['employee_id'])
    op.create_index(op.f('ix_users_customer_id'), 'users', ['customer_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_users_customer_id'), table_name='users')
    op.drop_index(op.f('ix_users_employee_id'), table_name='users')
    op.drop_column('users', 'customer_id')
    op.drop_column('users', 'employee_id')
