#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jp-query",
    version="0.1.0",
    author="Seoul Shrimp",
    author_email="seoul.shrimp@example.com",
    description="轻量级 JSON 路径查询工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/robertsong2019/jp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "jp=jp.cli:main",
        ],
    },
)
