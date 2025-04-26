# ast_nodes.py

class ASTNode:
    """Base class for all AST nodes."""
    pass

class Stmt(ASTNode):
    """Base class for all statements."""
    pass

class Program(ASTNode):
    def __init__(self, items):
        self.items = items
    def __repr__(self):
        return f"Program({self.items})"

    def __str__(self):
        return 'Program([\n  ' + ',\n  '.join(str(item).replace('\n', '\n  ') for item in self.items) + '\n])'

class FuncDecl(ASTNode):
    def __init__(self, name, params, ret_type, body):
        self.name = name
        self.params = params     # list of Param
        self.ret_type = ret_type # may be None or a type node
        self.body = body         # Block
    def __repr__(self):
        return (f"FuncDecl(name={self.name}, params={self.params}, "
                f"ret_type={self.ret_type}, body={self.body})")

    def __str__(self):
        return f'FuncDecl(\n  name={self.name},\n  params={self.params},\n  ret_type={self.ret_type},\n  body={self.body}\n)'

class Param(ASTNode):
    def __init__(self, name, mutable, typ):
        self.name = name
        self.mutable = mutable
        self.typ = typ
    def __repr__(self):
        return f"Param(name={self.name}, mutable={self.mutable}, typ={self.typ})"
    def __str__(self):
        return f"Param(name={self.name}, mutable={self.mutable}, typ={self.typ})"

class VarBinding(ASTNode):
    """represents VariableInternal in the grammar"""
    def __init__(self, name, mutable=False):
        self.name = name
        self.mutable = mutable
    def __repr__(self):
        return f"VarBinding(name={self.name}, mutable={self.mutable})"

class VarDecl(Stmt):
    def __init__(self, name, mutable, typ, init):
        self.name = name
        self.mutable = mutable
        self.typ = typ   # may be None
        self.init = init # may be None or Expr
    def __repr__(self):
        return (f"VarDecl(name={self.name}, mutable={self.mutable}, "
                f"typ={self.typ}, init={self.init})")

class ReturnStmt(Stmt):
    def __init__(self, expr):
        self.expr = expr  # may be None or Expr
    def __repr__(self):
        return f"ReturnStmt({self.expr})"
    def __str__(self):
        return f"ReturnStmt({self.expr})"

class AssignStmt(Stmt):
    def __init__(self, target, expr):
        self.target = target  # an Expr (Ident, IndexExpr, MemberExpr, etc.)
        self.expr = expr      # Expr
    def __repr__(self):
        return f"AssignStmt(target={self.target}, expr={self.expr})"
    def __str__(self):
        return f"AssignStmt(\n  target={self.target},\n  expr={self.expr}\n)"

class IfStmt(Stmt):
    def __init__(self, cond, then_body, else_body):
        self.cond = cond            # Expr
        self.then_body = then_body  # Block
        self.else_body = else_body  # Block or None
    def __repr__(self):
        return f"IfStmt(cond={self.cond}, then={self.then_body}, else={self.else_body})"
    def __str__(self):
        return (f"IfStmt(\n"
                f"  cond={self.cond},\n"
                f"  then={self.then_body},\n"
                f"  else={self.else_body}\n)")

class WhileStmt(Stmt):
    def __init__(self, cond, body):
        self.cond = cond  # Expr
        self.body = body  # Block
    def __repr__(self):
        return f"WhileStmt(cond={self.cond}, body={self.body})"

class ForStmt(Stmt):
    def __init__(self, name, mutable, start, end, body):
        self.name = name        # identifier string
        self.mutable = mutable  # bool
        self.start = start      # Expr
        self.end = end          # Expr
        self.body = body        # Block
    def __repr__(self):
        return (f"ForStmt(name={self.name}, mutable={self.mutable}, "
                f"start={self.start}, end={self.end}, body={self.body})")

class LoopStmt(Stmt):
    def __init__(self, body):
        self.body = body  # Block
    def __repr__(self):
        return f"LoopStmt(body={self.body})"

class BreakStmt(Stmt):
    def __init__(self, expr=None):        # ← 默认为 None
        self.expr = expr                  # 可能是 None，也可能是一个 Expr
    def __repr__(self):
        return f"BreakStmt({self.expr})" if self.expr is not None else "BreakStmt()"

class ContinueStmt(Stmt):
    def __repr__(self):
        return "ContinueStmt()"

class ExprStmt(Stmt):
    def __init__(self, expr):
        self.expr = expr  # Expr
    def __repr__(self):
        return f"ExprStmt({self.expr})"

class EmptyStmt(Stmt):
    def __repr__(self):
        return "EmptyStmt()"

class Block(ASTNode):
    def __init__(self, stmts):
        self.stmts = stmts  # list of Stmt nodes
    def __repr__(self):
        return f"Block({self.stmts})"
    def __str__(self):
        body = ',\n    '.join(str(stmt).replace('\n', '\n    ') for stmt in self.stmts)
        return f"Block([\n    {body}\n  ])"


# Expression nodes

class Expr(ASTNode):
    pass

class BinaryOp(Expr):
    def __init__(self, op, left, right):
        self.op = op          # string, e.g. '+', '=='
        self.left = left      # Expr
        self.right = right    # Expr
    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"
    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

class NumberLit(Expr):
    def __init__(self, value):
        self.value = value    # int
    def __repr__(self):
        return f"NumberLit({self.value})"

class Ident(Expr):
    def __init__(self, name):
        self.name = name      # string
    def __repr__(self):
        return f"Ident({self.name})"

class FuncCall(Expr):
    def __init__(self, func, args):
        self.func = func      # Expr, typically Ident
        self.args = args      # list of Expr
    def __repr__(self):
        return f"FuncCall(func={self.func}, args={self.args})"
    def __str__(self):
        args_str = ', '.join(str(arg) for arg in self.args)
        return f"FuncCall(func={self.func}, args=[{args_str}])"

class ArrayLiteral(Expr):
    def __init__(self, elements):
        self.elements = elements  # list of Expr
    def __repr__(self):
        return f"ArrayLiteral({self.elements})"

class TupleLiteral(Expr):
    def __init__(self, elements):
        self.elements = elements  # list of Expr
    def __repr__(self):
        return f"TupleLiteral({self.elements})"

class DerefExpr(Expr):
    def __init__(self, expr):
        self.expr = expr  # Expr
    def __repr__(self):
        return f"DerefExpr({self.expr})"

class BorrowExpr(Expr):
    def __init__(self, expr, mutable=False):
        self.expr = expr        # Expr
        self.mutable = mutable  # bool
    def __repr__(self):
        return f"BorrowExpr(expr={self.expr}, mutable={self.mutable})"

class IndexExpr(Expr):
    def __init__(self, base, index):
        self.base = base    # Expr
        self.index = index  # Expr
    def __repr__(self):
        return f"IndexExpr(base={self.base}, index={self.index})"

class MemberExpr(Expr):
    def __init__(self, base, field):
        self.base = base    # Expr
        self.field = field  # int or string
    def __repr__(self):
        return f"MemberExpr(base={self.base}, field={self.field})"
