import requests
import unicodedata

from bs4 import BeautifulSoup as BS
from fake_useragent import UserAgent
from selenium_stealth import stealth
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver import Firefox


def get_firefox_driver():
    """ This method is used to get the Firefox driver """

    options = FirefoxOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-dev-shm-usage')

    driver = Firefox(options=options)

    return driver


def get_random_user_agent():
    """ This method is used to get the random user agent """

    user_agent = UserAgent()
    return user_agent.random


def get_chrome_driver():
    """ This method is used to get the chrome driver """

    options = uc.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument(f"user-agent={get_random_user_agent()}")
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = uc.Chrome(use_subprocess=True, options=options)

    stealth(driver,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36',
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    return driver


def get_page_source_code(url):
    """ This method is used to get the page source code from the url """

    header = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Safari/537.3"}
    response = requests.get(url, headers=header)

    soup = BS(response.content, "html.parser")
    return soup


def get_item_specification(soup):
    """ This method is used to get the specification of the items """

    if item_specific_container := soup.select_one(".ux-layout-section-evo__item--table-view"):
        keys = item_specific_container.select(".ux-labels-values__labels")
        values = item_specific_container.select(".ux-labels-values__values")
        if keys:
            data = {}
            for key, value in zip(keys, values):
                data[key.text.strip()] = value.select_one("span.ux-textspans").text.strip()
            return data
        return {}


def get_item_description(product_id):
    """ This method is used to get the item description """

    url = f"https://vi.vipr.ebaydesc.com/ws/eBayISAPI.dll?ViewItemDescV4&item={product_id}"
    soup = get_page_source_code(url)
    try:
        description = soup.select("td")[-1].text.strip()
        if description:
            return description
        else:
            des = soup.find('div', {'id': 'ds_div'}).text.strip()
            return des

    except Exception as e:
        print(f"[+ Ebay +] Exception raised, {e}")
        return "N/A"


def get_product_images(soup):
    """ This method is used to get the product images """

    image_urls = []
    if images_tag := soup.select(".ux-image-filmstrip-carousel img"):
        image_urls = {image.get("src").replace("l64.jpg", "l1600.jpg") for image in images_tag}
        return list(image_urls)
    else:
        buttons = soup.find_all('button', {'class': 'ux-image-grid-item'})

        for but in buttons:
            try:
                image_urls.append(but.img.get("src").replace("l64.jpg", "l1600.jpg"))
            except:
                image_urls.append(but.img.get("data-src").replace("l64.jpg", "l1600.jpg"))

    return image_urls


def get_seller_username(soup):
    """ This method is used to get the seller username """

    if contact := soup.select_one(
            ".d-stores-info-categories__container__action .d-stores-info-categories__container__action__contact.fake-btn.fake-btn--secondary"):
        return contact.get("href").split("&")[2].split("=")[-1]


def get_seller_rating(soup):
    """ This method is used to get the seller ratings """

    if seller_rating_tag := soup.select_one(".fdbk-seller-rating__detailed-list"):
        ratings = seller_rating_tag.select(".fdbk-detail-seller-rating")
        rating_data = {}
        for rating in ratings:
            rating_text = rating.select_one(".fdbk-detail-seller-rating__label").text.strip()
            rating_value = rating.select_one(".fdbk-detail-seller-rating__value").text.strip()
            rating_data[rating_text] = rating_value
        return rating_data
    return None


def get_stock(soup):
    """ This method is used to get the stock of the product """

    try:
        return soup.select_one(".d-quantity__availability").text.strip()
    except AttributeError as e:
        print(f"[+ Ebay +] Exception raised, {e}")
        return "N/A"


def get_title(soup):
    """ This method is used to get the title of the product """

    try:
        return soup.select_one(".x-item-title__mainTitle .ux-textspans--BOLD").text.strip()
    except AttributeError as e:
        print(f"[+ Ebay +] Exception raised, {e}")
        return "N/A"


def get_price(soup):
    """ This method is used to get the price of the product """

    try:
        price = soup.select_one(".x-price-primary .ux-textspans").text.strip()
        return price
    except AttributeError as e:
        print(f"[+ Ebay +] Exception raised, {e}")
        return "N/A"


def get_color_variants(soup):
    """ This method is used to get the color variants """

    if colors_tag := soup.select('[selectboxlabel*="Colour"] option'):
        colors = [color.text.strip() for color in colors_tag if "Select" not in color.text.strip()]
        return colors
    if colors_tag := soup.select('[selectboxlabel*="Color"] option'):
        colors = [color.text.strip() for color in colors_tag if "Select" not in color.text.strip()]
        return colors
    return []


def get_size_variants(soup):
    """ This method is used to get the size variants """

    if sizes_tag := soup.select('[selectboxlabel*="Size"] option'):
        sizes = [size.text.strip()
                 for size in sizes_tag if "Select" not in size.text.strip()]
        sizes = [s.replace("\xa0", "") for s in sizes]
        return sizes
    return []


def get_reviews(driver, soup, seller_username, product_id, number_of_reviews):
    """ This method is used to get the reviews the product """

    feedback = soup.find('div', {'class': "fdbk-detail-list"})
    if not feedback:
        return []
    comments = feedback.find_all('div', {'class': 'fdbk-container__details__comment'})
    comments = [c.text.strip() for c in comments]

    if number_of_reviews <= len(comments):
        return comments[:number_of_reviews]

    reviews = comments.copy()
    page_num = 1
    reviews_fetched = False

    while not reviews_fetched:
        url = f"https://www.ebay.com/fdbk/feedback_profile/{seller_username}?filter=feedback_page%3ARECEIVED_AS_SELLER&sort=TIME&page_id={page_num}&limit=200&q={product_id}"
        driver.get(url)
        if driver.title == "Security Measure":
            driver.quit()
            driver = get_firefox_driver()
            print("[+ Ebay +] Getting chrome driver for scraping reviews...")
            continue
        else:
            if "This member has not received any feedback comments." in driver.page_source:
                return []

            feedback_tag = driver.find_elements(By.CSS_SELECTOR, ".card__text")
            for review in feedback_tag[3:]:
                if len(reviews) >= number_of_reviews:
                    reviews_fetched = True
                    break
                else:
                    reviews.append(review.text.strip())
            if not feedback_tag:
                reviews_fetched = True
            page_num += 1

    return reviews[:number_of_reviews]


def scrap_product_urls(keyword, number_of_products):
    """ This method is used to scrap the product urls """

    keyword = "+".join(keyword.split(" "))
    page_num = 1
    url = f"https://www.ebay.com/sch/i.html?_from=R40&_nkw={keyword}&_sacat=0&LH_TitleDesc=0&_pgn={page_num}"
    soup = get_page_source_code(url)
    if links_tag := soup.select(".clearfix > .s-item__pl-on-bottom .s-item__link"):
        return [url.get("href") for url in links_tag][:number_of_products]
    return None


def clean_text(text):
    """ This method is used to clean text """

    cleaned_text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C')
    cleaned_text = cleaned_text.replace('\n', ' ')
    cleaned_text = cleaned_text.replace(":", "") if cleaned_text.endswith(":") else cleaned_text
    cleaned_text = cleaned_text.replace("\xa0", "")
    return cleaned_text.strip()


def scrap_product_data(driver, product_url, keyword, number_of_reviews):
    """ This method is used to scrap the product data """

    print(f"[+ Ebay +] Scraping data from: {product_url}")

    soup = get_page_source_code(product_url)
    title = get_title(soup)
    price = get_price(soup)
    stock = get_stock(soup)
    sizes = get_size_variants(soup)
    colors = get_color_variants(soup)
    seller_ratings = get_seller_rating(soup)
    product_images = get_product_images(soup)
    seller_username = get_seller_username(soup)

    items_specific_details = get_item_specification(soup)
    product_id = product_url.split("?")[0].split("/")[-1]
    product_description = get_item_description(product_id)
    product_description = clean_text(product_description)
    reviews = get_reviews(driver, soup, seller_username, product_id, number_of_reviews)

    data = {
        "product_id": product_id,
        "SEARCH_KEYWORD": keyword,
        "title": title,
        "price": price,
        "description": product_description,
        "about_item": items_specific_details,
        "color_variants": colors,
        "sizes": sizes,
        "images": product_images,
        "stock": stock,
        "url": product_url,
        "seller_ratings": seller_ratings,
        "reviews": reviews,
    }
    return data


def scrap_ebay(keyword, number_of_products, number_of_reviews):
    """ This method is used to scrap ebay information """

    print(f"[+ Ebay +] Search Keyword: {keyword}")

    driver = get_firefox_driver()

    product_links = scrap_product_urls(keyword, number_of_products)
    print(f"[+ Ebay +] Product Link is found for {keyword}")
    print(f"[+ Ebay +] Links: {product_links}")

    data = []
    if product_links:
        for link in product_links:
            product_details = scrap_product_data(driver, link, keyword, number_of_reviews)
            data.append(product_details)
    else:
        print("[+ Ebay +] Unable to fetch product links")

    driver.quit()
    return data
