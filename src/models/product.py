from enum import StrEnum, unique
from typing import List
from typing import Optional

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.sql import false
from sqlalchemy.types import Numeric

from .base import Base
from .source import Source


@unique
class QuantityUnit(StrEnum):
    """
    Unit of the quantity of food product contained in a product packaging.

    The unit represents eigher a weight or a volume.
    """

    KILOGRAM = "kg"
    LITRE = "L"

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


@unique
class Category(StrEnum):
    """
    The normalised category of the product.
    """

    VIANDE = "Viandes"
    POISSON = "Poissons et fruits de mer"
    LAITIER = "Œufs et produits laitiers"
    LEGUMINEUSE = "Légumineuses"
    SOJA = "Produits à base de soja"
    ASSIMILE = "Légumes et assimilés"
    CEREALE = "Céréales et pseudo-céréales"
    NOIX = "Noix et graines"
    POUDRE = "Poudres protéinées"
    ALTERNATIVE = "Alternatives végétales"

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


@unique
class Department(StrEnum):
    """
    The store main department of the product.
    """

    LAITIER = "Produits laitiers, oeufs, fromages"  # cn01
    VIANDE = "Boucherie, volaille, poissonnerie"  # cn02
    CHARCUTERIE = "Charcuterie, traiteur"  # cn12
    FRAIS = "Marché frais"  # cb19
    EPICERIE = "Epicerie salée"  # cn06
    SUCRE = "Epicerie sucrée"  # cn05
    FRUIT_LEGUME = "Fruits, légumes"  # cn03
    SURGELE = "Surgelés"  # cn04

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

    category: Mapped["Category"] = mapped_column(
        Enum(
            Category,
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
    )

    department: Mapped["Department"] = mapped_column(
        Enum(
            Department,
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
    )

    sources: Mapped[List["Source"]] = relationship(back_populates="product")
