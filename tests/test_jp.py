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
        """解析字段访问"""
        nodes = parse(".name")
        assert len(nodes) == 2
        assert isinstance(nodes[1], FieldNode)
        assert nodes[1].name == "name"
    
    def test_parse_index(self):
        """解析数组索引"""
        nodes = parse("[0]")
        assert len(nodes) == 1
        assert isinstance(nodes[0], IndexNode)
        assert nodes[0].index == 0
    
    def test_parse_nested(self):
        """解析嵌套路径"""
        nodes = parse(".users[0].name")
        assert len(nodes) == 4
        assert isinstance(nodes[1], IndexNode)
        assert nodes[1].index == 0
    
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
    
    def test_query_json_string(self):
        """测试从 JSON 字符串查询"""
        json_str = '{"name": "Alice"}'
        result = query_json(json_str, ".name")
        assert result == ["Alice"]
    
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
