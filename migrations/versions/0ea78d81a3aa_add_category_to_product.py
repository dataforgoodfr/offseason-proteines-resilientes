"""Add 'category' to 'Product' table

Revision ID: 0ea78d81a3aa
Revises: b13c7ee298c7
Create Date: 2025-11-14 12:55:00.663110

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from models.category import Category, CategoryValues, initialise_categories
from models.product import Product

# revision identifiers, used by Alembic.
revision: str = "0ea78d81a3aa"
down_revision: Union[str, Sequence[str], None] = "b13c7ee298c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# See https://alembic.sqlalchemy.org/en/latest/batch.html#dropping-unnamed-or-named-foreign-key-constraints.
naming_convention = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def upgrade() -> None:
    """Upgrade schema."""

    bind = op.get_bind()

    category_type = sa.Enum(
        CategoryValues, values_callable=lambda e: [x.value for x in e]
    )

    op.create_table(
        "category",
        sa.Column("id", sa.INTEGER, primary_key=True),
        sa.Column("name", category_type),
        sa.Column("parent_id", sa.INTEGER, nullable=True),
    )
    with op.batch_alter_table(
        "category", naming_convention=naming_convention
    ) as batch_op:
        batch_op.create_foreign_key(
            constraint_name="fk_category_parent_id_category",
            referent_table="category",
            local_cols=["parent_id"],
            remote_cols=["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table(
        "product", naming_convention=naming_convention
    ) as batch_op:
        batch_op.add_column(sa.Column("category_id", sa.INTEGER))
        batch_op.create_foreign_key(
            constraint_name="fk_product_category_id_category",
            referent_table="category",
            local_cols=["category_id"],
            remote_cols=["id"],
            ondelete="CASCADE",
        )

    product_table = sa.inspect(Product).local_table
    category_table = sa.inspect(Category).local_table

    initialise_categories(category_table, bind)

    category_unknown_id = bind.execute(
        sa.select(category_table.c.id).where(
            category_table.c.name == CategoryValues.UNKNOWN
        )
    ).scalar_one()
    bind.execute(product_table.update().values(category_id=category_unknown_id))


def downgrade() -> None:
    """Downgrade schema."""

    with op.batch_alter_table(
        "product", naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_product_category_id_category", type_="foreignkey")
        batch_op.drop_column("category_id")

    with op.batch_alter_table(
        "category", naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_category_parent_id_category", type_="foreignkey")

    op.drop_table("category")
