"""empty message

Revision ID: 8c8806cc0651
Revises: 8f36b4ccd430
Create Date: 2024-03-31 04:26:11.009654

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '8c8806cc0651'
down_revision = '8f36b4ccd430'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('purchases', sa.Column('buyer_id', sqlmodel.sql.sqltypes.GUID(), nullable=False))
    op.add_column('purchases', sa.Column('delivery_address_id', sqlmodel.sql.sqltypes.GUID(), nullable=False))
    op.drop_column('purchases', 'buyer')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('purchases', sa.Column('buyer', sa.UUID(), autoincrement=False, nullable=False))
    op.drop_column('purchases', 'delivery_address_id')
    op.drop_column('purchases', 'buyer_id')
    # ### end Alembic commands ###
