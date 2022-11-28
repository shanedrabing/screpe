__author__ = "Shane Drabing"
__license__ = "MIT"
__version__ = "0.0.1"
__email__ = "shane.drabing@gmail.com"


# IMPORTS


import atexit
import concurrent.futures
import os
import time

import bs4
import requests
import selenium.webdriver
import webdriver_manager.firefox

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC


# CONSTANTS


USER_MOZ = "Mozilla/5.0 (Windows NT 5.1; rv:52.0) Gecko/20100101 Firefox/103.0"
HEADERS_MOZ = {"User-Agent": USER_MOZ}

BY_XPATH = selenium.webdriver.common.by.By.XPATH
BY_SELECTOR = selenium.webdriver.common.by.By.CSS_SELECTOR
WDW = selenium.webdriver.support.ui.WebDriverWait


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


def wait_for(f, limit=10, pause=0.1):
    start = time.time()
    while not f():
        if start + limit < time.time():
            raise Exception(f"Timeout waiting for {f.__name__}")
        time.sleep(pause)


# FUNCTIONS (SELENIUM)


def driver_launch():
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
    if "driver" not in dir(mem):
        driver_launch()
    mem.old_id = _driver_id()
    mem.driver.get(url)
    wait_for(_driver_loaded)
    del mem.old_id


def driver_source():
    return mem.driver.page_source


def driver_soup():
    return cook(driver_source())


def driver_wait_for(selector, timeout=10):
    wait = WDW(mem.driver, timeout)
    elem = (BY_SELECTOR, selector)
    wait.until(EC.visibility_of_element_located(elem))


def driver_click(selector):
    driver_wait_for(selector)
    node = mem.driver.find_element(BY_SELECTOR, selector)
    node.click()
    return node


# FUNCTIONS (SCREPE)


def get(url):
    resp = requests.get(url, headers=HEADERS_MOZ)
    if resp.status_code != 200:
        return resp
    return cook(resp.content)


def gets(urls):
    return thread(get, urls)


def dip(url):
    driver_open(url)
    return driver_soup()


def download(url, fpath):
    resp = requests.get(url, headers=HEADERS_MOZ)
    if resp.status_code != 200:
        raise Exception(f"Failed to download {url}")
    with open(fpath, "wb") as fh:
        fh.write(resp.content)


# CLEANUP


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
    htmls = gets(urls)
    print("GATHER".ljust(N), N == len(htmls))

    # request many pages with rate limiting

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

    # parse nodeset from page

    # cache pages to memory

    # cache pages to file

    exit()

    # request a dynamic page
    url = URL_NASDAQ + "stocks/aapl/price-earnings-peg-ratios"
    html = dip(url)
    print("DYNAMIC".ljust(N), bool(html.select_one("table td").text.strip()))

    # log into a page
    driver_open(URL_WIKIPEDIA)
    node = driver_click("input#searchInput")
    node.send_keys("Selenium")
    driver_click("button")
    html = driver_soup()
    print("KEYBOARD".ljust(N), "Selenium" in html.select_one("h1").text)
