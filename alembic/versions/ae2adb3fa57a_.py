"""create tables

Revision ID: ae2adb3fa57a
Revises: 
Create Date: 2024-12-30 14:12:58.315128

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ae2adb3fa57a"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("username", sa.String, nullable=False),
        sa.Column("login", sa.String, nullable=False, unique=True),
        sa.Column("password", sa.String, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.sql.expression.text("now()"),
        ),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column(
            "done_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.sql.expression.text("now()"),
        ),
    )
    op.create_foreign_key(
        "user_id_fkey",
        source_table="transactions",
        referent_table="users",
        local_cols=["user_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("user_id_fkey", "transactions", type_="foreignkey")
    op.drop_table("transactions")
    op.drop_table("users")
