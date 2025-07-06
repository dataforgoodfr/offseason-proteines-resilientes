from enum import Enum, StrEnum, unique
from typing import List, Optional
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .base import Base

# To avoid circular imports.
if TYPE_CHECKING:
    from .reference import Reference


@unique
class NutriScore(StrEnum):
    """
    The Nutri-Score represents the nutrition quality of food products.

    "A" is the best score whereas "E" is the worst.

    See https://world.openfoodfacts.org/nutriscore.
    """

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"

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


@unique
class NovaScore(Enum):
    """
    The nova score represents the degree of processing of foods.

    See https://world.openfoodfacts.org/nova.
    """

    # Unprocessed or minimally processed foods.
    Group1 = 1

    # Processed culinary ingredients.
    Group2 = 2

    # Processed foods.
    Group3 = 3

    # Ultra-processed food and drink products.
    Group4 = 4

    @classmethod
    def _missing_(cls, value):
        """
        Invoked when the value is not found in the enum. It is used here to
        accept values as strings.

        See https://docs.python.org/3/library/enum.html#enum.Enum._missing_.
        """

        if isinstance(value, str):
            value = int(value)

            for member in cls:
                if member.value == value:
                    return member

        return None


class Product(Base):
    """
    Represents the product table in the RDBMS.
    """

    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    references: Mapped[Optional[List["Reference"]]] = relationship(
        back_populates="product"
    )

    nutriscore: Mapped[Optional[NutriScore]]
    novascore: Mapped[Optional[NovaScore]]

    fat_100g: Mapped[Optional[float]]
    saturated_fat_100g: Mapped[Optional[float]]
    carbohydrates_100g: Mapped[Optional[float]]
    sugars_100g: Mapped[Optional[float]]
    fiber_100g: Mapped[Optional[float]]
    proteins_100g: Mapped[Optional[float]]
    salt_100g: Mapped[Optional[float]]
