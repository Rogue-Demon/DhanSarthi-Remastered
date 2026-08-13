"""add phone and occupation to profiles

Revision ID: c4741a01276c
Revises: a1b2c3d4e5f6
Create Date: 2026-08-13 14:47:10.024400
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c4741a01276c'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('profiles', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('profiles', sa.Column('occupation', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('profiles', 'occupation')
    op.drop_column('profiles', 'phone')
