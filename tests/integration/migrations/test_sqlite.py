"""
Integration tests for Alembic migrations on SQLite.

These tests ensure that all migrations can be applied and reverted successfully
on SQLite.
"""

import unittest
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect


class TestMigrations(unittest.TestCase):
    """
    Tests for database migrations.
    """

    def setUp(self):
        """
        Sets up a temporary database for testing.
        """

        self.project_root = Path(__file__).parent.parent.parent.parent

        # Set up Alembic configuration.
        self.alembic_cfg = Config(str(self.project_root / "alembic.ini"))
        self.alembic_cfg.set_main_option(
            "script_location", str(self.project_root / "migrations")
        )

        # Create an in-memory database.
        self.engine = create_engine("sqlite:///:memory:")

        # Initiate a connection to the database and share it via Alembic
        # configuration object.
        #
        # See https://alembic.sqlalchemy.org/en/latest/cookbook.html#sharing-a-connection-across-one-or-more-programmatic-migration-commands.
        self.conn = self.engine.connect()
        self.alembic_cfg.attributes["connection"] = self.conn

        # Create base tables manually (without migration-added columns).
        #
        # This represents the state of the database before any migrations.
        self.conn.execute(
            sa.text("""
            CREATE TABLE product (
                id INTEGER NOT NULL,
                ean_13 VARCHAR(13) NOT NULL,
                name VARCHAR(255) NOT NULL,
                brand VARCHAR(255),
                PRIMARY KEY (id)
            );
        """)
        )
        self.conn.execute(
            sa.text("""
            CREATE TABLE source (
                id INTEGER NOT NULL,
                url VARCHAR(8000) NOT NULL,
                seen_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                product_id INTEGER NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(product_id) REFERENCES product (id)
            );
        """)
        )
        self.conn.execute(
            sa.text("""
            CREATE TABLE price (
                id INTEGER NOT NULL,
                amount NUMERIC(4, 2) NOT NULL,
                currency VARCHAR(3) NOT NULL,
                source_id INTEGER NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(source_id) REFERENCES source (id)
            );
        """)
        )
        self.conn.execute(
            sa.text("""
            CREATE TABLE nutrition_facts (
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
                PRIMARY KEY (id),
                FOREIGN KEY(source_id) REFERENCES source (id)
            );
        """)
        )
        self.conn.execute(
            sa.text("""
            CREATE TABLE environmental_facts (
                id INTEGER PRIMARY KEY,
                co2_kg REAL,
                nutriscore TEXT,
                ecoscore TEXT,
                nova_group INTEGER,
                source_id INTEGER UNIQUE NOT NULL,
                FOREIGN KEY(source_id) REFERENCES source (id) ON DELETE CASCADE
            )
        """)
        )

        # Stamp the database with 'base' to track migrations.
        command.stamp(self.alembic_cfg, "base")

    def tearDown(self):
        """
        Cleans up the temporary database.
        """

        self.engine.dispose()

    def test_migrations_upgrade_to_head(self):
        """
        Tests that all migrations can be applied successfully.
        """

        # Run all migrations.
        command.upgrade(self.alembic_cfg, "head")
        self.conn.commit()

        # Verify that the database has tables.
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()

        # Check that expected tables exist.
        expected_tables = [
            "product",
            "source",
            "price",
            "nutrition_facts",
            "environmental_facts",
            "category",
        ]
        for table in expected_tables:
            self.assertIn(
                table,
                tables,
                f"Table '{table}' should exist after migrations",
            )

    def test_migrations_downgrade_to_base(self):
        """
        Tests that all migrations can be reverted successfully.
        """

        # First upgrade to 'head'.
        command.upgrade(self.alembic_cfg, "head")

        # Then downgrade to 'base'.
        command.downgrade(self.alembic_cfg, "base")

        self.conn.commit()

        # Verify that base tables still exist (migrations don't delete them).
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()

        # Base tables should still exist after downgrade.
        base_tables = [
            "product",
            "source",
            "price",
            "nutrition_facts",
            "environmental_facts",
        ]
        for table in base_tables:
            self.assertIn(
                table,
                tables,
                f"Base table '{table}' should still exist after downgrade",
            )

        # Verify that migration-added columns are removed.
        product_columns = {col["name"] for col in inspector.get_columns("product")}
        self.assertNotIn(
            "disabled", product_columns, "disabled column should be removed"
        )
        self.assertNotIn(
            "quantity", product_columns, "quantity column should be removed"
        )
        self.assertNotIn(
            "quantity_unit",
            product_columns,
            "quantity_unit column should be removed",
        )
        self.assertNotIn(
            "category_id", product_columns, "category_id column should be removed"
        )

        source_columns = {col["name"] for col in inspector.get_columns("source")}
        self.assertNotIn("origin", source_columns, "origin column should be removed")

        price_columns = {col["name"] for col in inspector.get_columns("price")}
        self.assertNotIn(
            "discounted", price_columns, "discounted column should be removed"
        )
        self.assertNotIn(
            "discounted_amount",
            price_columns,
            "discounted_amount column should be removed",
        )

        # Category table should be removed (it was created by a migration).
        self.assertNotIn("category", tables, "category table should be removed")

    def test_migrations_upgrade_downgrade_each_revision(self):
        """
        Tests that each migration can be applied and reverted individually.
        """

        # Get all revisions.
        script = ScriptDirectory.from_config(self.alembic_cfg)
        revisions = [rev.revision for rev in script.walk_revisions()]
        revisions.reverse()  # Start from oldest.

        # Test each revision.
        for i, revision in enumerate(revisions):
            with self.subTest(revision=revision, step=i + 1):
                # Upgrade to this revision.
                command.upgrade(self.alembic_cfg, revision)
                self.conn.commit()

                # Verify database is in a consistent state.
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                self.assertGreaterEqual(
                    len(tables),
                    1,
                    f"At least alembic_version table should exist at revision {revision}",
                )

                # Downgrade one step.
                if i > 0:
                    command.downgrade(self.alembic_cfg, revisions[i - 1])
                else:
                    command.downgrade(self.alembic_cfg, "base")

    def test_migration_adds_category_table(self):
        """
        Tests that the category migration creates the category table.
        """

        command.upgrade(self.alembic_cfg, "0ea78d81a3aa")
        self.conn.commit()

        inspector = inspect(self.engine)
        tables = inspector.get_table_names()

        self.assertIn("category", tables)

        columns = {col["name"] for col in inspector.get_columns("category")}
        self.assertIn("id", columns)
        self.assertIn("name", columns)
        self.assertIn("parent_id", columns)

        product_columns = {col["name"] for col in inspector.get_columns("product")}
        self.assertIn("category_id", product_columns)

    def test_migration_adds_disabled_field(self):
        """
        Tests that the disabled field migration works.
        """

        command.upgrade(self.alembic_cfg, "74f8c9658d25")

        inspector = inspect(self.engine)
        product_columns = {col["name"] for col in inspector.get_columns("product")}

        self.assertIn("disabled", product_columns)

    def test_migration_adds_quantity_fields(self):
        """
        Tests that the quantity fields migration works.
        """

        command.upgrade(self.alembic_cfg, "b13c7ee298c7")

        inspector = inspect(self.engine)
        product_columns = {col["name"] for col in inspector.get_columns("product")}

        self.assertIn("quantity", product_columns)
        self.assertIn("quantity_unit", product_columns)

    def test_migration_adds_origin_field(self):
        """
        Tests that the origin field migration works.
        """

        command.upgrade(self.alembic_cfg, "d483c555d6d1")

        inspector = inspect(self.engine)
        source_columns = {col["name"] for col in inspector.get_columns("source")}

        self.assertIn("origin", source_columns)

    def test_migration_adds_price_discount_fields(self):
        """
        Tests that the price discount fields migrations work.
        """

        # Upgrade to the 'discounted' field migration.
        command.upgrade(self.alembic_cfg, "dd08dfad6653")
        self.conn.commit()

        inspector = inspect(self.engine)
        price_columns = {col["name"] for col in inspector.get_columns("price")}

        self.assertIn("discounted", price_columns)

        # Continue to 'discounted_amount' field migration.
        command.upgrade(self.alembic_cfg, "aaa4b447e0c5")
        self.conn.commit()

        inspector = inspect(self.engine)
        price_columns = {col["name"] for col in inspector.get_columns("price")}

        self.assertIn("discounted_amount", price_columns)

    def test_no_missing_downgrade_functions(self):
        """
        Tests that all migrations have a downgrade function.
        """

        script = ScriptDirectory.from_config(self.alembic_cfg)

        for revision in script.walk_revisions():
            with self.subTest(revision=revision.revision):
                # Check that the module has a downgrade function.
                module = revision.module
                self.assertTrue(
                    hasattr(module, "downgrade"),
                    f"Migration {revision.revision} is missing downgrade function",
                )
                self.assertIsNotNone(
                    module.downgrade,
                    f"Migration {revision.revision} has None downgrade function",
                )


if __name__ == "__main__":
    unittest.main()
