"""add goals table

Revision ID: cc036a01fc43
Revises: aa923732d0f6
Create Date: 2025-09-16 22:37:35.862468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc036a01fc43'
down_revision: Union[str, None] = 'aa923732d0f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('goals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('target_amount', sa.Float(), nullable=False),
    sa.Column('deadline', sa.Date(), nullable=False),
    sa.Column('is_completed', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('goals')
