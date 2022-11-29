__author__ = "Shane Drabing"
__license__ = "MIT"
__version__ = "0.0.3"
__email__ = "shane.drabing@gmail.com"


# IMPORTS


import atexit
import concurrent.futures
import os
import pickle
import ssl
import time

import bs4
import requests
import selenium.webdriver

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW


# CONSTANTS


# refresh rate
PAUSE = 1 / 60

# webdriver methods
BY_SELECTOR = selenium.webdriver.common.by.By.CSS_SELECTOR
BY_XPATH = selenium.webdriver.common.by.By.XPATH

# user agent headers
USER_MOZ = "Mozilla/5.0 (Windows NT 5.1; rv:52.0) Gecko/20100101 Firefox/103.0"
HEADERS_MOZ = {"User-Agent": USER_MOZ}


# HELPERS


def get(url):
    resp = requests.get(url, headers=HEADERS_MOZ)
    if resp.status_code != 200:
        return
    return resp.content


def cook(html):
    if html is None:
        return
    return bs4.BeautifulSoup(html, "lxml")


def thread(f, *args):
    with concurrent.futures.ThreadPoolExecutor() as exe:
        return list(exe.map(f, *args))


def wait_for(f, limit=10):
    start = time.time()
    while not f():
        if start + limit < time.time():
            raise Exception(f"Timeout waiting for {f.__name__}")
        time.sleep(PAUSE)


def node_text(node):
    if node is None:
        return
    return " ".join(node.get_text(" ").split())


# CLASSES


class Screpe:
    def __init__(self):
        # default variables
        self.driver = None
        self.cache = dict()
        self.info = {
            "caching": False,
            "driver_id": None,
            "node": None,
            "pause": 0,
            "time": 0,
            "user-agent": USER_MOZ,
        }

    def __del__(self):
        self.driver_close()


    # METHODS (RATE-LIMITING)


    def halt(self):
        while time.time() < self.info["time"] + self.info["pause"]:
            time.sleep(PAUSE)
        self.info["time"] = time.time()

    def halt_duration(self, seconds):
        self.info["pause"] = max(0, float(seconds))


    # METHODS (CACHE)


    def cache_on(self):
        self.info["caching"] = True

    def cache_off(self):
        self.info["caching"] = False

    def cache_clear(self):
        self.cache = dict()

    def cache_save(self, fpath):
        tmp = {
            k[0]: self.cache[k]
            for k in self.cache
            if k[0] != "bs4"
        }

        with open(fpath, "wb") as fh:
            pickle.dump(tmp, fh)

    def cache_load(self, fpath, activate=True):
        if activate:
            self.cache_on()
        with open(fpath, "rb") as fh:
            self.cache = pickle.load(fh)

    def cache_access(self, key, expr):
        # check to see if we are caching
        if not self.info["caching"]:
            return expr()

        # run the expression if not in cache
        if key not in self.cache:
            value = expr()
            if value is None:
                return
            self.cache[key] = value

        return self.cache[key]


    # METHODS (REQUESTS)


    def get(self, url):
        self.halt()
        content = self.cache_access(("requests", url), lambda: get(url))
        soup = self.cache_access(("bs4", url), lambda: cook(content))
        return soup

    def get_many(self, urls):
        return thread(self.get, urls)

    def download(self, url, fpath):
        self.halt()
        content = self.cache_access(("requests", url), lambda: get(url))
        if content is None:
            return
        with open(fpath, "wb") as fh:
            fh.write(content)

    def download_table(self, url, fpath, which=0, index=False):
        # lazy import
        if "pandas" not in globals():
            ssl._create_default_https_context = ssl._create_unverified_context
            import pandas

        self.halt()
        dfs = pandas.read_html(url)
        dfs[which].to_csv(fpath, index=index)


    # METHODS (SELENIUM)


    def driver_launch(self):
        # lazy import
        if "webdriver_manager" not in globals():
            import webdriver_manager.firefox
        
        # silent logging
        os.environ["WDM_LOG_LEVEL"] = "0"

        # options
        opts = selenium.webdriver.firefox.options.Options()
        opts.add_argument("--headless")

        # install driver
        gdm = webdriver_manager.firefox.GeckoDriverManager
        path = gdm(print_first_line=False).install()
        
        # assign driver to instance
        self.driver = selenium.webdriver.Firefox(
            executable_path=path, options=opts)

    def driver_close(self):
        if self.driver is not None:
            self.driver.close()

    def driver_restart(self):
        driver_close()
        driver_launch()

    def driver_id(self):
        return self.driver.find_element(BY_XPATH, "html").id

    def driver_loaded(self):
        return self.info["driver_id"] != self.driver_id()

    def open(self, url):
        if self.driver is None:
            self.driver_launch()
        self.halt()
        self.bide(lambda: self.driver.get(url))

    def url(self):
        if self.driver is None:
            return
        return self.driver.current_url

    def source(self):
        if self.driver is None:
            return
        return cook(self.driver.page_source)

    def bide(self, expr):
        self.info["driver_id"] = self.driver_id()
        expr()
        wait_for(self.driver_loaded)

    def select(self, selector):
        self.info["node"] = self.driver.find_element(BY_SELECTOR, selector)
        return self.info["node"]

    def click(self, selector):
        self.info["node"] = self.select(selector)
        self.info["node"].click()
        return self.info["node"]

    def send_keys(self, message):
        if self.info["node"] is not None:
            self.info["node"].send_keys(message)

    def enter(self):
        self.send_keys(Keys.ENTER)

    def tab(self):
        self.send_keys(Keys.TAB)


# SCRIPT


if __name__ == "__main__":
    scr = Screpe()
    url = "https://www.wikipedia.org"
    fpath = "private/cache.bin"

    # open Wikipedia home page
    scr.open(url)

    # click on input box and input terms
    scr.click("input#searchInput")
    scr.send_keys("Selenium")

    # hit enter and halt for page load
    scr.bide(lambda: scr.enter())

    # get page source
    soup = scr.source()
    href = soup.select_one(".infobox img")["src"]

    # download an image
    scr.download("https:" + href, "private/test." + href.split(".")[-1])

    # download a table
    scr.download_table(scr.url(), "private/test.csv")

    # select a node
    node = scr.select("h1")
    print(node.text)
    print(node.get_attribute("id"))
    print(node.get_attribute("outerHTML"))