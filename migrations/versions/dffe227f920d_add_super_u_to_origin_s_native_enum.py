"""Add Super U to origin's native enum

Revision ID: dffe227f920d
Revises: 0ea78d81a3aa
Create Date: 2026-02-12 16:12:53.430207

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dffe227f920d"
down_revision: Union[str, Sequence[str], None] = "0ea78d81a3aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def is_postgres() -> bool:
    """
    Returns true if the RDBMS in use is a PostgreSQL one, false otherwise.
    """

    return op.get_context().dialect.name == "postgresql"


def check_enum_exists(enum_name: str) -> bool:
    """
    Checks whether or not a native enum exists.

    Taken from https://github.com/sqlalchemy/alembic/issues/1254#issuecomment-2921234852.
    """

    connection = op.get_bind()
    result = connection.execute(
        sa.text(f"SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}')")
    )
    return result.scalar()


def upgrade() -> None:
    """Upgrade schema."""

    if is_postgres() and check_enum_exists("origin"):
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE origin ADD VALUE 'SUPER_U'")


def downgrade() -> None:
    """Downgrade schema."""

    if is_postgres() and check_enum_exists("origin"):
        op.execute("ALTER TYPE origin RENAME TO origin_old")
        op.execute(
            "CREATE TYPE origin AS ENUM('AUCHAN', 'BIOCOOP', 'CARREFOUR', 'CASINO', 'ELECLERC', 'LA_VIE_CLAIRE', 'INTERMARCHE', 'LIDL', 'OPEN_FOOD_FACTS', 'PICARD')"
        )
        op.execute(
            (
                "ALTER TABLE source ALTER COLUMN origin TYPE origin USING "
                "origin::text::origin"
            )
        )
        op.execute("DROP TYPE origin_old")
