"""add categories table

Revision ID: 6376d0895e27
Revises: ae2adb3fa57a
Create Date: 2025-09-15 23:23:29.859368

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6376d0895e27"
down_revision: Union[str, None] = "ae2adb3fa57a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Add category_id column to transactions table
    op.add_column("transactions", sa.Column("category_id", sa.Integer(), nullable=False))
    op.create_foreign_key("fk_transactions_category_id", "transactions", "categories", ["category_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    # Remove foreign key constraint and column from transactions table
    op.drop_constraint("fk_transactions_category_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "category_id")
    # Drop categories table
    op.drop_table("categories")
