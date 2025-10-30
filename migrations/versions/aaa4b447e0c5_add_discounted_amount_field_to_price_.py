"""Add 'discounted_amount' field to 'Price' table

Revision ID: aaa4b447e0c5
Revises: dd08dfad6653
Create Date: 2025-10-30 11:46:38.566885

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "aaa4b447e0c5"
down_revision: Union[str, Sequence[str], None] = "dd08dfad6653"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "price",
        sa.Column("discounted_amount", sa.FLOAT),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("price", "discounted_amount")
