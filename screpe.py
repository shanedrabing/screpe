__author__ = "Shane Drabing"
__license__ = "MIT"
__version__ = "0.0.3"
__email__ = "shane.drabing@gmail.com"


# IMPORTS


import atexit
import concurrent.futures
import os
import pickle
import time

import bs4
import requests
import selenium.webdriver

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW


# CONSTANTS


# global variable on which to store elements
MEM = lambda: None

# webdriver methods
BY_SELECTOR = selenium.webdriver.common.by.By.CSS_SELECTOR
BY_XPATH = selenium.webdriver.common.by.By.XPATH
EX_TIMEOUT = selenium.common.exceptions.TimeoutException

# user agent headers
USER_MOZ = "Mozilla/5.0 (Windows NT 5.1; rv:52.0) Gecko/20100101 Firefox/103.0"
HEADERS_MOZ = {"User-Agent": USER_MOZ}


# CLASSES


# some extra methods compared to a BeautifulSoup object
class BodaciousSoup(bs4.BeautifulSoup):
    def select_one_attr(self, selector, attr):
        return safe_attr(self.select_one(selector), attr)

    def select_attr(self, selector, attr):
        return [safe_attr(node, attr) for node in self.select(selector)]

    def select_one_text(self, selector):
        return node_text(self.select_one(selector))

    def select_text(self, selector):
        return list(map(node_text, self.select(selector)))


# used for caching results from a function
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


def node_text(node):
    if node is None:
        return
    return " ".join(node.get_text(" ").split())


def cook(html):
    return BodaciousSoup(html, "lxml")


def safe_attr(obj, attr):
    try:
        return obj[attr]
    except KeyError:
        pass


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
    print("Launching webdriver...", end="\r")
    os.environ["WDM_LOG_LEVEL"] = "0"

    # options
    opts = selenium.webdriver.firefox.options.Options()
    opts.add_argument("--headless")

    # WDM path and launch
    gdm = webdriver_manager.firefox.GeckoDriverManager
    path = gdm(print_first_line=False).install()
    MEM.driver = selenium.webdriver.Firefox(executable_path=path, options=opts)

    # clear message
    print(20 * " ", end = "\r")


def driver_close():
    if "driver" in dir(MEM):
        print("Closing webdriver...", end="\r")
        MEM.driver.close()
        print(20 * " ", end = "\r")
        del MEM.driver


def _driver_id():
    return MEM.driver.find_element(BY_XPATH, "html").id


def _driver_loaded():
    return MEM.old_id != _driver_id()


def driver_open(url):
    # global rate limited set by module functions
    rate_limit("global", MEM.limit)

    if "driver" not in dir(MEM):
        driver_launch()
    MEM.old_id = _driver_id()    
    MEM.driver.get(url)
    wait_for(_driver_loaded)
    del MEM.old_id


def driver_source():
    return MEM.driver.page_source


def driver_get_content(url):
    def f():
        driver_open(url)
        return driver_source()

    if MEM.is_caching:
        return MEM.cache.access(url, f)
    return f()


def driver_get(url):
    return cook(driver_get_content(url))


def driver_wait_for(selector, timeout=10):
    try:
        wait = WDW(MEM.driver, timeout)
        elem = (BY_SELECTOR, selector)
        wait.until(EC.visibility_of_element_located(elem))
    except EX_TIMEOUT:
        return False
    return True


def driver_click(selector):
    if not driver_wait_for(selector):
        return
    node = MEM.driver.find_element(BY_SELECTOR, selector)
    node.click()
    return node


# FUNCTIONS (CACHING)


def clear_cache():
    MEM.cache = Cache()


def save_cache(fpath):
    if "cache" in dir(MEM):
        MEM.cache.save(fpath)


def load_cache(fpath):
    if "cache" not in dir(MEM):
        clear_cache()
    MEM.cache.load(fpath)


def set_cache_active():
    MEM.is_caching = True
    if "cache" not in dir(MEM):
        clear_cache()


def set_cache_inactive():
    MEM.is_caching = False
    


# FUNCTIONS (SCREPE)


def set_rate_limit(seconds):
    MEM.limit = max(0, float(seconds))


def get_content(url):
    def f():
        resp = requests.get(url, headers=HEADERS_MOZ)
        if resp.status_code != 200:
            return
        return resp.content

    if MEM.is_caching:
        return MEM.cache.access(url, f)
    return f()


def get(url):
    # global rate limited set by module functions
    rate_limit("global", MEM.limit)

    content = get_content(url)
    if content is None:
        return
    return cook(content)


def get_many(urls):
    return thread(get, urls)


def download(url, fpath):
    # global rate limited set by module functions
    rate_limit("global", MEM.limit)

    content = get_content(url)
    if content is None:
        return
    with open(fpath, "wb") as fh:
        fh.write(content)


def download_table(url, fpath, which=0, index=False):
    # global rate limited set by module functions
    rate_limit("global", MEM.limit)

    # lazy import
    if "pandas" not in globals():
        import pandas

    dfs = pandas.read_html(url)
    dfs[which].to_csv(fpath, index=index)


# SCRIPT


set_rate_limit(0)
set_cache_inactive()
atexit.register(driver_close)
