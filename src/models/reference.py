from enum import StrEnum, unique
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .base import Base

# To avoid circular imports.
if TYPE_CHECKING:
    from .product import Product


@unique
class Type(StrEnum):
    """
    Represents the reference type.

    All values must be unique.
    """

    EAN = "EAN"

    @classmethod
    def _missing_(cls, value):
        """
        Invoked when the value is not found in the enum. It is used here to
        accept values in a case-insensitive way.

        See https://docs.python.org/3/library/enum.html#enum.Enum._missing_.
        """

        value = value.upper()

        for member in cls:
            if member.value == value:
                return member

        return None


class Reference(Base):
    """
    Represents the RDBMS table containing the product references.
    """

    __tablename__ = "product_reference"

    id: Mapped[int] = mapped_column(primary_key=True)

    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    product: Mapped["Product"] = relationship(back_populates="references")

    type: Mapped[Type]
    value: Mapped[str] = mapped_column(String(300))
