"""add accounts table

Revision ID: aa923732d0f6
Revises: 6376d0895e27
Create Date: 2025-09-16 20:23:56.106162

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "aa923732d0f6"
down_revision: Union[str, None] = "6376d0895e27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("balance", sa.Float(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Add account_id column to transactions table
    op.add_column(
        "transactions", 
        sa.Column("account_id", sa.Integer(), nullable=False)
    )
    op.create_foreign_key(
        "fk_transactions_account_id",
        "transactions",
        "accounts", 
        ["account_id"],
        ["id"],
        ondelete="CASCADE"
    )


def downgrade() -> None:
    # Drop foreign key and column from transactions table
    op.drop_constraint("fk_transactions_account_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "account_id")
    
    # Drop accounts table
    op.drop_table("accounts")
