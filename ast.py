# ast.py

class ASTNode:
    """Base class for all AST nodes."""
    pass

class Program(ASTNode):
    def __init__(self, items):
        self.items = items
    def __repr__(self):
        return f"Program({self.items})"

class FuncDecl(ASTNode):
    def __init__(self, name, params, ret_type, body):
        self.name = name
        self.params = params
        self.ret_type = ret_type
        self.body = body
    def __repr__(self):
        return f"FuncDecl(name={self.name}, params={self.params}, ret_type={self.ret_type}, body={self.body})"

class Param(ASTNode):
    def __init__(self, name, mutable, typ):
        self.name = name
        self.mutable = mutable
        self.typ = typ
    def __repr__(self):
        return f"Param(name={self.name}, mutable={self.mutable}, typ={self.typ})"

class VarDecl(ASTNode):
    def __init__(self, name, mutable, typ, init):
        self.name = name
        self.mutable = mutable
        self.typ = typ
        self.init = init
    def __repr__(self):
        return f"VarDecl(name={self.name}, mutable={self.mutable}, typ={self.typ}, init={self.init})"

class IfStmt(ASTNode):
    def __init__(self, cond, then_body, else_body):
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body
    def __repr__(self):
        return f"IfStmt(cond={self.cond}, then={self.then_body}, else={self.else_body})"

class ExprStmt(ASTNode):
    def __init__(self, expr):
        self.expr = expr
    def __repr__(self):
        return f"ExprStmt({self.expr})"

class ReturnStmt(ASTNode):
    def __init__(self, expr):
        self.expr = expr
    def __repr__(self):
        return f"ReturnStmt({self.expr})"

class WhileStmt(ASTNode):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body
    def __repr__(self):
        return f"WhileStmt(cond={self.cond}, body={self.body})"

class ForStmt(ASTNode):
    def __init__(self, var, iterable, body):
        self.var = var
        self.iterable = iterable
        self.body = body
    def __repr__(self):
        return f"ForStmt(var={self.var}, iterable={self.iterable}, body={self.body})"

class LoopStmt(ASTNode):
    def __init__(self, body):
        self.body = body
    def __repr__(self):
        return f"LoopStmt(body={self.body})"

class BreakStmt(ASTNode):
    def __repr__(self):
        return "BreakStmt()"

class ContinueStmt(ASTNode):
    def __repr__(self):
        return "ContinueStmt()"

class Block(ASTNode):
    def __init__(self, stmts):
        self.stmts = stmts
    def __repr__(self):
        return f"Block({self.stmts})"

# Expression nodes

class Expr(ASTNode):
    pass

class BinaryOp(Expr):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"

class NumberLit(Expr):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"NumberLit({self.value})"

class Ident(Expr):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"Ident({self.name})"

class CallExpr(Expr):
    def __init__(self, func, args):
        self.func = func
        self.args = args
    def __repr__(self):
        return f"CallExpr(func={self.func}, args={self.args})"
