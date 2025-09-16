"""add categories table

Revision ID: 6376d0895e27
Revises: ae2adb3fa57a
Create Date: 2025-09-15 23:23:29.859368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6376d0895e27'
down_revision: Union[str, None] = 'ae2adb3fa57a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('categories')
