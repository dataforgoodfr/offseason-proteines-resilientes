from enum import StrEnum, unique
from typing import List, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import false
from sqlalchemy.types import Numeric

from models.category import Category

from .base import Base
from .source import Source


@unique
class QuantityUnit(StrEnum):
    """
    Unit of the quantity of food product contained in a product packaging.

    The unit represents either a weight, a volume, or pieces (i.e. eggs).
    """

    KILOGRAM = "kg"
    LITRE = "L"
    PIECE = "p"

    @classmethod
    def _missing_(cls, value):
        """
        Invoked when the value is not found in the enum. It is used here to
        accept values in a case-insensitive way.

        See https://docs.python.org/3/library/enum.html#enum.Enum._missing_.
        """

        value = value.upper()

        for member in cls:
            if member.value.upper() == value:
                return member

        return None


class Product(Base):
    """
    Represents the product table in the RDBMS.
    """

    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True)

    ean_13: Mapped[str] = mapped_column(String(13))
    disabled: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=false())

    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[Optional[str]] = mapped_column(String(255))

    quantity: Mapped[float] = mapped_column(Numeric(4, 2))
    quantity_unit: Mapped["QuantityUnit"] = mapped_column(
        Enum(
            QuantityUnit,
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        server_default=QuantityUnit.KILOGRAM,
    )

    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))

    category: Mapped["Category"] = relationship(back_populates="products")
    sources: Mapped[List["Source"]] = relationship(back_populates="product")
