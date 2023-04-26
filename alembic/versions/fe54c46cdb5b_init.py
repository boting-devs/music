"""init

Revision ID: fe54c46cdb5b
Revises:
Create Date: 2023-02-16 23:10:49.452676

"""
# pyright: reportPrivateImportUsage=false
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "fe54c46cdb5b"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "blacklist_guilds",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "blacklist_users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "commands",
        sa.Column("command", sa.String(length=255), nullable=False),
        sa.Column("guild", sa.BigInteger(), nullable=False),
        sa.Column("channel", sa.BigInteger(), nullable=False),
        sa.Column("member", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("command", "guild", "channel", "member"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("commands")
    op.drop_table("blacklist_users")
    op.drop_table("blacklist_guilds")
    # ### end Alembic commands ###
