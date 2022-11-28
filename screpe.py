__author__ = "Shane Drabing"
__license__ = "MIT"
__version__ = "0.0.0"
__email__ = "shane.drabing@gmail.com"


# IMPORTS


import bs4
import requests
import selenium


# CONSTANTS


USER_MOZ = "Mozilla/5.0 (Windows NT 5.1; rv:52.0) Gecko/20100101 Firefox/103.0"
HEADERS_MOZ = {"User-Agent": USER_MOZ}


# FUNCTIONS


def get(url):
    resp = requests.get(url, headers=HEADERS_MOZ)
    if resp.status_code != 200:
        return resp
    html = resp.content
    soup = bs4.BeautifulSoup(html, "lxml")
    return soup


# CLASSES


# SCRIPT


if __name__ == "__main__":
    # constants
    URL_NASDAQ = "https://www.nasdaq.com/market-activity/"
    URL_WIKIPEDIA = "https://www.wikipedia.org"

    # request a static page
    html = get(URL_WIKIPEDIA)
    print("STAT", html.select_one("h1") is not None)

    # request with headers
    url = URL_NASDAQ + "stocks/aapl/earnings"
    html = get(url)
    print("HEAD", html.select_one("table") is not None)

    # request a dynamic page
    url = URL_NASDAQ + "stocks/aapl/price-earnings-peg-ratios"
    html = get(url)
    print("DYNA", bool(html.select_one("table td").text.strip()))

    # log into a page

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
