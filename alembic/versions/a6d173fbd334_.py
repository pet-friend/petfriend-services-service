"""empty message

Revision ID: a6d173fbd334
Revises: 8c8806cc0651
Create Date: 2024-03-31 20:45:19.540754

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'a6d173fbd334'
down_revision = '8c8806cc0651'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('stores', 'shipping_cost',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=14, scale=2),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('stores', 'shipping_cost',
               existing_type=sa.Numeric(precision=14, scale=2),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=False)
    # ### end Alembic commands ###
