"""Python setup.py for pyzandro package"""
import io
import os
from setuptools import find_packages, setup

exec(open('pyzandro/version.py').read())

setup(
    name="pyzandro",
    version=__version__,
    description="Querying tool for Zandronum servers",
    url="https://github.com/AJMJ2012/pyzandro/",
    author="klaufir216, Dark-Assassin (AJMJ2012)",
    packages=find_packages(exclude=["tests"]),
    install_requires=[],
    extras_require={"test": ["pytest"]},
)
