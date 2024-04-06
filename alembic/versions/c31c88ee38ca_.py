"""empty message

Revision ID: c31c88ee38ca
Revises: 7bcf8b603ef0
Create Date: 2024-03-29 05:42:27.694896

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'c31c88ee38ca'
down_revision = '7bcf8b603ef0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('purchases',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('current_timestamp'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('current_timestamp'), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('store_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('state', sa.Enum('IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='purchasestatus'), nullable=False),
    sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
    sa.PrimaryKeyConstraint('store_id', 'id')
    )
    op.create_table('purchase_items',
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('product_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('store_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('purchase_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.ForeignKeyConstraint(['store_id', 'product_id'], ['products.store_id', 'products.id'], ),
    sa.ForeignKeyConstraint(['store_id', 'purchase_id'], ['purchases.store_id', 'purchases.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('purchase_items')
    op.drop_table('purchases')
    # ### end Alembic commands ###
    
    # drop purchasestatus enum
    sa.Enum(name='purchasestatus').drop(op.get_bind())
