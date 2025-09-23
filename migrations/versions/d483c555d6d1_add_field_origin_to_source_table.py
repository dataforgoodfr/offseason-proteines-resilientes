"""Add field 'origin' to 'Source' table

Revision ID: d483c555d6d1
Revises: 74f8c9658d25
Create Date: 2025-09-21 13:54:30.471604

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from models.source import Origin, Source


# revision identifiers, used by Alembic.
revision: str = "d483c555d6d1"
down_revision: Union[str, Sequence[str], None] = "74f8c9658d25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    bind = op.get_bind()

    origin_type = sa.Enum(Origin)
    origin_type.create(bind, checkfirst=True)
    op.add_column("source", sa.Column("origin", origin_type, index=True))

    source_table = sa.inspect(Source).local_table
    sources = bind.execute(sa.select(source_table.c.id, source_table.c.url)).fetchall()

    for id, url in sources:
        new_origin = None

        if url.startswith("https://world.openfoodfacts.org"):
            new_origin = Origin.OPEN_FOOD_FACTS
        elif url.startswith("https://www.auchan.fr"):
            new_origin = Origin.AUCHAN
        else:
            raise ValueError("URL not recognised")

        bind.execute(
            source_table.update()
            .where(source_table.c.id == id)
            .values(origin=new_origin)
        )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("ix_source_origin", table_name="source", if_exists=True)
    op.drop_column("source", "origin")
