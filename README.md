<div align="center">

# Screpe

High-level Python web scraping.

<img src="docs/crepe.jpg" width="60%" />

(Crepes not included)

<br>

---

## Installation

</div>
<br>

### Using `pip`

The Python package installer makes it easy to install `screpe`.

```console
pip install screpe
```

<br>

### Using `git`

Otherwise, clone this repository to your local machine with git, then install
with Python.

```console
git clone https://github.com/shanedrabing/screpe.git
cd screpe
python setup.py install
```

You can also simply download `screpe.py` and place it in your working
directory.

<br>

---

<div align="center">

## Getting Started

</div>
<br>

### Initializing Screpe

Import the module in Python, and initialize a `Screpe` object.

```python
from screpe import Screpe

# do we want the scraper to remember previous responses?
scr = Screpe(is_caching=True)
```

All methods in this module live on the `Screpe` class, so there is no need to
import anything else!

<br>

### Requests and BeautifulSoup

If you are familiar with web scraping in Python, then you've probably used the
`requests` and `bs4` packages before. There are a couple of static methods that
Screpe provides to make their usage even easier!

```python
# a webpage we want to scrape
url = "https://www.wikipedia.org"

# returns None if status code is not 200
html = Screpe.get(url)

# can handle None as input, parses the HTML with `lxml`
soup = Screpe.cook(html)

# check to make sure we have a soup object, otherwise see bs4
if soup is not None:
    print(soup.select_one("h1"))
```

We can marry these two functions with the instance method `Screpe.dine`.
Remember that we have the `scr` object from the section above.

```python
# get and cook
soup = scr.dine(url)
```

Responses from `Screpe.dine` can be cached and adhere to rate-limiting (see
next sections).

<br>

### Downloading a Webpage or a File

Commonly, we just want to download an image, webpage, generic file, etc. Let's
see how to do this with Screpe!

```python
# locator to file we want, local path to where we want it
url = "https://www.python.org/static/img/python-logo.png"
fpath = "logo.png"

# let us use our object to download the file
scr.download(url, fpath)
```

Note that the URL can be pretty much any filetype as the response is saved in
binary, just make sure you get the filetype right.

<br>

### Downloading an HTML Table

Sometimes there is a nice HTML table on a webpage that we want as more
interoperable format. The `pandas` package can do this easily, and we take
advantage of that with Screpe.

```python
# this webpage contains a table that we want to download
url = "https://www.multpl.com/cpi/table/by-year"

# we save the tables as a CSV file
fpath = "table.csv"

# the `which` parameter decides what table to save
scr.download_table(url, fpath, which=0)
```

<br>

### Selenium

One of the most challenging tasks in web scraping is to deal with dynamic pages
that require a web browser to work properly. Thankfully, the `selenium` package
is pretty good at this. Screpe removes headaches surrounding Selenium.

```python
# the homepage of Wikipedia has a search box
url = "https://www.wikipedia.org"

# let us open the page in a webdriver
scr.open(url)

# we can click on the input box
scr.click("input#searchInput")

# ...enter a search term
scr.send_keys("Selenium")

# ...and hit return to initiate the search
scr.bide(lambda: scr.send_enter())
# note that the `Screpe.bide` function takes a function as input, checks what
# page it is on, calls the function, and waits for the next page to load

# we can use bs4 once the next page loads!
soup = scr.source()
```

<br>

### Asynchronous Requests

Screpe uses `concurrent.futures` to spawn a bunch of threads that can work
simulatanously to retrieve webpages.

```python
# a collection of URLs
urls = ["https://www.wikipedia.org/wiki/Dog",
        "https://www.wikipedia.org/wiki/Cat",
        "https://www.wikipedia.org/wiki/Sheep"]

# we want soup objects for all
soups = scr.dine_many(urls)
```

<br>

### Rate-Limiting

If sites are sensitive to how often you can request, consider setting your
`Screpe` object to halt before sending another request.

```python
# we give the function a duration, but can find that from a rate
rate_per_second = 2
duration_in_seconds = 1 / rate_per_second

# inform your scraper to not surpass the request interval
scr.halt_duration(duration_in_seconds)
```

Note that cached responses do not adhere to the rate limit. After all, we
already have the reponse!

<br>

### Caching

Sometimes, we have to request many pages. So that we don't waste bandwidth, or
a rate limit, we can use cached reponses. Note that caching is on by default,
turn it off if you want real-time responses.

```python
# turn caching on
scr.cache_on()

# ...or turn it off
scr.cache_off()
```

We can save and load the cache between sessions for even more greatness!

```python
# where shall we save the cache? (binary file)
fpath = "cahce.bin"

# save the cache
scr.cache_save(fpath)

# load the cache
scr.cache_load(fpath)

# clear the cache
scr.cache_clear()
```

<br>
<br>
<div align="center">

---

## License

</div>
<br>

[MIT License](https://choosealicense.com/licenses/mit/)

Copyright (c) 2022 <a href="https://:-)">Shane Drabing</a>
