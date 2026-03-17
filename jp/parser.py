"""
解析器 - 将 Token 序列转换为抽象语法树 (AST)

AST 节点类型：
- RootNode: 根节点
- FieldNode: 字段访问
- IndexNode: 数组索引访问
- WildcardNode: 通配符
"""

from dataclasses import dataclass
from typing import List, Union
from .lexer import tokenize, Token, TokenType, LexerError


class ParseError(Exception):
    """解析错误"""
    pass


# AST 节点定义
@dataclass
class RootNode:
    """根节点"""
    pass


@dataclass
class FieldNode:
    """字段访问节点"""
    name: str


@dataclass
class IndexNode:
    """数组索引节点"""
    index: int


@dataclass
class WildcardNode:
    """通配符节点"""
    pass


# AST 类型
ASTNode = Union[RootNode, FieldNode, IndexNode, WildcardNode]


class Parser:
    """递归下降解析器"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0] if tokens else None
    
    def advance(self):
        """前进一个 Token"""
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def expect(self, token_type: TokenType) -> Token:
        """期望特定类型的 Token"""
        if self.current_token.type != token_type:
            raise ParseError(f"Expected {token_type}, got {self.current_token.type}")
        token = self.current_token
        self.advance()
        return token
    
    def parse(self) -> List[ASTNode]:
        """解析 Token 序列，返回 AST 节点列表"""
        nodes = []
        
        # 根节点
        if self.current_token.type == TokenType.ROOT:
            nodes.append(RootNode())
            self.advance()
        
        # 解析后续节点
        while self.current_token.type != TokenType.EOF:
            if self.current_token.type == TokenType.DOT:
                self.advance()
                
                if self.current_token.type == TokenType.IDENTIFIER:
                    nodes.append(FieldNode(self.current_token.value))
                    self.advance()
                elif self.current_token.type == TokenType.WILDCARD:
                    nodes.append(WildcardNode())
                    self.advance()
                else:
                    raise ParseError(f"Expected IDENTIFIER or WILDCARD after DOT, got {self.current_token.type}")
            
            elif self.current_token.type == TokenType.LBRACKET:
                self.advance()
                
                if self.current_token.type == TokenType.NUMBER:
                    nodes.append(IndexNode(self.current_token.value))
                    self.advance()
                elif self.current_token.type == TokenType.WILDCARD:
                    nodes.append(WildcardNode())
                    self.advance()
                elif self.current_token.type == TokenType.IDENTIFIER:
                    # 支持字符串索引（用于字典）
                    nodes.append(FieldNode(self.current_token.value))
                    self.advance()
                else:
                    raise ParseError(f"Expected NUMBER, WILDCARD, or IDENTIFIER in brackets, got {self.current_token.type}")
                
                self.expect(TokenType.RBRACKET)
            
            elif self.current_token.type == TokenType.IDENTIFIER:
                # 直接的标识符（没有前导点）
                nodes.append(FieldNode(self.current_token.value))
                self.advance()
            
            else:
                raise ParseError(f"Unexpected token: {self.current_token}")
        
        return nodes


def parse(path: str) -> List[ASTNode]:
    """便捷函数：将路径字符串解析为 AST"""
    tokens = tokenize(path)
    parser = Parser(tokens)
    return parser.parse()
