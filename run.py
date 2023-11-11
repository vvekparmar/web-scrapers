import sys

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

sys.path.append('app/app/helpers')
from ebay_scraper import scrap_ebay
from amazon_scraper import scrap_amazon

fastapi_app = FastAPI()


class RequestBody(BaseModel):
    keyword: str
    number_of_products: int
    number_of_reviews: int


@fastapi_app.post('/amazon-scraper')
def amazon_scrapper(data: RequestBody):
    try:
        product_info = scrap_amazon(data.keyword, data.number_of_products, data.number_of_reviews)
        return product_info
    except Exception:
        return {}

@fastapi_app.post('/ebay-scraper')
def ebay_scrapper(data: RequestBody):
    try:
        product_info = scrap_ebay(data.keyword, data.number_of_products, data.number_of_reviews)
        return product_info
    except Exception:
        return {}


if __name__ == "__main__":
    try:
        uvicorn.run("run:fastapi_app", host="0.0.0.0")
    except Exception as e:
        print(f"Server exit with error: {e}")
