"""empty message

Revision ID: c49af59982d2
Revises: 1e8021fd11ad
Create Date: 2024-04-08 03:21:52.363321

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

from app.models.util import TZDateTime

# revision identifiers, used by Alembic.
revision = 'c49af59982d2'
down_revision = '1e8021fd11ad'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('appointment_slots', sa.Column('appointment_price', sa.Numeric(precision=14, scale=2), nullable=False))
    op.add_column('appointments', sa.Column('created_at', TZDateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('appointments', sa.Column('updated_at', TZDateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('appointments', sa.Column('payment_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('appointments', 'payment_url')
    op.drop_column('appointments', 'updated_at')
    op.drop_column('appointments', 'created_at')
    op.drop_column('appointment_slots', 'appointment_price')
    # ### end Alembic commands ###