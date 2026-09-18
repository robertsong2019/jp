# jp - 轻量级 JSON 路径查询工具

🦐 **by Seoul Shrimp**

一个简单、模块化、有教育意义的 JSONPath 实现，用于在 JSON 数据中查询特定值。

## ✨ 特性

- 🎯 **简洁** - 核心代码 < 500 行，易于理解和学习
- 🧩 **模块化** - 清晰的词法分析、解析、查询分离
- 📚 **教育性** - 完整的编译器前端实现示例
- 🚀 **实用** - 支持常见的 JSONPath 操作

## 📦 安装

```bash
# 从源码安装
git clone https://github.com/robertsong2019/jp.git
cd jp
pip install -e .
```

## 🎮 使用

### 基本用法

```bash
# 简单字段访问
echo '{"name": "Alice", "age": 30}' | jp .name
# 输出: "Alice"

# 嵌套对象
echo '{"user": {"name": "Bob"}}' | jp .user.name
# 输出: "Bob"

# 数组索引
echo '{"items": ["apple", "banana", "cherry"]}' | jp '.items[1]'
# 输出: "banana"

# 通配符
echo '{"users": [{"name": "Alice"}, {"name": "Bob"}]}' | jp '.users[*].name'
# 输出:
# "Alice"
# "Bob"
```

### 命令行选项

```bash
# JSON 格式输出
echo '{"data": [1, 2, 3]}' | jp -j .data
# 输出: [1, 2, 3]

# 原始输出（字符串不加引号）
echo '{"msg": "hello"}' | jp -r .msg
# 输出: hello

# 从文件读取
jp .users[0].name < data.json

# 显示版本
jp --version
```

## 🏗️ 架构

```
jp/
├── lexer.py      # 词法分析器 - Token 化
├── parser.py     # 解析器 - 构建 AST
├── query.py      # 查询引擎 - 执行查询
└── cli.py        # 命令行接口
```

### 编译器前端流程

```
路径字符串 → Lexer → Token 流 → Parser → AST → Query Engine → 结果
```

**词法分析 (Lexer):**
- 将 `.users[0].name` 转换为:
  - `[DOT, IDENTIFIER("users"), LBRACKET, NUMBER(0), RBRACKET, DOT, IDENTIFIER("name")]`

**语法分析 (Parser):**
- 将 Token 流转换为 AST:
  - `[FieldNode("users"), IndexNode(0), FieldNode("name")]`

**查询执行 (Query):**
- 在 JSON 数据上遍历 AST，返回匹配值

## 📚 支持的 JSONPath 语法

| 语法 | 说明 | 示例 |
|------|------|------|
| `.` | 字段访问 | `.name` |
| `[n]` | 数组索引 | `[0]`, `[2]` |
| `.*` 或 `[*]` | 通配符 | `.users[*].name` |
| `$` | 根节点（可选） | `$.store.book` |

## 🧪 测试

```bash
# 运行测试
python -m pytest tests/
```

## 📖 教育价值

这个项目展示了：

1. **词法分析器设计** - 如何将字符串转换为 Token
2. **递归下降解析器** - 如何构建抽象语法树
3. **解释器模式** - 如何在数据结构上执行 AST
4. **模块化设计** - 关注点分离、单一职责
5. **Python 最佳实践** - 类型注解、dataclass、异常处理

## 🤝 贡献

欢迎 Issue 和 PR！

## 📄 许可证

MIT License

## 🙏 致谢

灵感来自 [jq](https://stedolan.github.io/jq/) 和 [jsonpath](https://goessner.net/articles/JsonPath/)。

---

🦐 Made with ❤️ by Seoul Shrimp
