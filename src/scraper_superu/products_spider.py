import asyncio
import scrapy
from scrapy import Request, Spider
from urllib.parse import quote_plus
from typing import Dict

from .items import ProductItem
# from playwright.async_api import async_playwright
from .connector_nodriver import ConnectorNodriver

# Name of the cookie used to specify the "journey" ID.
#
# A journey ID is required to get the price on the product pages as it is tied
# to a physical store.
#
# See https://github.com/dataforgoodfr/offseason-proteines-resilientes/issues/2
# for more information.
JOURNEY_COOKIE_NAME = "storeId"


class SuperUProductsSpider:
    """
    Scrapy Spider for the products of the SuperU retail website.
    """

    name = "superu_products"
    allowed_domains = ["www.coursesu.com"]
    start_urls = ["data:,"]
    custom_settings = {}
    cookies=[
                {
                    "domain": "www.coursesu.com",
                    "expirationDate": 1760788969.193743,
                    "hostOnly": "true",
                    "httpOnly": "false",
                    "name": "newsletterDisplayNb",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "false",
                    "storeId": "null",
                    "value": "0"
                },
                {
                    "domain": ".coursesu.com",
                    "expirationDate": 1758198770.193917,
                    "hostOnly": "false",
                    "httpOnly": "true",
                    "name": "__cf_bm",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "false",
                    "storeId": "null",
                    "value": "UOb4zV2b4AY9.joEXJ61.iMJz5pcz1ifWfHPmHIF2RU-1758196970-1.0.1.1-MDKt0p5ZQEEGbdTFFC5z5MQ3EC0pdqzGFomK3_eG3UgFwAsM6ifT2YufcB423Ap0pCaCkAscysXcszCtHHuEViBpQVAcdo_5W.20HmWx4Ck"
                },
                {
                    "domain": "www.coursesu.com",
                    "hostOnly": "true",
                    "httpOnly": "true",
                    "name": "dwsid",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "true",
                    "storeId": "null",
                    "value": "eAmxjxSFBB7r8RALohtJ7zQL9tRurCAvYJOrtOg-nBOYvaodj-ADE0fvqbMtI03nXOm-1lCJu04k0DdlXMACPQ=="
                },
                {
                    "domain": "www.coursesu.com",
                    "hostOnly": "true",
                    "httpOnly": "false",
                    "name": "cquid",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "true",
                    "storeId": "null",
                    "value": "||"
                },
                {
                    "domain": ".coursesu.com",
                    "expirationDate": 1758198786.734987,
                    "hostOnly": "false",
                    "httpOnly": "false",
                    "name": "tfpsi",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "false",
                    "storeId": "null",
                    "value": "ab68e120-d34e-41a9-a050-1bfe8618d6cb"
                },
                {
                    "domain": "www.coursesu.com",
                    "expirationDate": 1789732986,
                    "hostOnly": "true",
                    "httpOnly": "false",
                    "name": "_lm_id",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "false",
                    "storeId": "null",
                    "value": "HS8Y3IFNLKA1H691"
                },
                {
                    "domain": "www.coursesu.com",
                    "expirationDate": 1758198785.319777,
                    "hostOnly": "true",
                    "httpOnly": "false",
                    "name": "availableDeliveryMethods",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "false",
                    "storeId": "null",
                    "value": "drive%2Cdelivery%2Cdelivery%2Cdelivery"
                },
                {
                    "domain": ".coursesu.com",
                    "expirationDate": 1789733069.780824,
                    "hostOnly": "false",
                    "httpOnly": "false",
                    "name": "datadome",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "false",
                    "storeId": "null",
                    "value": "ALkxeBwMbKusWWNEW684SA83K9gRx16NKK~ki2VSp7ZV3_XLdldKv445dwXJyumq0Xl3itGPwIE~d44eHUxafNxFeygZ53tMsf34gMn~ER2W6RMofsNF1FyFwJc37gL7"
                },
                {
                    "domain": "www.coursesu.com",
                    "hostOnly": "true",
                    "httpOnly": "false",
                    "name": "__cq_dnt",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "true",
                    "storeId": "null",
                    "value": "0"
                },
                {
                    "domain": ".coursesu.com",
                    "expirationDate": 1792360974,
                    "hostOnly": "false",
                    "httpOnly": "false",
                    "name": "_cs_c",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "false",
                    "storeId": "null",
                    "value": "1"
                },
                {
                    "domain": ".coursesu.com",
                    "hostOnly": "false",
                    "httpOnly": "false",
                    "name": "_cs_cvars",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "true",
                    "storeId": "null",
                    "value": "%7B%7D"
                },
                {
                    "domain": ".coursesu.com",
                    "expirationDate": 1792283309,
                    "hostOnly": "false",
                    "httpOnly": "false",
                    "name": "_cs_id",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "false",
                    "storeId": "null",
                    "value": "045a620a-28f0-abba-8b1a-4b78c3468458.1758119309.2.1758196987.1758196874.1739955371.1792283309787.1.x"
                },
                {
                    "domain": ".coursesu.com",
                    "expirationDate": 1758198865,
                    "hostOnly": "false",
                    "httpOnly": "false",
                    "name": "_cs_s",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "false",
                    "storeId": "null",
                    "value": "3.5.U.9.1758198865897"
                },
                {
                    "domain": "www.coursesu.com",
                    "expirationDate": 1758197586.912049,
                    "hostOnly": "true",
                    "httpOnly": "false",
                    "name": "checkReservationSlots",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "false",
                    "storeId": "null",
                    "value": "2025-09-18T12%3A11%3A06.881Z"
                },
                {
                    "domain": "www.coursesu.com",
                    "hostOnly": "true",
                    "httpOnly": "false",
                    "name": "cqcid",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "true",
                    "storeId": "null",
                    "value": "bc1iRcJmjanjIXTohieu76NANa"
                },
                {
                    "domain": "www.coursesu.com",
                    "hostOnly": "true",
                    "httpOnly": "false",
                    "name": "dw_dnt",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "true",
                    "storeId": "null",
                    "value": "0"
                },
                {
                    "domain": "www.coursesu.com",
                    "hostOnly": "true",
                    "httpOnly": "false",
                    "name": "dwac_8d8721aecf7af8fe498c1f352b",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "true",
                    "storeId": "null",
                    "value": "HUZDBwW74JFrBPwJQnHsNlFEBFx_ksSg4GY%3D|dw-only|||EUR|false|Europe%2FParis|true"
                },
                {
                    "domain": "www.coursesu.com",
                    "expirationDate": 1773748970.193778,
                    "hostOnly": "true",
                    "httpOnly": "false",
                    "name": "dwanonymous_8ce4ace52d14ef4ce78780bbb2b979c7",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "false",
                    "storeId": "null",
                    "value": "bc1iRcJmjanjIXTohieu76NANa"
                },
                {
                    "domain": "www.coursesu.com",
                    "hostOnly": "true",
                    "httpOnly": "false",
                    "name": "sid",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "true",
                    "storeId": "null",
                    "value": "HUZDBwW74JFrBPwJQnHsNlFEBFx_ksSg4GY"
                },
                {
                    "domain": "www.coursesu.com",
                    "expirationDate": 1765972984.498117,
                    "hostOnly": "true",
                    "httpOnly": "false",
                    "name": "storeId",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": "true",
                    "session": "false",
                    "storeId": "null",
                    "value": "37005"
                }
            ]

    async def start(self, query: str, store_id: str):
        # query: str = getattr(self, "query", None)
        
        if query is None:
            raise AttributeError("Missing 'query' argument")
        
        url: str = "https://www.coursesu.com"
        connector: ConnectorNodriver = ConnectorNodriver()
        await connector.get_page(f"{url}?q={quote_plus(query)}")
       

    def parse(self, response, **kwargs):
        # 'response' contains the page as seen by the browser
        return {"url": response.url}