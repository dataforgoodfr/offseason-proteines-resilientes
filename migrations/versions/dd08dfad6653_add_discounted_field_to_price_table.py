"""Add 'discounted' field to 'Price' table

Revision ID: dd08dfad6653
Revises: d483c555d6d1
Create Date: 2025-09-30 12:03:23.308390

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dd08dfad6653"
down_revision: Union[str, Sequence[str], None] = "d483c555d6d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "price", sa.Column("discounted", sa.BOOLEAN, server_default=sa.sql.false())
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("price", "discounted")
