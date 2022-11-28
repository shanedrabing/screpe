__author__ = "Shane Drabing"
__license__ = "MIT"
__version__ = "0.0.2"
__email__ = "shane.drabing@gmail.com"


# IMPORTS


import atexit
import concurrent.futures
import pickle
import os
import time

import bs4
import requests
import selenium.webdriver

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW


# CONSTANTS


USER_MOZ = "Mozilla/5.0 (Windows NT 5.1; rv:52.0) Gecko/20100101 Firefox/103.0"
HEADERS_MOZ = {"User-Agent": USER_MOZ}

BY_XPATH = selenium.webdriver.common.by.By.XPATH
BY_SELECTOR = selenium.webdriver.common.by.By.CSS_SELECTOR


# CLASSES


class mem:
    pass


class BodaciousSoup(bs4.BeautifulSoup):
    def select_one_attr(self, selector, attr):
        return safe_attr(self.select_one(selector), attr)

    def select_attr(self, selector, attr):
        return [safe_attr(node, attr) for node in self.select(selector)]

    def select_one_text(self, selector):
        return node_text(self.select_one(selector))

    def select_text(self, selector):
        return list(map(node_text, self.select(selector)))


class Cache:
    def __init__(self):
        self.dct = dict()

    def access(self, key, fallback):
        if key not in self.dct:
            value = fallback()
            if value is None:
                return
            self.dct[key] = value
        return self.dct[key]

    def save(self, fpath):
        with open(fpath, "wb") as fh:
            pickle.dump(self.dct, fh)

    def load(self, fpath):
        with open(fpath, "rb") as fh:
            self.dct = pickle.load(fh)


# FUNCTIONS (GENERAL)


def safe_attr(obj, attr):
    try:
        return obj[attr]
    except KeyError:
        pass


def node_text(node):
    return " ".join(node.get_text(" ").split())


def cook(html):
    return BodaciousSoup(html, "lxml")


def thread(f, *args):
    with concurrent.futures.ThreadPoolExecutor() as exe:
        return list(exe.map(f, *args))


def rate_limit(key, interval, lookup=dict()):
    if key not in lookup:
        lookup[key] = 0
    while (time.monotonic() - lookup[key]) < interval:
        time.sleep(0.01)
    lookup[key] = time.monotonic()


def wait_for(f, limit=10, pause=0.1):
    start = time.time()
    while not f():
        if start + limit < time.time():
            raise Exception(f"Timeout waiting for {f.__name__}")
        time.sleep(pause)


# FUNCTIONS (SELENIUM)


def driver_launch():
    # lazy import
    if "webdriver_manager" not in globals():
        import webdriver_manager.firefox

    # silent WDM
    print("Launching driver...", end="\r")
    os.environ["WDM_LOG_LEVEL"] = "0"
    
    # options
    opts = selenium.webdriver.firefox.options.Options()
    opts.add_argument("--headless")
    
    # WDM path and launch
    gdm = webdriver_manager.firefox.GeckoDriverManager
    path = gdm(print_first_line=False).install()
    mem.driver = selenium.webdriver.Firefox(executable_path=path, options=opts)

    # clear message
    print(20 * " ", end = "\r")


def driver_close():
    if "driver" in dir(mem):
        print("Closing driver...", end="\r")
        mem.driver.close()
        print(20 * " ", end = "\r")


def _driver_id():
    return mem.driver.find_element(BY_XPATH, "html").id


def _driver_loaded():
    return mem.old_id != _driver_id()


def driver_open(url):
    # global rate limited set by module functions
    rate_limit("global", mem.limit)

    if "driver" not in dir(mem):
        driver_launch()
    mem.old_id = _driver_id()    
    mem.driver.get(url)
    wait_for(_driver_loaded)
    del mem.old_id


def driver_source():
    return mem.driver.page_source


def driver_get_content(url):
    def f():
        driver_open(url)
        return driver_source()

    if mem.is_caching:
        return mem.cache.access(url, f)
    return f()


def driver_get(url):
    return cook(driver_get_content(url))


def driver_wait_for(selector, timeout=10):
    wait = WDW(mem.driver, timeout)
    elem = (BY_SELECTOR, selector)
    wait.until(EC.visibility_of_element_located(elem))


def driver_click(selector):
    driver_wait_for(selector)
    node = mem.driver.find_element(BY_SELECTOR, selector)
    node.click()
    return node


# FUNCTIONS (CACHING)


def clear_cache():
    mem.cache = Cache()


def save_cache(fpath):
    if "cache" in dir(mem):
        mem.cache.save(fpath)


def load_cache(fpath):
    if "cache" not in dir(mem):
        clear_cache()
    mem.cache.load(fpath)


def set_cache_active():
    mem.is_caching = True
    if "cache" not in dir(mem):
        clear_cache()


def set_cache_inactive():
    mem.is_caching = False
    


# FUNCTIONS (SCREPE)


def set_rate_limit(seconds):
    mem.limit = max(0, float(seconds))


def get_content(url):
    def f():
        resp = requests.get(url, headers=HEADERS_MOZ)
        if resp.status_code != 200:
            return
        return resp.content

    if mem.is_caching:
        return mem.cache.access(url, f)
    return f()


def get(url):
    # global rate limited set by module functions
    rate_limit("global", mem.limit)

    content = get_content(url)
    if content is None:
        return
    return cook(content)


def get_many(urls):
    return thread(get, urls)


def download(url, fpath):
    # global rate limited set by module functions
    rate_limit("global", mem.limit)

    content = get_content(url)
    if content is None:
        return
    with open(fpath, "wb") as fh:
        fh.write(content)


def download_table(url, fpath, which=0, index=False):
    # global rate limited set by module functions
    rate_limit("global", mem.limit)

    # lazy import
    if "pandas" not in globals():
        import pandas

    dfs = pandas.read_html(url)
    dfs[which].to_csv(fpath, index=index)


# CLEANUP


set_rate_limit(0)
set_cache_inactive()
atexit.register(driver_close)


# SCRIPT


if __name__ == "__main__":
    # constants
    N = 10
    URL_NASDAQ = "https://www.nasdaq.com/market-activity/"
    URL_WIKIPEDIA = "https://www.wikipedia.org/"

    # request a static page
    html = get(URL_WIKIPEDIA)
    print("STATIC".ljust(N), "Wikipedia" in html.select_one_text("h1"))

    # request with headers
    url = URL_NASDAQ + "stocks/aapl/earnings"
    html = get(url)
    print("HEADER".ljust(N), html.select_one("table") is not None)

    # request many pages
    urls = N * [URL_WIKIPEDIA]
    start = time.time()
    htmls = get_many(urls)
    print("GATHER".ljust(N), N == len(htmls))
    print("".ljust(N), round(time.time() - start, 2))

    # request many pages with rate limiting
    rate = 1 / 3
    set_rate_limit(rate)
    start = time.time()
    htmls = get_many(urls)
    print("LIMIT".ljust(N), N == len(htmls))
    print("".ljust(N), round(time.time() - start, 2), "::", round(N * rate, 2))
    set_rate_limit(0)

    # download an image
    url = "https://duckduckgo.com/assets/add-to-browser/cppm/laptop.svg"
    fpath = "private/test.svg"
    download(url, fpath)
    print("IMAGE".ljust(N), os.path.exists(fpath))

    # download a file
    url = "https://www.google.com/sitemap.xml"
    fpath = "private/test.xml"
    download(url, fpath)
    print("XML".ljust(N), os.path.exists(fpath))

    # download a page
    fpath = "private/test.html"
    download(URL_WIKIPEDIA, fpath)
    print("HTML".ljust(N), os.path.exists(fpath))

    # parse table from page
    url = "https://www.multpl.com/cpi/table/by-month"
    fpath = "private/test.csv"
    download_table(url, fpath)
    print("TABLE".ljust(N), os.path.exists(fpath))

    # cache pages to memory
    set_cache_active()
    start1 = time.time()
    html1 = get(URL_WIKIPEDIA)
    start2 = time.time()
    html2 = get(URL_WIKIPEDIA)
    print("CACHE".ljust(N), html1 == html2)
    print("".ljust(N), round(start2 - start1, 2),
          "::", round(time.time() - start2, 2))

    # cache pages to file
    fpath = "private/cache.bin"
    save_cache(fpath)
    clear_cache()
    load_cache(fpath)
    start3 = time.time()
    html3 = get(URL_WIKIPEDIA)
    print("PICKLE".ljust(N), html1 == html2 == html3)
    print("".ljust(N), round(time.time() - start3, 2))

    # request a dynamic page
    url = URL_NASDAQ + "stocks/aapl/price-earnings-peg-ratios"
    html = driver_get(url)
    print("DYNAMIC".ljust(N), bool(html.select_one("table td").text.strip()))

    # log into a page
    driver_open(URL_WIKIPEDIA)
    node = driver_click("input#searchInput")
    node.send_keys("Selenium")
    driver_click("button")
    html = cook(driver_source())
    print("KEYBOARD".ljust(N), "Selenium" in html.select_one("h1").text)
