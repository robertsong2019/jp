"""
jp - 轻量级 JSON 路径查询工具

一个简单的 JSONPath 实现，支持基本的路径查询操作。
"""

__version__ = "0.1.0"
__author__ = "Seoul Shrimp"

from .query import query
from .parser import parse

__all__ = ["query", "parse"]
