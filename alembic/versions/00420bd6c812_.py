"""empty message

Revision ID: 00420bd6c812
Revises: 7292119e1264
Create Date: 2024-02-25 03:02:36.029242

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = "00420bd6c812"
down_revision = "7292119e1264"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "stores",
        sa.Column("owner_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("stores", "owner_id")
    # ### end Alembic commands ###