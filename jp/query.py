"""
查询引擎 - 在 JSON 数据上执行 AST 查询

支持的操作：
- 字段访问: .field
- 数组索引: [0]
- 通配符: .* 或 [*]
- 链式查询: .users[0].name
"""

import json
from typing import Any, List, Union
from .parser import parse, ASTNode, RootNode, FieldNode, IndexNode, WildcardNode


class QueryError(Exception):
    """查询错误"""
    pass


def _query_single(data: Any, node: ASTNode) -> List[Any]:
    """
    在数据上执行单个 AST 节点的查询
    
    返回列表以支持通配符（可能匹配多个值）
    """
    if isinstance(node, RootNode):
        return [data]
    
    elif isinstance(node, FieldNode):
        if isinstance(data, dict):
            if node.name in data:
                return [data[node.name]]
            else:
                raise QueryError(f"Field '{node.name}' not found")
        else:
            raise QueryError(f"Cannot access field '{node.name}' on {type(data).__name__}")
    
    elif isinstance(node, IndexNode):
        if isinstance(data, list):
            if 0 <= node.index < len(data):
                return [data[node.index]]
            else:
                raise QueryError(f"Index {node.index} out of range (length {len(data)})")
        else:
            raise QueryError(f"Cannot index {type(data).__name__} with integer")
    
    elif isinstance(node, WildcardNode):
        results = []
        if isinstance(data, list):
            results.extend(data)
        elif isinstance(data, dict):
            results.extend(data.values())
        else:
            raise QueryError(f"Cannot use wildcard on {type(data).__name__}")
        return results
    
    else:
        raise QueryError(f"Unknown node type: {type(node)}")


def query(data: Any, path: str) -> List[Any]:
    """
    在 JSON 数据上执行路径查询
    
    Args:
        data: JSON 数据（已解析的 Python 对象）
        path: JSONPath 路径字符串
        
    Returns:
        匹配的值列表
        
    Examples:
        >>> data = {"users": [{"name": "Alice", "age": 30}]}
        >>> query(data, ".users[0].name")
        ['Alice']
        
        >>> query(data, ".users[*].name")
        ['Alice']
    """
    nodes = parse(path)
    
    if not nodes:
        return [data]
    
    # 从根节点开始
    if isinstance(nodes[0], RootNode):
        nodes = nodes[1:]
    
    # 执行查询链
    results = [data]
    
    for node in nodes:
        new_results = []
        for result in results:
            try:
                new_results.extend(_query_single(result, node))
            except QueryError:
                # 跳过不匹配的结果（用于通配符场景）
                pass
        results = new_results
        
        if not results:
            break
    
    return results


def query_json(json_str: str, path: str) -> List[Any]:
    """
    便捷函数：从 JSON 字符串执行查询
    
    Args:
        json_str: JSON 字符串
        path: JSONPath 路径字符串
        
    Returns:
        匹配的值列表
    """
    data = json.loads(json_str)
    return query(data, path)
