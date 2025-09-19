"""
Items module.
"""

from dataclasses import dataclass


@dataclass
class ProductItem:
    name: str
    brand: str
    eans: str
    price: str
    url: str
