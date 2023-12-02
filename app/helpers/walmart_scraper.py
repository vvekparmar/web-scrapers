import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup as bs

from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_chrome_driver():
    """ This method is used to get the chrome driver """

    options = uc.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-debugging-port=9222')
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


def get_rating_details(driver):
    try:
        s = bs(driver.page_source, features="lxml")
        rev = s.find('div', {'id': 'item-review-section'})
        if rev:
            total_reviews = rev.select_one('.pt1 a span.ml1.f7.dark-gray.underline').text.strip()[1:-1]

            total_rating = rev.select_one('.w-50 div .f-headline.b').text.strip() + " out of 5"

            rates = rev.select('.list.pl0.w-100 li')
            ratings = {}
            for rate in rates:
                k = rate.select_one('.w5').text.strip()
                v = rate.select_one('.w3').text.strip()
                ratings[k] = v

            rating_based_on_star = ratings
            return total_reviews, total_rating, rating_based_on_star
    except:
        return None, None, None


def get_product_listings(driver, keyword, number_of_products):
    """ This method is used to get the product lists """

    page_num = 1
    product_urls = []
    done_searching = False

    keyword = "+".join(keyword.split(" "))

    while not done_searching:
        url = f"https://www.walmart.com/search?q={keyword}&page={page_num}"
        driver.get(url)

        try:
            if link_tags := WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".ph1 .hide-sibling-opacity"))):

                for elem in link_tags:
                    if len(product_urls) >= number_of_products:
                        done_searching = True
                        break
                    else:
                        link = elem.get_attribute("href")
                        product_urls.append(link)
                page_num += 1
        except Exception as e:
            print(f"[+ Walmart +] Exception raised, {e}")

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
    try:
        if rating_tag := driver.find_element(By.CSS_SELECTOR, "span.rating-number"):
            return rating_tag.text.strip().replace("(", "").replace(")", "")
    except:
        return None


def get_specifications(driver):
    """ This method is used to get the specifications of the product """

    specifications = {}

    if specs_tag := driver.find_element(By.CSS_SELECTOR, ".ph3.pb4.pt1 .nt1").find_elements(By.TAG_NAME, 'div'):
        for spec in specs_tag[::2]:
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
    else:
        highlights = {}
        if highlights_tag := driver.find_elements(By.CSS_SELECTOR, ".pv2 .flex.w-100.mv2 div.w-50"):

            for highlight1 in highlights_tag:
                key = highlight1.find_elements(By.CSS_SELECTOR, ".b.mv1")
                value = highlight1.find_elements(By.CSS_SELECTOR, ".ml3.mv1")
                for data in zip(key, value):
                    key = data[0].text.strip()
                    value = data[1].text.strip()
                    highlights[key] = value

    return highlights


def get_frequent_mentions(driver):
    """ This method is used to get the frequent mentions of the product """

    try:
        element = driver.find_element(By.CSS_SELECTOR, ".overflow-auto")

        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(2)
        driver.find_element(By.CSS_SELECTOR, "#item-review-section button.ph0").click()

    except Exception as e:
        try:
            driver.execute_script("window.scrollTo(1,4500 );")
            driver.find_element(By.CSS_SELECTOR, "#item-review-section button.ph0").click()
        except:
            pass

        pass

    mentions = []

    if mentions_tag := driver.find_elements(By.CSS_SELECTOR, ".overflow-auto .pr1"):
        return [mention.text.strip() for mention in mentions_tag]

    return mentions


def get_product_description(driver):
    """ This method is used to get the product description of the product """

    if description_tag := WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".nb3"))):
        return description_tag.text.strip()
    return ""


def get_color_variants(driver):
    """ This method is used to get the color variants of the product """

    for i in range(0, 3):
        a = driver.find_elements(By.CSS_SELECTOR, f'[data-testid="variant-group-{i}"]')
        if a:
            txt = a[0].find_element(By.CLASS_NAME, "mid-gray.mb2").text.strip()
            if 'Color' in txt:
                color_variants_tag = a[0].find_elements(By.CSS_SELECTOR,
                                                        'button [data-testid="variant-tile"] span.w_iUH7')
                return [color.text.lstrip("selected,").strip() for color in color_variants_tag if
                        "Out of stock" not in color.text.strip()]

    return []


def get_sizes(driver):
    """ This method is used to get the sizes of the product """

    for i in range(0, 3):
        a = driver.find_elements(By.CSS_SELECTOR, f'[data-testid="variant-group-{i}"]')
        if a:
            txt = a[0].find_element(By.CLASS_NAME, "mid-gray.mb2").text.strip()
            if 'size' in txt.lower() or "edition" in txt.lower() or "capacity" in txt.lower():
                color_variants_tag = a[0].find_elements(By.CSS_SELECTOR,
                                                        'button [data-testid="variant-tile"] span.w_iUH7')
                return [color.text.lstrip("selected,").strip() for color in color_variants_tag]

    return []


def get_reviews(driver, number_of_reviews):
    """ This method is used to get the reviews of the product """

    reviews = []
    page_num = 1
    reviews_fetched = False

    rev = driver.find_element(By.CSS_SELECTOR, "#item-review-section")
    list_rev = rev.find_elements(By.CSS_SELECTOR, '.overflow-hidden.nr3.nr1-m li')
    for l_rev in list_rev:
        try:
            l_rev.find_element(By.TAG_NAME, 'button').click()
        except:
            pass
        time.sleep(1)

    for l in list_rev:

        try:
            review_title = l.find_element(By.CSS_SELECTOR, "h3.w_kV33").text
        except:
            review_title = None
        rating = l.find_element(By.CSS_SELECTOR, "span.w_iUH7").text
        try:
            txt = l.find_element(By.CSS_SELECTOR, "span.tl-m.mb3.db-m").text
        except:
            txt = None
        reviews.append({'review_title': review_title, "review_text": txt, "rating": rating})
        if len(reviews) >= number_of_reviews:
            reviews_fetched = True
            return reviews
    try:
        review_link = rev.find_element(By.CSS_SELECTOR, '[link-identifier="seeAllReviews"]').get_attribute('href')
    except:
        return reviews
    reviews_data = []
    while not reviews_fetched:
        url = f"{review_link}?page={page_num}"
        driver.get(url)
        review_list = driver.find_elements(By.CSS_SELECTOR, "li.dib.w-100.mb3")
        if not review_list:
            break
        for rl in review_list:
            try:
                rl.find_element(By.CSS_SELECTOR, 'button.f6.ml1').click()
            except:
                pass
            try:
                review_title = rl.find_element(By.CSS_SELECTOR, "h3.w_kV33").text
            except:
                review_title = None
            rating = rl.find_element(By.CSS_SELECTOR, "span.w_iUH7").text
            try:
                txt = rl.find_element(By.CSS_SELECTOR, "span.tl-m.mb3.db-m").text
            except:
                txt = None
            reviews_data.append({'review_title': review_title, "review_text": txt, "rating": rating})

        if len(reviews_data) >= number_of_reviews:
            reviews_fetched = True
            break

        page_num += 1
    if reviews_data:
        reviews = reviews_data

    return reviews


def scrap_product_data(driver, product_url, keyword, number_of_reviews):
    """ This method is used to scrap the product data """

    print(f"[+ Walmart +] Scraping data from: {product_url}")
    data = {}

    driver.get(product_url)
    dr_link = driver.current_url

    while "blocked" in dr_link:
        driver.quit()
        driver = get_chrome_driver()
        driver.get(product_url)
        time.sleep(2)
        dr_link = driver.current_url

    try:
        title = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#main-title"))).text.strip()
        data['title'] = title
        price = driver.find_element(
            By.CSS_SELECTOR, "[itemprop='price']").text.replace("Now ", "").strip()
        data['price'] = price
        data['SEARCH_KEYWORD'] = keyword
        data['url'] = product_url
        description = get_product_description(driver)
        data['description'] = description
        image_urls = get_images(driver)
        data['images'] = image_urls

        ratings = get_ratings(driver)
        data['ratings'] = ratings
        sizes = get_sizes(driver)
        data['sizes'] = sizes
        color_variants = get_color_variants(driver)
        data['color_variants'] = color_variants
        specifications = get_specifications(driver)
        data['specifications'] = specifications
        quick_highlights = get_highlights(driver)
        data['quick_highlights'] = quick_highlights
        mentions = get_frequent_mentions(driver)
        data["frequent_mentions"] = mentions
        total_reviews, total_rating, rating_based_on_star = get_rating_details(driver)
        data['total_reviews'] = total_reviews
        data['total_rating'] = total_rating
        data['customer_reviews'] = rating_based_on_star
        reviews = get_reviews(driver, number_of_reviews)
        data['reviews'] = reviews

        return data

    except Exception as e:
        print(f"[+ Walmart +] Exception raised, {e}")
        return data


def scrap_walmart(keyword, number_of_products, number_of_reviews):
    """ This is the main method of the scrapper """

    print(f"[+ Walmart +] Search Keyword: {keyword}")

    driver = get_chrome_driver()

    product_links = get_product_listings(driver, keyword, number_of_products)

    print(f"[+ Walmart +] Product Link is found for {keyword}")
    print(f"[+ Walmart +] Links: {product_links}")

    product_information = []
    if product_links:
        for product_url in product_links:
            result = scrap_product_data(driver, product_url, keyword, number_of_reviews)
            product_information.append(result)
    else:
        print("[+ Walmart +] Unable to fetch product links")

    driver.quit()
    return product_information
