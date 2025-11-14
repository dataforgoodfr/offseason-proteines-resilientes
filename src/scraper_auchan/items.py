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

    # Whether or not the price is discounted.
    discounted = scrapy.Field()

    # The discounted price of the product.
    discounted_price = scrapy.Field()

    # Quantity of food product.
    quantity = scrapy.Field()

    # Quantity unit (either a weight or a volume).
    quantity_unit = scrapy.Field()

    # The URL of the product.
    url = scrapy.Field()
