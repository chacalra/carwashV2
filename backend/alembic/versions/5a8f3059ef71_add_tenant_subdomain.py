"""add tenant subdomain

Revision ID: 5a8f3059ef71
Revises: 8a982724c18c
Create Date: 2026-05-03 12:51:30.241029

"""
import re
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a8f3059ef71'
down_revision: Union[str, Sequence[str], None] = '8a982724c18c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _slugify_subdomain(nombre_local: str) -> str:
    """Genera un subdominio base corto y compatible desde el nombre local."""
    cleaned = re.sub(r"[^a-z0-9]+", "-", nombre_local.lower()).strip("-")
    return cleaned or "lavanderia"


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "lavanderias",
        sa.Column("subdominio", sa.String(length=100), nullable=True),
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, nombre_local FROM lavanderias ORDER BY id ASC")
    ).fetchall()

    used_subdomains: set[str] = set()
    for row in rows:
        base_subdomain = _slugify_subdomain(row.nombre_local)
        candidate = base_subdomain
        suffix = 2

        while candidate in used_subdomains:
            candidate = f"{base_subdomain}-{suffix}"
            suffix += 1

        used_subdomains.add(candidate)
        connection.execute(
            sa.text(
                "UPDATE lavanderias SET subdominio = :subdominio WHERE id = :lavanderia_id"
            ),
            {
                "subdominio": candidate,
                "lavanderia_id": row.id,
            },
        )

    op.alter_column("lavanderias", "subdominio", nullable=False)
    op.create_index("ix_lavanderias_subdominio", "lavanderias", ["subdominio"], unique=False)
    op.create_unique_constraint(
        "uq_lavanderias_subdominio",
        "lavanderias",
        ["subdominio"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_lavanderias_subdominio", "lavanderias", type_="unique")
    op.drop_index("ix_lavanderias_subdominio", table_name="lavanderias")
    op.drop_column("lavanderias", "subdominio")
