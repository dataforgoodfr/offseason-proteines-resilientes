"""Add 'category' and 'aliment' to 'Product' table

Revision ID: 0ea78d81a3aa
Revises: b13c7ee298c7
Create Date: 2025-11-14 12:55:00.663110

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from models.product import Category


# revision identifiers, used by Alembic.
revision: str = "0ea78d81a3aa"
down_revision: Union[str, Sequence[str], None] = "b13c7ee298c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    bind = op.get_bind()

    category_type = sa.Enum(
        Category, native_enum=False, values_callable=lambda e: [x.value for x in e]
    )
    category_type.create(bind, checkfirst=True)

    op.add_column(
        "product",
        sa.Column("category", category_type, server_default=Category.UNKNOWN),
    )
    op.add_column(
        "product",
        sa.Column("aliment", str, server_default="Unknown"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("product", "category")
    op.drop_column("product", "aliment")
