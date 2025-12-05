"""
Items module.
"""

import scrapy

from utils.spider import ProductItem as ParentProductItem


class ProductItem(ParentProductItem):
    # The EAN-13 references of the product.
    #
    # Technically speaking, an EAN corresponds to one unique product, but Auchan
    # sometimes displays multiple EANs on product page.
    eans = scrapy.Field()
