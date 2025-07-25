from typing import List
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .base import Base
from .source import Source


class Product(Base):
    """
    Represents the product table in the RDBMS.
    """

    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True)

    ean_13: Mapped[str] = mapped_column(String(13))

    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[Optional[str]] = mapped_column(String(255))

    sources: Mapped[List["Source"]] = relationship(back_populates="product")
