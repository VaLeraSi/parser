import logging
import csv
import os

import bs4
import requests

from init import ParseResult, HEADERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("parser_metro")

dir_path = os.path.dirname(os.path.realpath(__file__))
file_name = "test.csv"
path = os.path.join(dir_path, file_name)


class Client:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36",
            "Accept-Language": "ru",
        }
        self.result = []

    def loading(self, page=1):
        url = f"https://online.metro-cc.ru/category/molochnye-prodkuty-syry-i-yayca/syry?page={page}"
        result = self.session.get(url=url)
        result.raise_for_status()
        return result.text

    def parse_page(self, text: str):
        soup = bs4.BeautifulSoup(text, "lxml")
        container = soup.select(
            "div.catalog-2-level-product-card.product-card.subcategory-or-type__products-item.with-prices-drop"
        )
        for block in container:
            if not block.find(
                "button", class_="catalog-2-level-product-card__button--only-tc"
            ):
                self.parse_product(block=block)

    def parse_product(self, block):
        id = block.get("id")
        if not id:
            logger.error("no id")
            return

        url_block = block.select_one("a.product-card-photo__link.reset-link")
        if not url_block:
            logger.error("no url_block")
            return
        url = url_block.get("href")
        if not url:
            logger.error("no href")
            return
        full_url = "https://online.metro-cc.ru" + url

        product_page_result = self.session.get(url=full_url)
        product_page_result.raise_for_status()

        product_soup = bs4.BeautifulSoup(product_page_result.text, "lxml")

        container = product_soup.select(
            "div.product-attributes.product-page-content__attributes-short.style--product-page-short-list"
        )
        for product_soup in container:
            self.parse_product(block=product_soup)

        attributes_list_items = product_soup.select("li.product-attributes__list-item")

        brand_name = None
        for item in attributes_list_items:
            if "Бренд" in item.text:
                brand_link = item.find_next("a")
                if brand_link:
                    brand_name = brand_link.text.strip()
                break

        name = block.select_one("span.product-card-name__text")
        if not name:
            logger.error("no name")

        name = name.text.strip()

        actual_price_wrapper = block.select_one(
            "div.product-unit-prices__actual-wrapper"
        )
        price = actual_price_wrapper.select_one(
            "span.product-price__sum-rubles"
        ).text.strip()
        promo_price = None
        old_price_wrapper = block.select_one("div.product-unit-prices__old-wrapper")
        if old_price_wrapper:
            old_price = old_price_wrapper.select_one("span.product-price__sum-rubles")
            if old_price:
                old_price = old_price.text.strip()
                promo_price = price
                price = old_price
            else:
                promo_price = None
                price = price

        self.result.append(
            ParseResult(
                id=id,
                brand=brand_name,
                name=name,
                url=full_url,
                price=price,
                promo_price=promo_price,
            )
        )

        logger.debug("%s, %s", full_url, name)
        logger.debug("-" * 100)

    def save_result(self):
        with open(path, "w") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(HEADERS)
            for item in self.result:
                writer.writerow(item)

    def run(self):
        page = 1
        while True:
            text = self.loading(page)
            self.parse_page(text=text)
            page += 1
            if page > 1:
                break

        logger.info(f"Получили {len(self.result)} товаров")
        self.save_result()
