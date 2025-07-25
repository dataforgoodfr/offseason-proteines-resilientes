from enum import Enum, StrEnum, unique
from typing import Optional
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.types import Numeric

from .base import Base

# To avoid circular imports.
if TYPE_CHECKING:
    from .source import Source


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


class NutritionFacts(Base):
    """
    Represents the nutrition facts table in the RDBMS.
    """

    __tablename__ = "nutrition_facts"

    id: Mapped[int] = mapped_column(primary_key=True)

    nutriscore: Mapped[Optional[NutriScore]]
    novascore: Mapped[Optional[NovaScore]]

    calories_100g: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))

    fat_100g: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    saturated_fat_100g: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    carbohydrates_100g: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    sugars_100g: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    fiber_100g: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    protein_100g: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    salt_100g: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))

    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    source: Mapped["Source"] = relationship(back_populates="nutrition_facts")
