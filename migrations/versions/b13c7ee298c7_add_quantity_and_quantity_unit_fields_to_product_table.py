"""Add 'quantity' and 'quantity_unit' fields to 'Product' table

Revision ID: b13c7ee298c7
Revises: aaa4b447e0c5
Create Date: 2025-10-30 16:48:18.246037

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from models.product import QuantityUnit


# revision identifiers, used by Alembic.
revision: str = "b13c7ee298c7"
down_revision: Union[str, Sequence[str], None] = "aaa4b447e0c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    bind = op.get_bind()

    op.add_column("product", sa.Column("quantity", sa.Numeric(precision=4, scale=2)))

    quantity_unit_type = sa.Enum(
        QuantityUnit, native_enum=False, values_callable=lambda e: [x.value for x in e]
    )
    quantity_unit_type.create(bind, checkfirst=True)
    op.add_column(
        "product",
        sa.Column(
            "quantity_unit", quantity_unit_type, server_default=QuantityUnit.KILOGRAM
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("product", "quantity")
    op.drop_column("product", "quantity_unit")
