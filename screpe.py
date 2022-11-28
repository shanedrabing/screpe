__author__ = "Shane Drabing"
__license__ = "MIT"
__version__ = "0.0.0"
__email__ = "shane.drabing@gmail.com"


# IMPORTS


import os
import time

import bs4
import requests
import selenium.webdriver
import webdriver_manager.firefox

# import os
# import time

# from selenium import webdriver
# from selenium.common.exceptions import NoSuchElementException
# from selenium.common.exceptions import TimeoutException
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import WebDriverWait
# from webdriver_manager.firefox import GeckoDriverManager


# CONSTANTS


USER_MOZ = "Mozilla/5.0 (Windows NT 5.1; rv:52.0) Gecko/20100101 Firefox/103.0"
HEADERS_MOZ = {"User-Agent": USER_MOZ}


# CLASSES


class mem:
    pass


# FUNCTIONS (REQUESTS)


def cook(html):
    return bs4.BeautifulSoup(html, "lxml")


def get(url):
    resp = requests.get(url, headers=HEADERS_MOZ)
    if resp.status_code != 200:
        return resp
    return cook(resp.content)


# FUNCTIONS (SELENIUM)


def wait_for(f, limit=10, pause=0.1):
    start = time.time()
    while not f():
        if start + limit < time.time():
            raise Exception(f"Timeout waiting for {f.__name__}")
        time.sleep(pause)
    return True


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


def driver_id():
    by_xpath = selenium.webdriver.common.by.By.XPATH
    return mem.driver.find_element(by_xpath, "html").id


def driver_loaded():
    return mem.old_id != driver_id()


def driver_open(url):
    if "driver" not in dir(mem):
        driver_launch()
    mem.old_id = driver_id()
    mem.driver.get(url)
    wait_for(driver_loaded)
    del mem.old_id


def driver_source():
    return mem.driver.page_source


def dip(url):
    driver_open(url)
    return cook(driver_source())


# CLASSES


# SCRIPT


if __name__ == "__main__":
    # constants
    URL_NASDAQ = "https://www.nasdaq.com/market-activity/"
    URL_WIKIPEDIA = "https://www.wikipedia.org/"

    # request a static page
    html = get(URL_WIKIPEDIA)
    print("STAT", html.select_one("h1") is not None)

    # request with headers
    url = URL_NASDAQ + "stocks/aapl/earnings"
    html = get(url)
    print("HEAD", html.select_one("table") is not None)

    # request many pages

    # request many pages with rate limiting

    # download an image

    # download a file
    
    # download a page

    # parse table from page

    # parse node from page

    # parse nodeset from page

    # cache pages to memory

    # cache pages to file

    # request a dynamic page
    url = URL_NASDAQ + "stocks/aapl/price-earnings-peg-ratios"
    html = dip(url)
    print("DYNA", bool(html.select_one("table td").text.strip()))

    # log into a page
