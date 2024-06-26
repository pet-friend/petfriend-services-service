"""empty message

Revision ID: bef6baf1604d
Revises: f5942eddda51
Create Date: 2024-04-06 00:35:53.693993

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'bef6baf1604d'
down_revision = 'f5942eddda51'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('appointment_slots', sa.Column('max_appointments_per_slot', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('appointment_slots', 'max_appointments_per_slot')
    # ### end Alembic commands ###
