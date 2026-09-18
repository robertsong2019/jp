#!/usr/bin/env python3
"""
jp - 命令行 JSON 路径查询工具

使用方式:
    echo '{"name": "Alice"}' | jp .name
    cat data.json | jp .users[0].name
    jp .name < data.json
"""

import sys
import json
import argparse
from typing import Optional

from .query import query, query_json
from . import __version__


def format_output(value, raw: bool = False) -> str:
    """格式化输出值：默认 JSON 编码（字符串带引号）；raw=True 时字符串裸输出"""
    if raw and isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def main(args: Optional[list] = None):
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="轻量级 JSON 路径查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  echo '{"name": "Alice"}' | jp .name
  echo '{"users": [{"name": "Bob"}]}' | jp .users[0].name
  echo '{"items": [1, 2, 3]}' | jp '.items[*]'
  cat data.json | jp .store.book[0].title

支持的操作:
  .field        访问字段
  [index]       访问数组索引
  .* 或 [*]     通配符（返回所有元素）
        """
    )
    
    parser.add_argument(
        'path',
        help='JSONPath 查询路径（例如: .users[0].name）'
    )
    
    parser.add_argument(
        '-i', '--input',
        help='输入文件（默认从 stdin 读取）'
    )
    
    parser.add_argument(
        '-r', '--raw',
        action='store_true',
        help='原始输出（不添加引号到字符串）'
    )
    
    parser.add_argument(
        '-j', '--json-output',
        action='store_true',
        help='JSON 格式输出（总是输出有效的 JSON）'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'jp {__version__}'
    )
    
    parsed_args = parser.parse_args(args)
    
    # 读取输入
    if parsed_args.input:
        with open(parsed_args.input, 'r', encoding='utf-8') as f:
            json_str = f.read()
    else:
        json_str = sys.stdin.read()
    
    # 执行查询
    try:
        results = query_json(json_str, parsed_args.path)
        
        if not results:
            sys.exit(0)
        
        # 格式化输出
        if len(results) == 1:
            value = results[0]
            if parsed_args.json_output:
                print(json.dumps(value, ensure_ascii=False, indent=2))
            else:
                print(format_output(value, raw=parsed_args.raw))
        else:
            # 多个结果
            if parsed_args.json_output:
                print(json.dumps(results, ensure_ascii=False, indent=2))
            else:
                for value in results:
                    print(format_output(value, raw=parsed_args.raw))
    
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
