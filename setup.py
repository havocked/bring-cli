"""Setup configuration for bring-cli."""

from setuptools import find_packages, setup

setup(
    packages=find_packages(include=["src", "src.*"]),
)
