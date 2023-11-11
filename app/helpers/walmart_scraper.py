import time
from app import config
from fake_useragent import UserAgent
from selenium_stealth import stealth

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC


def get_random_user_agent():
    """ This method is used to get the random user agent """

    user_agent = UserAgent()
    return user_agent.random


def get_chrome_driver(use_user_agent=False):
    """ This method is used to get the chrome driver """

    options = Options()

    if use_user_agent:
        options.add_argument(f"user-agent={get_random_user_agent()}")

    options.add_argument("start-maximized")
    options.add_argument("headless")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    return driver


def get_product_listings(keyword):
    """ This method is used to get the product lists """

    page_num = 1
    product_urls = []
    done_searching = False

    driver = get_chrome_driver(use_user_agent=True)
    keyword = "+".join(keyword.split(" "))

    while not done_searching:
        url = f"https://www.walmart.com/search?q={keyword}&page={page_num}"
        driver.get(url)

        try:
            if link_tags := WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".ph1 .hide-sibling-opacity"))):

                for elem in link_tags:
                    if len(product_urls) >= config.NUMBER_OF_PRODUCTS:
                        done_searching = True
                        break
                    else:
                        link = elem.get_attribute("href")
                        product_urls.append(link)
                page_num += 1
        except Exception as e:
            print(f"[+ Walmart +] Exception raised, {e}")

    driver.quit()
    return product_urls


def get_images(driver):
    """ This method is used to get the images of the product """

    image_tag = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, "[data-testid='media-thumbnail'] img")))
    image_urls = [img.get_attribute('src').split(".jpeg")[
        0] + ".jpeg?odnHeight=2000&odnWidth=2000&odnBg=FFFFFF" for img in image_tag]

    return image_urls


def get_ratings(driver):
    """ This method is used to get the ratings of the product """

    if rating_tag := driver.find_element(By.CSS_SELECTOR, "span.rating-number"):
        return rating_tag.text.strip().replace("(", "").replace(")", "")


def get_specifications(driver):
    """ This method is used to get the specifications of the product """

    specifications = {}
    if specs_tag := driver.find_elements(By.CSS_SELECTOR, ".ph3.pb4.pt1 .nt1"):
        for spec in specs_tag:
            key = spec.find_element(By.CSS_SELECTOR, "h3").text.strip()
            value = spec.find_element(By.CSS_SELECTOR, ".mv0.lh-copy.f6.mid-gray").text.strip()
            specifications[key] = value
    return specifications


def get_highlights(driver):
    """ This method is used to get the highlights of the product """

    highlights = {}
    if highlights_tag := driver.find_elements(By.CSS_SELECTOR, ".pv2 .flex.w-100.mv2 li"):
        for highlight in highlights_tag:
            data = highlight.find_elements(By.CSS_SELECTOR, "div")
            key = data[0].text.strip()
            value = data[1].text.strip()
            highlights[key] = value
    return highlights


def get_frequent_mentions(driver):
    """ This method is used to get the frequent mentions of the product """

    try:
        if see_more_btn := driver.find_element(By.CSS_SELECTOR, "#item-review-section .ph0"):
            see_more_btn.click()

    except NoSuchElementException:
        print(f"[+ Walmart +] Exception raised, NoSuchElementException")

    mentions = []
    if mentions_tag := driver.find_elements(By.CSS_SELECTOR, ".w_3hhZ"):
        return [mention.text.strip().replace("\n", "") for mention in mentions_tag]

    return mentions


def get_product_description(driver):
    """ This method is used to get the product description of the product """

    if description_tag := WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".nb3"))):
        return description_tag.text.strip()
    return ""


def get_color_variants(driver):
    """ This method is used to get the color variants of the product """

    if color_variants_tag := driver.find_elements(By.CSS_SELECTOR, '[data-testid="variant-group-0"] button [data-testid="variant-tile"] span.w_iUH7'):
        return [color.text.split(", ")[-2] for color in color_variants_tag if "Out of stock" not in color.text.strip()]
    return []


def get_sizes(driver):
    """ This method is used to get the sizes of the product """

    if sizes_tag := driver.find_elements(By.CSS_SELECTOR, '[data-testid="variant-group-1"] [data-testid="variant-tile"] [aria-hidden="true"]'):
        return [size.text.strip() for size in sizes_tag]
    return []


def get_reviews(driver):
    """ This method is used to get the reviews of the product """

    reviews = []
    page_num = 1
    reviews_fetched = False

    while not reviews_fetched:
        url = f"https://www.walmart.com/reviews/product/363405465?page={page_num}"
        driver.get(url)
        if reviews_tag := driver.find_elements(By.CSS_SELECTOR, ".db-m"):
            for elem in reviews_tag:
                if len(reviews) >= config.NUMBER_REVIEWS:
                    reviews_fetched = True
                    break
                else:
                    reviews.append(elem.text.strip())
            page_num += 1
        else:
            break

    return reviews


def scrap_product_data(product_url):
    """ This method is used to scrap the product data """

    print(f"[+ Walmart +] Scraping data from: {product_url}")

    driver = get_chrome_driver()
    driver.get(product_url)

    try:
        title = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#main-title"))).text.strip()
        price = driver.find_element(
            By.CSS_SELECTOR, "[itemprop='price']").text.replace("Now ", "").strip()

        description = get_product_description(driver)
        image_urls = get_images(driver)
        ratings = get_ratings(driver)
        sizes = get_sizes(driver)
        color_variants = get_color_variants(driver)
        specifications = get_specifications(driver)
        quick_highlights = get_highlights(driver)
        mentions = get_frequent_mentions(driver)
        reviews = get_reviews(driver)

        data = {
            "title": title,
            "description": description,
            "url": product_url,
            "price": price,
            "color_variants": color_variants,
            "sizes": sizes,
            "images": image_urls,
            "ratings": ratings,
            "frequent_mentions": mentions,
            "specifications": specifications,
            "quick_highlights": quick_highlights,
            "reviews": reviews,
        }
        driver.quit()
        return data
    except Exception as e:
        print(f"[+ Walmart +] Exception raised, {e}")


def scrap_walmart():
    """ This method is used to scrap walmart information """

    print(f"[+ Walmart +] Search Keyword: {config.SEARCH_KEYWORD}")
    product_links = get_product_listings(config.SEARCH_KEYWORD)
    print(f"[+ Walmart +] Product Link is found for {config.SEARCH_KEYWORD}")
    print(f"[+ Walmart +] Links: {product_links}")

    data = []
    if product_links:
        for link in product_links:
            product_details = scrap_product_data(link)
            data.append(product_details)
    else:
        print("[+ Walmart +] Unable to fetch product links")

    return data


scrap_walmart()