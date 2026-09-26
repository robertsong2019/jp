"""
词法分析器 - 将路径字符串转换为 Token 序列

词法单元类型：
- ROOT: $ 或 . 开头的根节点
- DOT: . 属性访问符
- LBRACKET: [ 数组索引开始
- RBRACKET: ] 数组索引结束
- IDENTIFIER: 标识符（属性名）
- NUMBER: 数字（数组索引）
- STRING: 引号字符串（括号内引号键，["my-key"]，JSONPath 标准语法）
- WILDCARD: * 通配符
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Iterator


class TokenType(Enum):
    ROOT = auto()
    DOT = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    WILDCARD = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str | int
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r})"


class LexerError(Exception):
    """词法分析错误"""
    pass


class Lexer:
    """词法分析器"""
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char = self.text[0] if text else None
    
    def advance(self):
        """前进一个字符"""
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
    
    def skip_whitespace(self):
        """跳过空白字符"""
        while self.current_char and self.current_char.isspace():
            self.advance()
    
    def read_identifier(self) -> str:
        """读取标识符"""
        result = []
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result.append(self.current_char)
            self.advance()
        return ''.join(result)
    
    def read_number(self) -> int:
        """读取数字"""
        result = []
        while self.current_char and self.current_char.isdigit():
            result.append(self.current_char)
            self.advance()
        return int(''.join(result))

    def read_string(self) -> str:
        """读取双引号字符串（当前字符必须是起始 "），支持 \\" 与 \\\\ 转义"""
        self.advance()  # 跳过开引号
        result = []
        while self.current_char:
            if self.current_char == '"':
                self.advance()
                return ''.join(result)
            if self.current_char == '\\':
                self.advance()
                if self.current_char in ('"', '\\'):
                    result.append(self.current_char)
                    self.advance()
                else:
                    raise LexerError(f"Invalid escape sequence: \\{self.current_char}")
                continue
            result.append(self.current_char)
            self.advance()
        raise LexerError("Unterminated string in bracket")
    
    def tokenize(self) -> List[Token]:
        """将输入字符串转换为 Token 列表"""
        tokens = []
        
        while self.current_char:
            # 跳过空白
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            # 根节点符号
            if self.current_char == '$':
                tokens.append(Token(TokenType.ROOT, '$'))
                self.advance()
                continue
            
            # 属性访问
            if self.current_char == '.':
                tokens.append(Token(TokenType.DOT, '.'))
                self.advance()
                
                # 检查是否是通配符
                if self.current_char == '*':
                    tokens.append(Token(TokenType.WILDCARD, '*'))
                    self.advance()
                elif self.current_char and (self.current_char.isalpha() or self.current_char == '_'):
                    identifier = self.read_identifier()
                    tokens.append(Token(TokenType.IDENTIFIER, identifier))
                continue
            
            # 数组索引开始
            if self.current_char == '[':
                tokens.append(Token(TokenType.LBRACKET, '['))
                self.advance()
                
                # 跳过空白
                self.skip_whitespace()
                
                # 检查内容
                if self.current_char == '*':
                    tokens.append(Token(TokenType.WILDCARD, '*'))
                    self.advance()
                elif self.current_char == '"':
                    string = self.read_string()
                    tokens.append(Token(TokenType.STRING, string))
                elif self.current_char and self.current_char.isdigit():
                    number = self.read_number()
                    tokens.append(Token(TokenType.NUMBER, number))
                elif self.current_char and (self.current_char.isalpha() or self.current_char == '_'):
                    identifier = self.read_identifier()
                    tokens.append(Token(TokenType.IDENTIFIER, identifier))
                else:
                    raise LexerError(f"Unexpected character in bracket: {self.current_char}")
                
                # 跳过空白
                self.skip_whitespace()
                
                # 期望右括号
                if self.current_char != ']':
                    raise LexerError(f"Expected ']', got {self.current_char}")
                tokens.append(Token(TokenType.RBRACKET, ']'))
                self.advance()
                continue
            
            # 如果以字母开头（没有 $ 或 .），视为根节点后的标识符
            if self.current_char.isalpha() or self.current_char == '_':
                # 隐式添加根节点
                if not tokens:
                    tokens.append(Token(TokenType.ROOT, '$'))
                identifier = self.read_identifier()
                tokens.append(Token(TokenType.IDENTIFIER, identifier))
                continue
            
            raise LexerError(f"Unexpected character: {self.current_char}")
        
        tokens.append(Token(TokenType.EOF, None))
        return tokens


def tokenize(path: str) -> List[Token]:
    """便捷函数：将路径字符串转换为 Token 列表"""
    lexer = Lexer(path)
    return lexer.tokenize()
