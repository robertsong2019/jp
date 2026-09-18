"""
jp 测试套件

测试词法分析、解析、查询功能
"""

import json
import pytest
from jp.lexer import tokenize, TokenType, LexerError
from jp.parser import parse, FieldNode, IndexNode, WildcardNode, RootNode, ParseError
from jp.query import query, query_json, QueryError


class TestLexer:
    """测试词法分析器"""
    
    def test_simple_field(self):
        """测试简单字段访问"""
        tokens = tokenize(".name")
        assert len(tokens) == 3  # DOT, IDENTIFIER, EOF
        assert tokens[0].type == TokenType.DOT
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "name"

    def test_unterminated_bracket_raises(self):
        """未闭合的 [ → LexerError"""
        with pytest.raises(LexerError):
            tokenize("[0")

    def test_bracket_garbage_raises(self):
        """[内非法字符 → LexerError"""
        with pytest.raises(LexerError):
            tokenize("[!?]")

    def test_leading_digit_path_raises(self):
        """数字开头的路径 → LexerError"""
        with pytest.raises(LexerError):
            tokenize("1abc")

    def test_whitespace_inside_brackets(self):
        """[ 0 ] 空白被跳过"""
        tokens = tokenize("[ 0 ]")
        assert tokens[1].type == TokenType.NUMBER
        assert tokens[1].value == 0
    
    def test_array_index(self):
        """测试数组索引"""
        tokens = tokenize("[0]")
        assert tokens[0].type == TokenType.LBRACKET
        assert tokens[1].type == TokenType.NUMBER
        assert tokens[1].value == 0
        assert tokens[2].type == TokenType.RBRACKET
    
    def test_nested_path(self):
        """测试嵌套路径"""
        tokens = tokenize(".users[0].name")
        assert tokens[0].type == TokenType.DOT
        assert tokens[1].value == "users"
        assert tokens[3].value == 0  # NUMBER
        assert tokens[6].value == "name"
    
    def test_wildcard(self):
        """测试通配符"""
        tokens = tokenize(".users[*]")
        assert tokens[3].type == TokenType.WILDCARD
    
    def test_root_symbol(self):
        """测试根节点符号"""
        tokens = tokenize("$.store")
        assert tokens[0].type == TokenType.ROOT
        assert tokens[2].value == "store"


class TestParser:
    """测试解析器"""
    
    def test_parse_field(self):
        """解析字段访问（README 契约: dot-path 无隐式 RootNode）"""
        nodes = parse(".name")
        assert len(nodes) == 1
        assert isinstance(nodes[0], FieldNode)
        assert nodes[0].name == "name"

    def test_parse_index(self):
        """解析数组索引"""
        nodes = parse("[0]")
        assert len(nodes) == 1
        assert isinstance(nodes[0], IndexNode)
        assert nodes[0].index == 0

    def test_parse_nested(self):
        """解析嵌套路径（README 契约: [FieldNode, IndexNode, FieldNode]）"""
        nodes = parse(".users[0].name")
        assert len(nodes) == 3
        assert isinstance(nodes[1], IndexNode)
        assert nodes[1].index == 0
        assert isinstance(nodes[2], FieldNode)
        assert nodes[2].name == "name"

    def test_parse_explicit_root(self):
        """显式 $ 产生 RootNode（查询引擎负责剥离）"""
        nodes = parse("$.store")
        assert len(nodes) == 2
        assert isinstance(nodes[0], RootNode)
        assert isinstance(nodes[1], FieldNode)

    def test_parse_root_only(self):
        """裸 $ 只有一个 RootNode"""
        nodes = parse("$")
        assert nodes == [RootNode()]

    def test_parse_bare_identifier_gets_implicit_root(self):
        """裸标识符路径由 lexer 隐式补 ROOT（lexer.py 已实现的行为）"""
        nodes = parse("name")
        assert len(nodes) == 2
        assert isinstance(nodes[0], RootNode)
        assert isinstance(nodes[1], FieldNode)
        assert nodes[1].name == "name"

    def test_parse_bracket_string_index(self):
        """[ident] 形式的字典字符串索引 → FieldNode（parser 分支已实现，从未有测试）"""
        nodes = parse(".a[b]")
        assert len(nodes) == 2
        assert isinstance(nodes[1], FieldNode)
        assert nodes[1].name == "b"

    def test_parse_trailing_dot_raises(self):
        """尾随点 → ParseError 而非崩溃"""
        with pytest.raises(ParseError):
            parse(".a.")

    def test_parse_lone_dot_raises(self):
        """单独一个点 → ParseError"""
        with pytest.raises(ParseError):
            parse(".")

    def test_parse_wildcard(self):
        """解析通配符"""
        nodes = parse(".users[*]")
        assert isinstance(nodes[1], WildcardNode)


class TestQuery:
    """测试查询引擎"""
    
    def test_simple_field(self):
        """查询简单字段"""
        data = {"name": "Alice", "age": 30}
        result = query(data, ".name")
        assert result == ["Alice"]
    
    def test_nested_field(self):
        """查询嵌套字段"""
        data = {"user": {"name": "Bob", "age": 25}}
        result = query(data, ".user.name")
        assert result == ["Bob"]
    
    def test_array_index(self):
        """查询数组索引"""
        data = {"items": ["apple", "banana", "cherry"]}
        result = query(data, ".items[1]")
        assert result == ["banana"]
    
    def test_array_of_objects(self):
        """查询对象数组"""
        data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ]
        }
        result = query(data, ".users[0].name")
        assert result == ["Alice"]
    
    def test_wildcard(self):
        """测试通配符"""
        data = {
            "users": [
                {"name": "Alice"},
                {"name": "Bob"}
            ]
        }
        result = query(data, ".users[*].name")
        assert result == ["Alice", "Bob"]
    
    def test_wildcard_tolerates_missing_field_in_fanout(self):
        """通配符扇出中单个元素缺字段 → 跳过该元素（docstring: 用于通配符场景）"""
        data = {"users": [{"name": "Alice"}, {"x": 1}]}
        result = query(data, ".users[*].name")
        assert result == ["Alice"]

    def test_type_error_raises_on_plain_path(self):
        """非扇出路径上类型不匹配 → QueryError 上抛而非吞掉"""
        with pytest.raises(QueryError):
            query("just a string", ".name")

    def test_error_after_wildcard_step_tolerated(self):
        """通配符之后那一步的缺字段在扇出语境下被容忍"""
        data = {"items": [1, 2]}
        # 上一节点是通配符 → 数字上访问 .name 缺失被跳过 → 结果空
        result = query(data, ".items[*].name")
        assert result == []

    def test_query_root_returns_whole_data(self):
        """$ 返回整个数据"""
        data = {"a": 1}
        assert query(data, "$") == [data]

    def test_query_empty_path_returns_whole_data(self):
        """空路径返回整个数据"""
        assert query({"a": 1}, "") == [{"a": 1}]

    def test_bracket_string_index_query(self):
        """[ident] 字符串索引用于字典"""
        data = {"a": {"b": 42}}
        assert query(data, ".a[b]") == [42]

    def test_query_json_invalid_json_raises(self):
        """query_json 非法 JSON → JSONDecodeError 上抛"""
        with pytest.raises(json.JSONDecodeError):
            query_json("not json", ".a")
    
    def test_field_not_found(self):
        """测试字段不存在"""
        data = {"name": "Alice"}
        with pytest.raises(QueryError):
            query(data, ".age")
    
    def test_index_out_of_range(self):
        """测试索引越界"""
        data = {"items": ["a", "b"]}
        with pytest.raises(QueryError):
            query(data, ".items[5]")


class TestIntegration:
    """集成测试"""
    
    def test_complex_json(self):
        """测试复杂 JSON 结构"""
        data = {
            "store": {
                "book": [
                    {
                        "category": "reference",
                        "author": "Nigel Rees",
                        "title": "Sayings of the Century",
                        "price": 8.95
                    },
                    {
                        "category": "fiction",
                        "author": "Evelyn Waugh",
                        "title": "Sword of Honour",
                        "price": 12.99
                    }
                ],
                "bicycle": {
                    "color": "red",
                    "price": 19.95
                }
            }
        }
        
        # 查询第一本书的标题
        result = query(data, ".store.book[0].title")
        assert result == ["Sayings of the Century"]
        
        # 查询所有书的作者
        result = query(data, ".store.book[*].author")
        assert result == ["Nigel Rees", "Evelyn Waugh"]
        
        # 查询自行车颜色
        result = query(data, ".store.bicycle.color")
        assert result == ["red"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
