"""add user table

Revision ID: 552612cc0faf
Revises: 7c93553d9e92
Create Date: 2023-04-26 15:11:52.824464

"""
# pyright: reportPrivateImportUsage=false
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "552612cc0faf"
down_revision = "7c93553d9e92"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("spotify", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("users")
    # ### end Alembic commands ###