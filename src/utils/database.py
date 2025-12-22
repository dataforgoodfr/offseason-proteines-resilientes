from scrapy.spiders import Spider
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models.base import Base

# The default database URL.
#
# See https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.engine.URL.
#DEFAULT_DATABASE_URL = "sqlite+pysqlite:///data.sqlite"
DEFAULT_DATABASE_URL = "postgresql://localhost/offseason_db"


class RDBMSPipelineMixin:
    """
    Mixin for Scrapy RDBMS pipelines.
    """

    def open_spider(self, spider: Spider):
        database_url = spider.settings.get("DATABASE_URL", DEFAULT_DATABASE_URL)

        engine = create_engine(database_url)
        Base.metadata.create_all(engine)

        self.db_engine = engine
        self.db_session = Session(self.db_engine)

    def close_spider(self, spider: Spider):
        self.db_session.close()
