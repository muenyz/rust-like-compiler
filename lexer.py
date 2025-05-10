from enum import Enum, auto

class TokenKind(Enum):
    IDENT   = auto()
    KEYWORD = auto()
    NUMBER  = auto()
    OP      = auto()
    DELIM   = auto()
    EOF     = auto()
    ERROR   = auto()

class Token:
    def __init__(self, kind: TokenKind, value: str, line: int, col: int):
        self.kind = kind
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"{self.kind.name}({self.value!r})@{self.line}:{self.col}"

class Lexer:
    KEYWORDS = {'let','mut','if','else','while','return','fn','i32','for','in','loop','break','continue'}
    OPS = {'==','!=','>=','<=','->','..','+','-','*','/','>','<','=','.', '&'}
    DELIMS = {';', ',', ':', '(', ')', '{', '}', '[', ']'}

    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1

    def peek(self):
        return self.source[self.pos] if self.pos < len(self.source) else None

    def advance(self):
        c = self.peek()
        self.pos += 1
        if c == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return c

    def match(self, s):
        return self.source.startswith(s, self.pos)

    def skip_whitespace_and_comments(self):
        while True:
            c = self.peek()
            if c is None:
                return
            if c.isspace():
                self.advance()
            elif self.match('//'):
                while self.peek() not in ('\n', None):
                    self.advance()
            else:
                return

    def lex_number(self):
        start_line, start_col = self.line, self.col
        num = ''
        if self.match('0x') or self.match('0X'):
            num += self.advance()  # 0
            num += self.advance()  # x
            while self.peek() and (self.peek().isdigit() or self.peek().lower() in 'abcdef'):
                num += self.advance()
        elif self.match('0o') or self.match('0O'):
            num += self.advance()
            num += self.advance()
            while self.peek() and self.peek() in '01234567':
                num += self.advance()
        elif self.match('0b') or self.match('0B'):
            num += self.advance()
            num += self.advance()
            while self.peek() and self.peek() in '01':
                num += self.advance()
        else:
            while self.peek() and self.peek().isdigit():
                num += self.advance()
        if self.peek() and (self.peek().isalpha() or self.peek() == '_'):
            num += self.advance()
            return Token(TokenKind.ERROR, num, start_line, start_col)
        return Token(TokenKind.NUMBER, num, start_line, start_col)

    def next_token(self):
        self.skip_whitespace_and_comments()
        c = self.peek()
        if c is None:
            return Token(TokenKind.EOF, '', self.line, self.col)

        start_line, start_col = self.line, self.col

        if c.isalpha() or c == '_':
            ident = ''
            while self.peek() is not None and (self.peek().isalnum() or self.peek() == '_'):
                ident += self.advance()
            kind = TokenKind.KEYWORD if ident in self.KEYWORDS else TokenKind.IDENT
            return Token(kind, ident, start_line, start_col)

        if c.isdigit():
            return self.lex_number()

        for op in sorted(self.OPS, key=lambda x: -len(x)):
            if self.match(op):
                for _ in op:
                    self.advance()
                return Token(TokenKind.OP, op, start_line, start_col)

        if c in self.DELIMS:
            return Token(TokenKind.DELIM, self.advance(), start_line, start_col)

        return Token(TokenKind.ERROR, self.advance(), start_line, start_col)

def tokenize_file(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    lexer = Lexer(text)
    tokens = []
    while True:
        tok = lexer.next_token()
        tokens.append(tok)
        if tok.kind == TokenKind.EOF:
            break
    return tokens