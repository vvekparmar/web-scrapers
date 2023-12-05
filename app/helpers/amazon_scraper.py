import time
import unicodedata
from bs4 import BeautifulSoup as bs
import undetected_chromedriver as uc

from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def get_chrome_driver():
    """ This method is used to get the chrome driver """

    options = Options()
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


def get_page_source_code(driver, url):
    """ This method is used to get the page source code from the url """

    driver.get(url)

    soup = get_soup(driver.page_source)
    return soup


def get_soup(page_source):
    """ This method is used to get the html parser using page source """

    return bs(page_source, 'html.parser')


def remove_unicode_chars(input_string):
    """ This method is used to remove the unicode chars """

    return ''.join(c for c in input_string if unicodedata.category(c)[0] != 'C')


def scrap_product_listing_url(driver, keyword, number_of_products=5):
    """ This method is used to scrap the product list from the url """

    keyword = "+".join(keyword.split(" "))
    page_num = 1
    product_links = []

    searching = True

    while searching:
        url = f"https://www.amazon.com/s?k={keyword}&page={page_num}"
        print(f"[+ Amazon +] Scrapping {url} page {page_num}")

        soup = get_page_source_code(driver, url)
        if soup:
            asin_list_tag = soup.find_all('div',attrs={'class': 'sg-col-4-of-24 sg-col-4-of-12 s-result-item s-asin sg-col-4-of-16 sg-col s-widget-spacing-small sg-col-4-of-20'})
            if not asin_list_tag:
                asin_list_tag = soup.find_all('div',attrs={'class': 's-result-item'})
            for data_asin in asin_list_tag:
                if asin := data_asin['data-asin']:

                    if len(product_links) != number_of_products:
                        product_links.append(f"https://amazon.com/dp/{asin.strip()}")

                    else:
                        searching = False
                        break
            page_num += 1

    return product_links


def get_reviews(driver, reviews_url, number_of_reviews=5):
    """ This method is used to get the product reviews from the review url """

    page_num = 1
    reviews = []

    while True:
        if len(reviews) >= number_of_reviews:
            break
        soup = get_page_source_code(driver, reviews_url + "&pageNumber=" + str(page_num))
        reviews_list_tag = soup.select("div.a-section.review.aok-relative")

        for review in reviews_list_tag:
            review_title = review.find('a', {'data-hook': "review-title"}).find_all('span')
            review_title = [r.text.strip() for r in review_title][-1]

            review_text = "\n".join([text.get_text(strip=True) for text in review.select(
                ".review-text-content span")])

            rating_element = review.find('i', {'class': 'a-icon-star'})

            rating = rating_element.find('span', {'class': 'a-icon-alt'}).text
            txt = clean_text(review_text)

            helpful_element = review.find('span', {'data-hook': 'helpful-vote-statement'})
            if helpful_element:
                helpful_text = extract_number_from_string(helpful_element.text)
            else:
                helpful_text = 0

            reviews.append(
                {'review_title': review_title, "review_text": txt, "rating": rating, "helpful_count": helpful_text})

            if len(reviews) >= number_of_reviews:
                break

        if len(reviews_list_tag) < 10:
            break

        page_num += 1

    return reviews[:number_of_reviews]


def clean_text(text):
    """ This method is used to clean text """

    cleaned_text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C')
    cleaned_text = cleaned_text.replace('\n', ' ')
    cleaned_text = cleaned_text.replace(":", "") if cleaned_text.endswith(":") else cleaned_text
    cleaned_text = cleaned_text.replace("\xa0", "")
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
    s = soup.find_all('li', attrs={'class': 'swatch-list-item-text'})
    for p in s:
        sizes.append(p.find('span', {"class": "a-size-base swatch-title-text-display swatch-title-text"}).text.strip())
    sizes = [s for s in sizes if s]
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


def get_read_review_keyword(driver, soup):
    """ This method is used to read the review keywords """

    if read_review_tag := soup.select_one(".cr-lighthouse-terms"):
        tags = [tag.text.strip() for tag in read_review_tag.select(".a-declarative")]
        return tags
    else:
        review_element = driver.find_element(By.CSS_SELECTOR, "#reviewsMedley h2")
        scroll_page_with_pagedown(driver, review_element)
        time.sleep(1)
        soup = get_soup(driver.page_source)
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
    else:

        if color_variant_tag := soup.select_one("#tp-inline-twister-dim-values-container"):
            variants = color_variant_tag.select("li img")
            for variant in variants:
                alt_text = variant.get("alt")
                color_variants.append(alt_text)
            color_variants = [c for c in color_variants if c]
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

    about_item = ""
    if about_item_tag := soup.select_one("#featurebullets_feature_div"):

        about_item_list_tag = about_item_tag.select("li span.a-list-item")
        about_item = "\n".join([li.text.strip() for li in about_item_list_tag])
        return about_item
    else:
        if about_item_tag := soup.select_one("#productFactsDesktopExpander"):
            about_item_list_tag = about_item_tag.select("li span.a-list-item")
            about_item = "\n".join([li.text.strip() for li in about_item_list_tag])
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


def get_customer_retry_reviews(soup):
    title_rating_tag = soup.select_one('div', {'id': 'cm_cr_dp_d_rating_histogram'})

    title_ratings = {}
    if title_rating_tag:
        rows = title_rating_tag.select(".a-normal.a-align-center.a-spacing-base tr")
        for row in rows:
            td = row.select("td")
            text = td[0].get_text(strip=True)
            value = td[2].get_text(strip=True)
            title_ratings[text] = value
    return title_ratings


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
    else:
        if overview_tag := soup.select_one("#productFactsDesktopExpander"):
            product_overview = {}
            overview_list_tag = overview_tag.find_all('div', {'class': "a-fixed-left-grid product-facts-detail"})
            for a in overview_list_tag:
                lr = [it.text.strip() for it in a.find_all('span', {'class': 'a-color-base'})]
                product_overview[lr[0]] = lr[1]
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
        if not price:
            price = soup.select_one(
                ".a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay").find('span', {
                "aria-hidden": "true"}).text.strip()

    except AttributeError:
        price = soup.select(".a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen")
        price = [p.text.strip() for p in price]
        price = '-'.join(price)

    return price


def extract_number_from_string(input_string):
    word_to_number = {
        'one': 1,
        'two': 2,
        'three': 3,
        'four': 4,
        'five': 5,
        'six': 6,
        'seven': 7,
        'eight': 8,
        'nine': 9,
        'ten': 10
    }

    words = input_string.split()
    for word in words:
        try:
            x = int(word)
            return x
        except Exception:
            word_lower = word.lower()
            if word_lower in word_to_number:
                return word_to_number[word_lower]

    return 0


def get_product_data(driver, product_url, keyword, number_of_reviews):
    """ This method is used to get the product data """

    data = {}

    print(f"[+ Amazon +] Scraping data from {product_url}")
    try:
        driver.get(product_url)
        review_element = driver.find_element(By.CSS_SELECTOR, "#reviewsMedley h2")
        scroll_page_with_pagedown(driver, review_element)
        time.sleep(1)
        soup = get_soup(driver.page_source)
        if title_tag := soup.select_one("h1#title"):
            title = clean_text(title_tag.get_text(strip=True))
            data["title"] = title

        elif title_tag := soup.select_one("#productTitle"):
            title = clean_text(title_tag.text.strip())
            data["title"] = title
        data["url"] = product_url

        if "No customer reviews".lower() not in soup.text.lower():
            ratings = soup.select_one("#reviewsMedley .a-size-medium").get_text(strip=True)
        else:
            ratings = "N/A"
        data["ratings"] = ratings

        size_chart = "N/A"
        if "size chart:" in soup.text.lower():
            size_chart = get_size_chart(soup)
        data["size_chart"] = size_chart

        price = get_price(soup)
        data['price'] = price

        images = get_image_urls(soup)
        data["images"] = images

        description = "\n".join([desc.text.strip() for desc in soup.select("#productDescription span")])
        if not description:
            try:
                description = soup.find('div', {'class': 'aplus-v2 desktop celwidget'}).text.strip()
                description = clean_text(description)
            except Exception:
                description = ""
        data["description"] = description

        details = get_product_details(soup)
        sizes = get_sizes(soup)
        data["sizes"] = sizes
        rating_by_features = get_rate_by_feature(soup)
        data["rating_by_features"] = rating_by_features
        total_ratings = get_total_ratings(soup)
        data["total_ratings"] = total_ratings

        table_data = get_technical_details(soup)
        category = soup.select_one("li:nth-of-type(1) .a-color-tertiary").get_text(strip=True)
        data["category"] = category

        details.update(table_data)
        data["product_info"] = details

        read_reviews_keywords = get_read_review_keyword(driver, soup)
        data["read_review_keywords"] = read_reviews_keywords

        color_variants = get_color_variant(soup)
        data["color_variants"] = color_variants
        about_item = get_about_item(soup)
        data["about_item"] = about_item
        warranty = get_warranty(soup)
        data["warranty"] = warranty
        accessories = get_accessories(soup)
        data["accessories"] = accessories
        product_overview = get_product_overview(soup)
        data["overview"] = product_overview

        customer_reviews = get_customer_reviews(soup)
        if not customer_reviews:
            customer_reviews = get_customer_retry_reviews(soup)
        data["customer_reviews"] = customer_reviews
        data["SEARCH_KEYWORD"] = keyword

        if reviews_url := soup.select_one("#cr-pagination-footer-0 .a-text-bold"):
            reviews_url = "https://www.amazon.com" + reviews_url.get("href")
            reviews = get_reviews(driver, reviews_url, number_of_reviews)
        else:
            reviews_url = "https://www.amazon.com" + soup.find('a', {'data-hook': "see-all-reviews-link-foot"})['href']
            reviews = get_reviews(driver, reviews_url, number_of_reviews)
        data["reviews"] = reviews

        return data
    except Exception as e:
        print(f"[+ Amazon +] Exception raised, {e}")
        return data


def scrap_amazon(keyword, number_of_products, number_of_reviews):
    """ This is the main method of the scrapper """

    print(f"[+ Amazon +] Search Keyword: {keyword}")

    driver = get_chrome_driver()

    product_links = scrap_product_listing_url(driver, keyword, number_of_products)

    print(f"[+ Amazon +] Product Link is found for {keyword}")
    print(f"[+ Amazon +] Links: {product_links}")

    product_information = []
    if product_links:
        for product_url in product_links:
            result = get_product_data(driver, product_url, keyword, number_of_reviews)
            product_information.append(result)
    else:
        print("[+ Amazon +] Unable to fetch product links")

    driver.quit()
    return product_information
