"""add estado to ventas

Revision ID: c7d3f0a1b2e4
Revises: 5a8f3059ef71
Create Date: 2026-05-06 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'c7d3f0a1b2e4'
down_revision: Union[str, Sequence[str], None] = '5a8f3059ef71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'ventas',
        sa.Column('estado', sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column('ventas', 'estado')
