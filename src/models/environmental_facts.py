from enum import StrEnum, unique
from typing import Optional
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .base import Base

# To avoid circular imports.
if TYPE_CHECKING:
    from .source import Source


@unique
class GreenScore(StrEnum):
    """
    The Green-Score represents the environmental impact of a product.

    "A" is the best score whereas "E" is the worst. OpenFoodFacts also
    introduced two custom grades which are "A+" and "F".

    See https://world.openfoodfacts.org/green-score.
    """

    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"

    @classmethod
    def _missing_(cls, value):
        """
        Invoked when the value is not found in the enum. It is used here to
        accept values in a case-insensitive way.

        See https://docs.python.org/3/library/enum.html#enum.Enum._missing_.
        """

        # To accept values such as "a+", "a-plus", or "a_plus".
        value = value.upper().replace("-PLUS", "+").replace("_PLUS", "+")

        for member in cls:
            if member.value == value:
                return member

        return None


class EnvironmentalFacts(Base):
    """
    Represents the environmental facts table in the RDBMS.
    """

    __tablename__ = "environmental_facts"

    id: Mapped[int] = mapped_column(primary_key=True)

    green_score: Mapped[Optional[GreenScore]]

    co2_agriculture: Mapped[Optional[float]]
    co2_consumption: Mapped[Optional[float]]
    co2_distribution: Mapped[Optional[float]]
    co2_packaging: Mapped[Optional[float]]
    co2_processing: Mapped[Optional[float]]
    co2_total: Mapped[Optional[float]]
    co2_transportation: Mapped[Optional[float]]

    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    source: Mapped["Source"] = relationship(back_populates="environmental_facts")
