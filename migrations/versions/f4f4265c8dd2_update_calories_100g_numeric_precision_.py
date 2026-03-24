"""Update calories_100g numeric precision to allow values > 1000

Revision ID: f4f4265c8dd2
Revises: 24c1199c4b3a
Create Date: 2026-03-16 12:09:53.643355

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from models.nutrition_facts import NutritionFacts

# revision identifiers, used by Alembic.
revision: str = "f4f4265c8dd2"
down_revision: Union[str, Sequence[str], None] = "24c1199c4b3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite requires recreating the table to change column types
    # We create a temporary table with the new schema

    # Create the new table with updated precision (NUMERIC(6, 2))
    op.execute("""
        CREATE TABLE nutrition_facts_new (
            id INTEGER NOT NULL,
            nutriscore VARCHAR(1),
            novascore VARCHAR(6),
            calories_100g NUMERIC(6, 2),
            fat_100g NUMERIC(5, 2),
            saturated_fat_100g NUMERIC(5, 2),
            carbohydrates_100g NUMERIC(5, 2),
            sugars_100g NUMERIC(5, 2),
            fiber_100g NUMERIC(5, 2),
            protein_100g NUMERIC(5, 2),
            salt_100g NUMERIC(5, 2),
            source_id INTEGER NOT NULL,
            PRIMARY KEY(id),
            FOREIGN KEY(source_id) REFERENCES source(id)
        )
    """)

    # Copy data from old table to new table
    op.execute("""
        INSERT INTO nutrition_facts_new
        SELECT * FROM nutrition_facts
    """)

    # Drop the old table
    op.execute("DROP TABLE nutrition_facts")

    # Rename the new table to the original name
    op.execute("ALTER TABLE nutrition_facts_new RENAME TO nutrition_facts")


def downgrade() -> None:
    """Downgrade schema."""

    # Check if any values exceed the old limit (999.99)
    bind = op.get_bind()
    nutrition_table = sa.inspect(NutritionFacts).local_table
    result = bind.execute(
        sa.select(nutrition_table.c.id).where(nutrition_table.c.calories_100g > 999.99)
    ).fetchall()
    if len(result) > 0:
        raise Exception(
            f"Cannot downgrade: {len(result)} records have calories_100g > 999.99. "
        )

    # Safe downgrade
    # Create the old table structure
    op.execute("""
        CREATE TABLE nutrition_facts_old (
            id INTEGER NOT NULL,
            nutriscore VARCHAR(1),
            novascore VARCHAR(6),
            calories_100g NUMERIC(5, 2),
            fat_100g NUMERIC(5, 2),
            saturated_fat_100g NUMERIC(5, 2),
            carbohydrates_100g NUMERIC(5, 2),
            sugars_100g NUMERIC(5, 2),
            fiber_100g NUMERIC(5, 2),
            protein_100g NUMERIC(5, 2),
            salt_100g NUMERIC(5, 2),
            source_id INTEGER NOT NULL,
            PRIMARY KEY(id),
            FOREIGN KEY(source_id) REFERENCES source(id)
        )
    """)

    # Copy data back
    op.execute("""
        INSERT INTO nutrition_facts_old
        SELECT * FROM nutrition_facts
    """)

    # Drop the current table
    op.execute("DROP TABLE nutrition_facts")

    # Rename the old table back
    op.execute("ALTER TABLE nutrition_facts_old RENAME TO nutrition_facts")
