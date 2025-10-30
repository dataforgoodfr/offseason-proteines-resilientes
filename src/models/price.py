from typing import Optional
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Boolean
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.sql import false
from sqlalchemy.types import Numeric

from .base import Base

# To avoid circular imports.
if TYPE_CHECKING:
    from .source import Source


class Price(Base):
    """
    Represents the price table in the RDBMS.
    """

    __tablename__ = "price"

    id: Mapped[int] = mapped_column(primary_key=True)

    amount: Mapped[float] = mapped_column(Numeric(4, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    discounted: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=false())
    discounted_amount: Mapped[Optional[float]] = mapped_column(Numeric(4, 2))

    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    source: Mapped["Source"] = relationship(back_populates="price")
