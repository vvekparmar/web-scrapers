import time
import unicodedata
from app import config

from selenium import webdriver
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def get_chrome_driver():
    """ This method is used to get the chrome driver """

    options = Options()
    options.add_argument("headless")
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.implicitly_wait(10)
    return driver


def get_page_source_code(url):
    """ This method is used to get the page source code from the url """

    driver = get_chrome_driver()
    driver.get(url)
    soup = get_soup(driver.page_source)
    return soup


def get_soup(page_source):
    """ This method is used to get the html parser using page source """

    return bs(page_source, 'html.parser')


def remove_unicode_chars(input_string):
    """ This method is used to remove the unicode chars """

    return ''.join(c for c in input_string if unicodedata.category(c)[0] != 'C')


def scrap_product_listing_url(keyword, number_of_products=5):
    """ This method is used to scrap the product list from the url """

    keyword = "+".join(keyword.split(" "))
    page_num = 1
    product_links = []

    searching = True

    while searching:
        url = f"https://www.amazon.com/s?k={keyword}&page={page_num}"
        print(f"[+ Amazon +] Scrapping {url} page {page_num}")

        soup = get_page_source_code(url)
        if soup:
            asin_list_tag = soup.find_all(attrs={'data-asin': True})

            for data_asin in asin_list_tag:
                if asin := data_asin['data-asin']:
                    if len(product_links) != number_of_products:
                        product_links.append(f"https://amazon.com/dp/{asin.strip()}")
                    else:
                        searching = False
            page_num += 1
    return product_links


def get_reviews(reviews_url, number_of_reviews=5):
    """ This method is used to get the product reviews from the review url """

    page_num = 1
    reviews = []

    while True:
        soup = get_page_source_code(reviews_url + "&pageNumber=" + str(page_num))
        reviews_list_tag = soup.select("div.a-section.review.aok-relative")

        if len(reviews) >= number_of_reviews:
            break

        for review in reviews_list_tag:
            review_text = "\n".join([text.get_text(strip=True) for text in review.select(
                ".review-text-content span")])
            reviews.append(clean_text(review_text))

        if len(reviews_list_tag) < 10:
            break

        page_num += 1

    if reviews:
        reviews = [clean_text(text) for text in reviews]
    return reviews[:number_of_reviews]


def clean_text(text):
    """ This method is used to clean text """

    cleaned_text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C')
    cleaned_text = cleaned_text.replace('\n', ' ')
    cleaned_text = cleaned_text.replace(":", "") if cleaned_text.endswith(":") else cleaned_text
    return cleaned_text.strip()


def get_rate_by_feature(soup):
    """ This method is used to get the rate by feature """

    rate_by_feature_tag = soup.select_one("#cr-dp-summarization-attributes")

    rating_by_features = {}
    if rate_by_feature_tag:
        rows = rate_by_feature_tag.select(".a-fixed-right-grid.a-spacing-base")
        for row in rows:
            text = row.select_one(".a-row .a-size-base.a-color-base").get_text(strip=True)
            value = row.select_one(".a-size-base.a-color-tertiary").get_text(strip=True)
            rating_by_features[text] = value
    return rating_by_features


def get_product_details(soup):
    """ This method is used to get the product details """

    details_tag = soup.select("#detailBullets_feature_div ul li .a-list-item")
    details = {}
    for tag in details_tag:
        d = tag.select("span")
        key = clean_text(d[0].get_text(strip=True))
        key = " ".join(c for c in key.split(" ") if c).replace(":", "").strip()
        value = clean_text(d[1].get_text(strip=True))
        value = " ".join(c for c in value.split(" ") if c)
        details[key] = value

    return details


def get_sizes(soup):
    """ This method is used to get the sizes of product """

    sizes = []
    if sizes_list_tag := soup.select_one("#native_dropdown_selected_size_name"):
        size_options = sizes_list_tag.select("option")
        size_options = [option.text.strip() for option in size_options]
        return size_options[1:]
    return sizes


def get_technical_details(soup):
    """ This method is used to get the technical details """

    table_data = {}

    if product_details := soup.select("#prodDetails"):
        product_table_tag = soup.select(".prodDetTable")
        for table_tag in product_table_tag:
            tr = table_tag.select("tr")
            for row in tr:
                key = row.select_one("th").get_text(strip=True)
                value = row.select_one("td").get_text(strip=True)
                table_data[remove_unicode_chars(key)] = remove_unicode_chars(value)

    return table_data


def get_read_review_keyword(soup):
    """ This method is used to read the review keywords """

    if read_review_tag := soup.select_one(".cr-lighthouse-terms"):
        tags = [tag.text.strip() for tag in read_review_tag.select(".a-declarative")]
        return tags
    return []


def get_color_variant(soup):
    """ This method is used to get the color variant keywords """

    color_variants = []
    if color_variant_tag := soup.select_one("#variation_color_name"):
        variants = color_variant_tag.select("li img")
        for variant in variants:
            alt_text = variant.get("alt")
            color_variants.append(alt_text)
    return color_variants


def get_accessories(soup):
    """ This method is used to get the accessories of the product """

    accessories = []
    if variation_tag := soup.select_one(".swatchesSquare"):
        accessories = [var.text.strip() for var in variation_tag.select(
            "li p.a-text-left.a-size-base")]
        return accessories
    return accessories


def get_about_item(soup):
    """ This method is used to get about item """

    about_item = None
    if about_item_tag := soup.select_one("#featurebullets_feature_div"):

        about_item_list_tag = about_item_tag.select("li span.a-list-item")
        about_item = "\n".join([li.text.strip() for li in about_item_list_tag])
        return about_item
    return about_item


def get_size_chart(soup):
    """ This method is used to get the size-chart of the product """

    if size_chart_element := soup.select_one(".apm-centerthirdcol.apm-wrap ul.a-unordered-list.a-vertical"):
        li_item = size_chart_element.select("li span.a-list-item")
        size_chart = [li.text.strip() for li in li_item]
        return size_chart
    return []


def get_image_urls(soup):
    """ This method is used to get the image urls of the product """

    images = []
    if image_container_tag := soup.select_one("#altImages"):

        image_url_tag = image_container_tag.select(
            ".a-spacing-small.item.imageThumbnail.a-declarative img")
        images = []
        for img in image_url_tag:
            i = img.get("src").split(".")
            i = ".".join(i[:-2]) + "." + i[-1]
            images.append(i)
        return images

    return images


def get_customer_reviews(soup):
    """ This method is used to get the customer reviews of the product """

    title_rating_tag = soup.select_one(".cr-widget-TitleRatingsAndHistogram")

    title_ratings = {}
    if title_rating_tag:
        rows = title_rating_tag.select(".a-normal.a-align-center.a-spacing-base tr")
        for row in rows:
            td = row.select("td")
            text = td[0].select_one("span.a-size-base").get_text(strip=True)
            value = td[2].get_text(strip=True)
            title_ratings[text] = value
    return title_ratings


def get_product_overview(soup):
    """ This method is used to get the product overview """

    product_overview = {}
    if overview_tag := soup.select_one("#productOverview_feature_div"):
        rows = overview_tag.select("table tr")
        for row in rows:
            td = row.select("td")
            product_overview[clean_text(td[0].text.strip())] = clean_text(td[1].text.strip())
        return product_overview
    return product_overview


def get_warranty(soup):
    """ This method is used to get the warranty of the product """

    warranty_text = ""
    if warranty_tag := soup.select_one("#productDetails_warranty_support_sections"):
        warranty_text = warranty_tag.text
        return clean_text(warranty_text)
    return warranty_text


def scroll_page_with_pagedown(driver, element):
    """ This method is used to scroll the page down """

    driver.execute_script("arguments[0].scrollIntoView();", element)


def get_total_ratings(soup):
    """ This method is used to get the total rating of product """

    if global_ratings_tag := soup.select_one(".averageStarRatingNumerical .a-color-secondary"):
        ratings = global_ratings_tag.text.strip().split(" ")[0]
        return ratings
    return ""


def get_price(soup):
    """ This method is used to get the price of the product """

    try:
        price = soup.select_one(
            ".a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay .a-offscreen").text.strip()

    except AttributeError:
        price = ""

    return price


def get_product_data(product_url):
    """ This method is used to get the product data """

    driver = get_chrome_driver()
    print(f"[+ Amazon +] Scraping data from {product_url}")

    try:
        driver.get(product_url)
        review_element = driver.find_element(By.CSS_SELECTOR, "#reviewsMedley h2")
        scroll_page_with_pagedown(driver, review_element)
        time.sleep(1)
        soup = get_soup(driver.page_source)
        title = ""
        if title_tag := soup.select_one("h1#title"):
            title = clean_text(title_tag.get_text(strip=True))

        elif title_tag := soup.select_one("#productTitle"):
            title = clean_text(title_tag.text.strip())

        if "No customer reviews".lower() not in soup.text.lower():
            ratings = soup.select_one("#reviewsMedley .a-size-medium").get_text(strip=True)
        else:
            ratings = "N/A"

        size_chart = "N/A"
        if "size chart:" in soup.text.lower():
            size_chart = get_size_chart(soup)

        price = get_price(soup)
        images = get_image_urls(soup)
        description = "\n".join([desc.text.strip() for desc in soup.select("#productDescription span")])
        details = get_product_details(soup)
        sizes = get_sizes(soup)
        rating_by_features = get_rate_by_feature(soup)
        total_ratings = get_total_ratings(soup)

        table_data = get_technical_details(soup)
        category = soup.select_one("li:nth-of-type(1) .a-color-tertiary").get_text(strip=True)
        details.update(table_data)

        read_reviews_keywords = get_read_review_keyword(soup)

        color_variants = get_color_variant(soup)
        about_item = get_about_item(soup)
        warranty = get_warranty(soup)
        accessories = get_accessories(soup)
        product_overview = get_product_overview(soup)

        customer_reviews = get_customer_reviews(soup)

        reviews = []
        if reviews_url := soup.select_one("#cr-pagination-footer-0 .a-text-bold"):
            reviews_url = "https://www.amazon.com" + reviews_url.get("href")
            reviews = get_reviews(reviews_url, config.NUMBER_REVIEWS)

        data = {
            "title": title,
            "category": category,
            "price": price,
            "ratings": ratings,
            "images": images,
            "description": description,
            "url": product_url,
            "reviews": reviews,
            "warranty": warranty,
            "product_info": details,
            "customer_reviews": customer_reviews,
            "sizes": sizes,
            "size_chart": size_chart,
            "about_item": about_item,
            "read_review_keywords": read_reviews_keywords,
            "SEARCH_KEYWORD": config.SEARCH_KEYWORD,
            "color_variants": color_variants,
            "rating_by_features": rating_by_features,
            "accessories": accessories,
            "overview": product_overview,
            "total_ratings": total_ratings,
        }
        return data

    except Exception as e:
        print(f"[+ Amazon +] Exception raised, {e}")

    finally:
        driver.quit()


def scrap_amazon():
    """ This is the main method of the scrapper """

    product_links = scrap_product_listing_url(config.SEARCH_KEYWORD, config.NUMBER_OF_PRODUCTS)

    print(f"[+ Amazon +] Product Link is found for {config.SEARCH_KEYWORD})")
    print(f"[+ Amazon +] Links: {product_links}")

    product_information = []
    if product_links:
        for product_url in product_links:
            result = get_product_data(product_url)
            product_information.append(result)
    else:
        print("[+ Amazon +] Unable to fetch product links")

    return product_information
