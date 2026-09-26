"""括号内引号键 ["key"] 支持（RED-first 2026-09-26）

JSONPath 标准语法：$["key"] 是带特殊字符 key（连字符/点号/空格/引号）的
唯一访问方式。旧实现 lexer 在 bracket 内遇到 `"` 直接
LexerError("Unexpected character in bracket")。

最小实现：TokenType.STRING + bracket 内 read_string（支持 \\" 与 \\\\ 转义，
未闭合报 LexerError），parser bracket 分支 STRING→FieldNode（query 复用
既有字段语义，零改动）。
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from jp.lexer import tokenize, TokenType, LexerError
from jp.parser import parse, FieldNode, ParseError
from jp.query import query


DATA = {
    "my-key": 1,
    "a.b": 2,
    'say "hi"': 3,
    "with space": 4,
    "数据": 5,
}


class TestQuotedBracketKey(unittest.TestCase):
    def test_simple_quoted_key(self):
        self.assertEqual(query(DATA, '["my-key"]'), [1])

    def test_dollar_prefixed_quoted_key(self):
        self.assertEqual(query(DATA, '$["a.b"]'), [2])

    def test_key_with_space(self):
        self.assertEqual(query(DATA, '["with space"]'), [4])

    def test_escaped_quote_in_key(self):
        self.assertEqual(query(DATA, '["say \\"hi\\""]'), [3])

    def test_lexer_emits_string_token(self):
        tokens = tokenize('["k"]')
        self.assertIn(TokenType.STRING, [t.type for t in tokens])

    def test_parser_maps_string_to_field_node(self):
        nodes = parse('$["my-key"]')
        self.assertIsInstance(nodes[-1], FieldNode)
        self.assertEqual(nodes[-1].name, "my-key")

    def test_unterminated_string_is_lexer_error(self):
        with self.assertRaises(LexerError):
            tokenize('["unterminated')

    def test_missing_quoted_key_raises_query_error(self):
        from jp.query import QueryError
        with self.assertRaises(QueryError):
            query(DATA, '["nope"]')

    def test_mixed_syntax_chain(self):
        data = {"items": [{"my-key": 7}]}
        self.assertEqual(query(data, '$["items"][0]["my-key"]'), [7])

    def test_unquoted_unicode_still_works(self):
        self.assertEqual(query(DATA, '.数据'), [5])


if __name__ == "__main__":
    unittest.main()
