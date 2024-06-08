"""empty message

Revision ID: 0d265e38316f
Revises: d5ce16b886f1
Create Date: 2024-04-10 00:19:01.063750

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0d265e38316f"
down_revision = "d5ce16b886f1"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("appointments", "status", new_column_name="payment_status")
    op.alter_column("purchases", "status", new_column_name="payment_status")


def downgrade():
    op.alter_column("purchases", "payment_status", new_column_name="status")
    op.alter_column("appointments", "payment_status", new_column_name="status")
