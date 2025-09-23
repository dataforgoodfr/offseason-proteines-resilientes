import datetime
from enum import StrEnum, unique
from typing import Optional
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, func, String
from sqlalchemy.types import DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .base import Base
from .nutrition_facts import NutritionFacts
from .price import Price

# To avoid circular imports.
if TYPE_CHECKING:
    from .product import Product


# Taken from RFC 7230:
#
# "It is RECOMMENDED that all HTTP senders and recipients support, at a minimum,
# request-line lengths of 8000 octets."
URL_MAX_LENGTH = 8000


@unique
class Origin(StrEnum):
    """
    The origin is used to filter the
    """

    AUCHAN = "Auchan"
    BIOCOOP = "Biocoop"
    CARREFOUR = "Carrefour"
    CASINO = "Casino"
    ELECLERC = "E.Leclerc"
    LA_VIE_CLAIRE = "La Vie Claire"
    INTERMARCHE = "Intermarché"
    LIDL = "Lidl"
    OPEN_FOOD_FACTS = "OpenFoodFacts"
    PICARD = "Picard"

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


class Source(Base):
    """
    Represents a source in the RDBMS.

    A source entry in the database is used to store where and when a product has
    been seen online.
    """

    __tablename__ = "source"

    id: Mapped[int] = mapped_column(primary_key=True)
    origin: Mapped["Origin"] = mapped_column(index=True)
    url: Mapped[str] = mapped_column(String(URL_MAX_LENGTH))
    seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))

    nutrition_facts: Mapped[Optional["NutritionFacts"]] = relationship(
        back_populates="source"
    )
    price: Mapped[Optional["Price"]] = relationship(back_populates="source")
    product: Mapped["Product"] = relationship(back_populates="sources")
