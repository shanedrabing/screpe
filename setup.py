import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="screpe",
    version="0.0.8",
    author="Shane Drabing",
    author_email="shane.drabing@gmail.com",
    packages=setuptools.find_packages(),
    url="https://github.com/shanedrabing/screpe",
    description="High-level Python web scraping.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    data_files=[
        ("", ["LICENSE"])
    ],
    install_requires=[
        "bs4",
        "lxml",
        "pandas",
        "requests",
        "selenium",
        "webdriver_manager",
    ],
    py_modules=[
        "screpe"
    ]
)
