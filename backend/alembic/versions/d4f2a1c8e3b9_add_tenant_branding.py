"""add tenant branding fields

Revision ID: d4f2a1c8e3b9
Revises: c7d3f0a1b2e4
Create Date: 2026-05-09 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4f2a1c8e3b9'
down_revision: Union[str, Sequence[str], None] = 'c7d3f0a1b2e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add branding columns to lavanderias."""
    op.add_column(
        "lavanderias",
        sa.Column("logo_url", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "lavanderias",
        sa.Column("logo_url_dark", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "lavanderias",
        sa.Column("color_primario", sa.String(length=9), nullable=True),
    )
    op.add_column(
        "lavanderias",
        sa.Column("color_secundario", sa.String(length=9), nullable=True),
    )
    op.add_column(
        "lavanderias",
        sa.Column(
            "mostrar_marca_mukusoft",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("lavanderias", "mostrar_marca_mukusoft")
    op.drop_column("lavanderias", "color_secundario")
    op.drop_column("lavanderias", "color_primario")
    op.drop_column("lavanderias", "logo_url_dark")
    op.drop_column("lavanderias", "logo_url")
