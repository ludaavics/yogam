from os import path
from setuptools import setup, find_packages

# Package meta-data.
NAME = "yogam"
AUTHOR = "Ludovic Tiako"
EMAIL = "ludovic.tiako@gmail.com"
DESCRIPTION = "Learn from your own mistakes"
URL = "https://github.com/ludaavics/yogam"
REQUIRES_PYTHON = ">=3.8.0"

REQUIRED = ["requests"]

EXTRAS = []

version = {}
here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.rst")) as f:
    readme = f.read()

with open(path.join(here, "LICENSE")) as f:
    license = f.read()

with open(path.join(here, NAME, "__version__.py")) as f:
    exec(f.read(), version)
version = version["__version__"]

setup(
    name=NAME,
    version=version,
    description=DESCRIPTION,
    long_description=readme,
    long_description_content_type="text/x-rst",
    url=URL,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    install_requires=REQUIRED,
    license=license,
    packages=find_packages(exclude=("tests", "docs")),
    include_package_data=True,
)