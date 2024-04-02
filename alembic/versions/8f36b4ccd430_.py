"""empty message

Revision ID: 8f36b4ccd430
Revises: c31c88ee38ca
Create Date: 2024-03-30 21:31:58.208539

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8f36b4ccd430'
down_revision = 'c31c88ee38ca'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('purchases', sa.Column('status', sa.Enum('CREATED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='purchasestatus'), nullable=False))
    op.add_column('purchases', sa.Column('payment_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('purchases', sa.Column('buyer', sqlmodel.sql.sqltypes.GUID(), nullable=False))
    op.drop_column('purchases', 'state')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('purchases', sa.Column('state', postgresql.ENUM('IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='purchasestate'), autoincrement=False, nullable=False))
    op.drop_column('purchases', 'buyer')
    op.drop_column('purchases', 'payment_url')
    op.drop_column('purchases', 'status')
    # ### end Alembic commands ###
