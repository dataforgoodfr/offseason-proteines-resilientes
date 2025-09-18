import scrapy


class ProductsSpiderSpider(scrapy.Spider):
    name = "products_spider"
    allowed_domains = ["coursesu.com"]
    start_urls = ["https://www.coursesu.com/recherche?q=poulet"]

    def parse(self, response):
        pass
