"""modify user spotify fields

Revision ID: 956abcb8f455
Revises: 6669e1c709a5
Create Date: 2023-05-18 16:04:06.657047

"""
# pyright: reportPrivateImportUsage=false
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "956abcb8f455"
down_revision = "6669e1c709a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("users", sa.Column("spotify_id", sa.Text(), nullable=True))
    op.drop_column("users", "spotify_activation_time")
    op.drop_column("users", "spotify_access_token")
    op.drop_column("users", "spotify_refresh_token")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "users",
        sa.Column(
            "spotify_refresh_token",
            sa.VARCHAR(length=255),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "spotify_access_token",
            sa.VARCHAR(length=255),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "spotify_activation_time",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.drop_column("users", "spotify_id")
    # ### end Alembic commands ###
