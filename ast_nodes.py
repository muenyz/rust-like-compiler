import html
from html import escape

class ASTNode:
    def graphviz(self, dot=None, parent=None, edge_label=""):
        if dot is None:
            from graphviz import Digraph
            dot = Digraph()
            dot.attr('node', shape='box', style='rounded')

        node_id = str(id(self))
        dot.node(node_id, self._graphviz_label())

        if parent:
            safe_label = edge_label.replace('[', '_').replace(']', '_')
            dot.edge(parent, node_id, label=safe_label)

        self._graphviz_children(dot, node_id)
        return dot

    def _graphviz_label(self):
        return self.__class__.__name__

    def _graphviz_children(self, dot, node_id):
        for field, value in vars(self).items():
            if field.startswith('_') or value is None:
                continue
            if isinstance(value, ASTNode):
                value.graphviz(dot, node_id, field)
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    if isinstance(item, ASTNode):
                        item.graphviz(dot, node_id, f"{field}_{idx}")

class Stmt(ASTNode):
    def _graphviz_label(self):
        return f"{self.__class__.__name__}"

    def graphviz(self, dot=None, parent=None, edge_label=""):
        node = super().graphviz(dot, parent, edge_label)
        node.node(str(id(self)),
                  shape='Mrecord',
                  color='#59a14f',
                  style='filled',
                  fillcolor='#e9f3e4')
        return node

class Program(ASTNode):
    def _graphviz_label(self):
        return "Program"

    def _graphviz_children(self, dot, node_id):
        for idx, item in enumerate(self.items):
            if isinstance(item, ASTNode):
                item.graphviz(dot, node_id, f"items_{idx}")

    def __init__(self, items):
        self.items = items

class FuncDecl(ASTNode):
    def _graphviz_label(self):
        return f"FuncDecl\\n{self.name}"

    def _graphviz_children(self, dot, node_id):
        params_id = f"{node_id}_params"
        dot.node(params_id, "params", shape='note', color='#4e79a7')
        dot.edge(node_id, params_id)
        for idx, param in enumerate(self.params):
            param.graphviz(dot, params_id, f"param_{idx}")

        if isinstance(self.ret_type, ASTNode):
            self.ret_type.graphviz(dot, node_id, "ret_type")
        elif self.ret_type is not None:
            label_id = f"{node_id}_ret_type"
            label_text = escape(f"ret_type: {self.ret_type}")
            dot.node(label_id, f"{label_text}", shape="note", color="#edc948")
            dot.edge(node_id, label_id, label="ret_type")

        self.body.graphviz(dot, node_id, "body")

    def __init__(self, name, params, ret_type, body):
        self.name = name
        self.params = params
        self.ret_type = ret_type
        self.body = body

class Param(ASTNode):
    def _graphviz_label(self):
        mut = "mut " if self.mutable else ""
        return f"Param\\n{mut}{self.name}: {self.typ}"

    def __init__(self, name, mutable, typ):
        self.name = name
        self.mutable = mutable
        self.typ = typ

class VarBinding(ASTNode):
    def _graphviz_label(self):
        mut = "mut " if self.mutable else ""
        return f"VarBinding\\n{mut}{self.name}"

    def __init__(self, name, mutable=False):
        self.name = name
        self.mutable = mutable

class VarDecl(Stmt):
    def _graphviz_label(self):
        mut = "mut " if self.mutable else ""
        typ = f": {self.typ}" if self.typ else ""
        return f"VarDecl\\n{mut}{self.name}{typ}"

    def __init__(self, name, mutable, typ, init):
        self.name = name
        self.mutable = mutable
        self.typ = typ
        self.init = init

class ReturnStmt(Stmt):
    def _graphviz_label(self):
        return "Return"

    def __init__(self, expr):
        self.expr = expr

class AssignStmt(Stmt):
    def _graphviz_label(self):
        return "Assign"

    def __init__(self, target, expr):
        self.target = target
        self.expr = expr

class IfStmt(Stmt):
    def _graphviz_label(self):
        return "If"

    def __init__(self, cond, then_body, else_body):
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body

class WhileStmt(Stmt):
    def _graphviz_label(self):
        return "While"

    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

class ForStmt(Stmt):
    def _graphviz_label(self):
        mut = "mut " if self.mutable else ""
        return f"For\\n{mut}{self.name}"

    def __init__(self, name, mutable, start, end, body):
        self.name = name
        self.mutable = mutable
        self.start = start
        self.end = end
        self.body = body

class LoopStmt(Stmt):
    def _graphviz_label(self):
        return "Loop"

    def __init__(self, body):
        self.body = body

class BreakStmt(Stmt):
    def _graphviz_label(self):
        return "Break"

    def __init__(self, expr=None):
        self.expr = expr

class ContinueStmt(Stmt):
    def _graphviz_label(self):
        return "Continue"

class ExprStmt(Stmt):
    def _graphviz_label(self):
        return "ExprStmt"

    def __init__(self, expr):
        self.expr = expr

class EmptyStmt(Stmt):
    def _graphviz_label(self):
        return "Empty"

class Block(ASTNode):
    def _graphviz_label(self):
        return f"Block\\n{len(self.stmts)} statements"

    def _graphviz_children(self, dot, node_id):
        for idx, stmt in enumerate(self.stmts):
            stmt.graphviz(dot, node_id, f"stmt_{idx}")

    def __init__(self, stmts):
        self.stmts = stmts

class Expr(ASTNode):
    def graphviz(self, dot=None, parent=None, edge_label=""):
        node = super().graphviz(dot, parent, edge_label)
        node.node(str(id(self)),
                  shape='oval',
                  color='#f28e2b',
                  style='filled',
                  fillcolor='#ffd8b2')
        return node

class BinaryOp(Expr):
    def _graphviz_label(self):
        return f"Operator\\n{escape(self.op)}"

    def _graphviz_children(self, dot, node_id):
        self.left.graphviz(dot, node_id, "left")
        self.right.graphviz(dot, node_id, "right")

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class NumberLit(Expr):
    def _graphviz_label(self):
        return f"Number\\n{self.value}"

    def __init__(self, value):
        self.value = value

class Ident(Expr):
    def _graphviz_label(self):
        return f"Identifier\\n{self.name}"

    def __init__(self, name):
        self.name = name

class FuncCall(Expr):
    def _graphviz_label(self):
        return "Call"

    def __init__(self, func, args):
        self.func = func
        self.args = args

class ArrayLiteral(Expr):
    def _graphviz_label(self):
        return f"Array\\n{len(self.elements)} elements"

    def __init__(self, elements):
        self.elements = elements

class TupleLiteral(Expr):
    def _graphviz_label(self):
        return f"Tuple\\n{len(self.elements)} elements"

    def __init__(self, elements):
        self.elements = elements

class DerefExpr(Expr):
    def _graphviz_label(self):
        return "Deref"

    def __init__(self, expr):
        self.expr = expr

class BorrowExpr(Expr):
    def _graphviz_label(self):
        kind = "mut " if self.mutable else ""
        return f"Borrow\\n{kind}"

    def __init__(self, expr, mutable=False):
        self.expr = expr
        self.mutable = mutable

class IndexExpr(Expr):
    def _graphviz_label(self):
        return "Index"

    def __init__(self, base, index):
        self.base = base
        self.index = index

class MemberExpr(Expr):
    def _graphviz_label(self):
        return f"Member\\n{escape(str(self.field))}"

    def __init__(self, base, field):
        self.base = base
        self.field = field
