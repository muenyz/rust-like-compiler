import sys
from enum import Enum, auto

class TokenKind(Enum):
    IDENT   = auto()   # 普通标识符
    KEYWORD = auto()   # 关键字（let, mut, if, …）
    NUMBER  = auto()   # 整数字面量
    OP      = auto()   # 运算符，如 + - * / == != >= <= = -> .. .
    DELIM   = auto()   # 界符/分隔符，如 ; , : ( ) { } [ ]
    EOF     = auto()   # 文件结束符
    ERROR   = auto()   # 未识别的字符

class Token:
    def __init__(self, kind: TokenKind, value: str, line: int, col: int):
        self.kind  = kind
        self.value = value
        self.line  = line
        self.col   = col

    def __repr__(self):
        return f"{self.kind.name}({self.value!r})@{self.line}:{self.col}"

class Lexer:
    KEYWORDS = {
        'i32','let','if','else','while','return','mut','fn',
        'for','in','loop','break','continue'
    }
    # longest operator tokens first for maximal munch
    OPS = {
        '==','!=','>=','<=','->','..',
        '+','-','*','/','>','<','=','.','&'
    }
    DELIMS = {';',',',':','(',')','{','}','[',']'}

    def __init__(self, text: str):
        self.text   = text
        self.pos    = 0
        self.line   = 1
        self.column = 1

    def peek(self, n: int = 1) -> str:
        return self.text[self.pos:self.pos + n] if self.pos + n <= len(self.text) else ''

    def advance(self, n: int = 1):
        for _ in range(n):
            if self.peek() == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1

    def skip_whitespace_and_comments(self):
        while True:
            c = self.peek()
            # 跳过空白字符
            if c.isspace():
                self.advance()
            # 单行注释 //
            elif c == '/' and self.text[self.pos:self.pos+2] == '//':
                self.advance(2)
                while self.peek() and self.peek() != '\n':
                    self.advance()
            # 多行注释 /* ... */
            elif c == '/' and self.text[self.pos:self.pos+2] == '/*':
                self.advance(2)
                while self.pos < len(self.text) and self.text[self.pos:self.pos+2] != '*/':
                    self.advance()
                # 跳过结尾 */
                if self.text[self.pos:self.pos+2] == '*/':
                    self.advance(2)
            else:
                break

    def next_token(self) -> Token:
        self.skip_whitespace_and_comments()
        start_line, start_col = self.line, self.column
        c = self.peek()

        # 文件末尾
        if not c:
            return Token(TokenKind.EOF, '', start_line, start_col)

        # 数字字面量
        if c.isdigit():
            start_line, start_col = self.line, self.column
            base = 10
            num = ''

            # 查看前缀
            if self.pos + 1 < len(self.text):
                prefix = self.text[self.pos:self.pos + 2]

                # 非法前缀（如 0z）
                if prefix.startswith('0') and prefix not in ('0b', '0o', '0x') and prefix[1].isalpha():
                    self.advance(2)
                    return Token(TokenKind.ERROR, prefix, start_line, start_col)

                # 二进制
                if prefix == '0b':
                    base = 2
                    self.advance(2)
                    while self.peek() in '01':
                        num += self.peek()
                        self.advance()
                    if not num:
                        return Token(TokenKind.ERROR, '0b', start_line, start_col)
                    return Token(TokenKind.NUMBER, f'0b{num}', start_line, start_col)

                # 八进制
                if prefix == '0o':
                    base = 8
                    self.advance(2)
                    while self.peek() in '01234567':
                        num += self.peek()
                        self.advance()
                    if not num:
                        return Token(TokenKind.ERROR, '0o', start_line, start_col)
                    return Token(TokenKind.NUMBER, f'0o{num}', start_line, start_col)

                # 十六进制
                if prefix == '0x':
                    base = 16
                    self.advance(2)
                    while self.peek().lower() in '0123456789abcdef':
                        num += self.peek()
                        self.advance()
                    if not num:
                        return Token(TokenKind.ERROR, '0x', start_line, start_col)
                    return Token(TokenKind.NUMBER, f'0x{num}', start_line, start_col)

            # 普通十进制
            while self.peek().isdigit():
                num += self.peek()
                self.advance()
            return Token(TokenKind.NUMBER, num, start_line, start_col)

        # 标识符或关键字
        if c.isalpha() or c == '_':
            ident = ''
            while self.peek().isalnum() or self.peek() == '_':
                ident += self.peek()
                self.advance()
            kind = TokenKind.KEYWORD if ident in self.KEYWORDS else TokenKind.IDENT
            return Token(kind, ident, start_line, start_col)

        # 运算符：两字符优先
        two = self.text[self.pos:self.pos+2]
        if two in self.OPS:
            self.advance(2)
            return Token(TokenKind.OP, two, start_line, start_col)

        # 单字符运算符
        if c in self.OPS:
            self.advance()
            return Token(TokenKind.OP, c, start_line, start_col)

        # 界符/分隔符
        if c in self.DELIMS:
            self.advance()
            return Token(TokenKind.DELIM, c, start_line, start_col)

        # 未知字符，标记为 ERROR
        self.advance()
        return Token(TokenKind.ERROR, c, start_line, start_col)

def tokenize_file(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    lexer = Lexer(text)
    tokens = []
    while True:
        tok = lexer.next_token()
        tokens.append(tok)
        if tok.kind == TokenKind.EOF:
            break
    return tokens

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("用法: python lexer.py <源文件.rs>")
        sys.exit(1)
    for token in tokenize_file(sys.argv[1]):
        print(token)