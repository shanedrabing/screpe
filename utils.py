import os
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager


def wait_for(f, limit=10, pause=0.1):
    start = time.time()
    while not f():
        if start + limit < time.time():
            raise Exception(f"Timeout waiting for {f.__name__}")
        time.sleep(pause)
    return True


class wait_for_page_load:
    def __init__(self, driver):
        self.driver = driver

    def get_page(self):
        return self.driver.find_element(By.XPATH, "html")

    def __enter__(self):
        self.old_page = self.get_page()

    def page_has_loaded(self):
        new_page = self.get_page()
        return new_page.id != self.old_page.id

    def __exit__(self, *_):
        wait_for(self.page_has_loaded)


class SeleniumScraper:
    def __init__(self, headless=True):
        os.environ["WDM_LOG_LEVEL"] = "0"
        path = GeckoDriverManager().install()
        options = Options()
        if headless:
            options.add_argument("--headless")
        self.driver = webdriver.Firefox(executable_path=path, options=options)
        self.elem = None
        self.url = None

    def open(self, url):
        self.url = url
        with wait_for_page_load(self.driver):
            self.driver.get(url)

    def close(self):
        self.driver.close()

    def source(self):
        return self.driver.page_source

    def get(self, url):
        self.open(url)
        return self.source()

    def wait_for(self, css_selector, timeout=10):
        try:
            wait = WebDriverWait(self.driver, timeout)
            elem = (By.CSS_SELECTOR, css_selector)
            wait.until(EC.visibility_of_element_located(elem))
        except TimeoutException:
            return False
        return True

    def wait_find_click(self, css_selector, timeout=10, click=True):
        self.wait_for(css_selector, timeout)
        self.elem = self.driver.find_element(By.CSS_SELECTOR, css_selector)
        if click:
            self.elem.click()
        return self.elem

    def send_keys(self, keys):
        self.elem.send_keys(str(keys))

    def sleep(self, duration=1):
        time.sleep(duration)

    def login(self, fname, css_user, css_pass, middle=lambda self: None):
        with open(fname) as f:
            gen = map(str.strip, f)
            user = next(gen)
            pasw = next(gen)

        self.wait_find_click(css_user)
        self.send_keys(user)
        middle(self)
        self.wait_find_click(css_pass)
        self.send_keys(pasw)


if __name__ == "__main__":
    sel = SeleniumScraper(headless=False)
    sel.open("https://www.wikipedia.com/")
    sel.sleep(5)
    sel.close()
