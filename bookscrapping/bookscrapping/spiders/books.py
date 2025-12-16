import scrapy
from scrapy import Spider
from scrapy.http import Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from twisted.internet.defer import Deferred

from ..items import BookscrappingItem


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = webdriver.Chrome()

    def close(self, reason: str) -> Deferred[None] | None:
        self.driver.close()
        return self.close(reason)

    def parse_book(self, response):
        self.driver.get(response.url)
        book = BookscrappingItem()

        book['title'] = self.driver.find_element(By.TAG_NAME, "h1").text

        price_text = self.driver.find_element(By.CSS_SELECTOR, "p.price_color").text
        book['price'] = float(price_text.replace("£", ""))

        stock_text = self.driver.find_element(By.CSS_SELECTOR, "p.instock.availability").text
        book['amount_in_stock'] = int(''.join(filter(str.isdigit, stock_text)))

        rating_element = self.driver.find_element(By.CSS_SELECTOR, "p.star-rating")
        rating_class = rating_element.get_attribute("class").split()[-1]
        book['rating'] = self._convert_rating(rating_class)

        try:
            category_element = self.driver.find_element(By.XPATH, "//ul[@class='breadcrumb']/li[3]/a")
            book['category'] = category_element.text
        except:
            book['category'] = "Unknown"

        try:
            desc_element = self.driver.find_element(By.XPATH, "//div[@id='product_description']/following-sibling::p")
            book['description'] = desc_element.text
        except:
            book['description'] = None

        book['upc'] = self.driver.find_element(By.XPATH, "//th[text()='UPC']/following-sibling::td").text

        yield book

    @staticmethod
    def _convert_rating(rating_text):
        ratings_map = {
            "One": 1,
            "Two": 2,
            "Three": 3,
            "Four": 4,
            "Five": 5
        }
        return ratings_map.get(rating_text, 0)

    def parse(self, response: Response, **kwargs):
        self.driver.get(response.url)
        book_links = self.driver.find_elements(By.CSS_SELECTOR, "article.product_pod h3 a")

        for link in book_links:
            url = link.get_attribute("href")
            yield scrapy.Request(url=url, callback=self.parse_book)

        next_buttons = self.driver.find_elements(By.CSS_SELECTOR, "li.next a")
        if next_buttons:
            next_page_url = next_buttons[0].get_attribute("href")
            yield scrapy.Request(url=next_page_url, callback=self.parse)
