"""
Items module.
"""

import scrapy


class ProductItem(scrapy.Item):
    # The name of the product.
    name = scrapy.Field()

    # The brand of the product.
    brand = scrapy.Field()

    # The EAN-13 references of the product.
    #
    # Technically speaking, an EAN corresponds to one unique product, but Auchan
    # sometimes displays multiple EANs on product page.
    eans = scrapy.Field()

    # The price of the product.
    price = scrapy.Field()

    # The URL of the product.
    url = scrapy.Field()
