"""
Items module.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ProductItem:
    name: str
    brand: str
    eans: List[str]
    price: str
    url: str
