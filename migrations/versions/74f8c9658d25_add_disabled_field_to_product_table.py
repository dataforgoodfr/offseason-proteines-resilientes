"""Add 'disabled' field to 'Product' table

Revision ID: 74f8c9658d25
Revises:
Create Date: 2025-08-11 13:56:23.604198

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "74f8c9658d25"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "product", sa.Column("disabled", sa.BOOLEAN, server_default=sa.sql.false())
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("product", "disabled")
