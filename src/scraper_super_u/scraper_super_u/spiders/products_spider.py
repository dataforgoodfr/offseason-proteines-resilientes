import scrapy


class ProductsSpiderSpider(scrapy.Spider):
    name = "products_spider"
    allowed_domains = ["scrapingclub.com"]
    start_urls = ["https://scrapingclub.com/exercise/list_infinite_scroll/"]

    def parse(self, response):
        pass
