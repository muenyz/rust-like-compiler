# ast_nodes.py

class ASTNode:
    """Base class for all AST nodes."""
    #pass

    def graphviz(self, dot=None, parent=None, edge_label=""):
        """生成Graphviz节点和边的核心方法"""
        if dot is None:
            from graphviz import Digraph
            dot = Digraph()
            dot.attr('node', shape='box', style='rounded')

        # 创建当前节点
        node_id = str(id(self))
        dot.node(node_id, self._graphviz_label())

        # 连接父节点
        if parent:
            dot.edge(parent, node_id, label=edge_label)

        # 递归处理子节点
        self._graphviz_children(dot, node_id)

        return dot

    def _graphviz_label(self):
        """默认节点标签"""
        return f"{self.__class__.__name__}"

    def _graphviz_children(self, dot, node_id):
        """默认子节点处理逻辑"""
        for field, value in vars(self).items():
            # 跳过非ASTNode字段
            if field.startswith('_') or value is None:
                continue

            # 处理单个子节点
            if isinstance(value, ASTNode):
                value.graphviz(dot, node_id, field)

            # 处理子节点列表
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    if isinstance(item, ASTNode):
                        item.graphviz(dot, node_id, f"{field}[{idx}]")

class Stmt(ASTNode):
    """Base class for all statements."""

    def _graphviz_label(self):
        return f"<<B>{self.__class__.__name__}</B>>"

    def graphviz(self, dot=None, parent=None, edge_label=""):
        node = super().graphviz(dot, parent, edge_label)
        # 统一语句节点样式
        node.node(str(id(self)),
                  shape='Mrecord',
                  color='#59a14f',
                  style='filled',
                  fillcolor='#e9f3e4')
        return node
    #pass

class Program(ASTNode):
    def _graphviz_label(self):
        return f"<<B>Program</B>>"

    def _graphviz_children(self, dot, node_id):
        # 只显示items字段的children
        for idx, item in enumerate(self.items):
            if isinstance(item, ASTNode):
                item.graphviz(dot, node_id, f"items[{idx}]")

    def __init__(self, items):
        self.items = items
    def __repr__(self):
        return f"Program({self.items})"

    def __str__(self):
        return 'Program([\n  ' + ',\n  '.join(str(item).replace('\n', '\n  ') for item in self.items) + '\n])'

class FuncDecl(ASTNode):
    def _graphviz_label(self):
        return f"<<B>FuncDecl</B><BR/><I>{self.name}</I>>"

    def _graphviz_children(self, dot, node_id):
        # 添加参数节点
        params_id = f"{node_id}_params"
        dot.node(params_id, "params", shape='note', color='#4e79a7')
        dot.edge(node_id, params_id)
        for idx, param in enumerate(self.params):
            param.graphviz(dot, params_id, f"[{idx}]")

        # 添加返回类型
        if self.ret_type:
            self.ret_type.graphviz(dot, node_id, "ret_type")

        # 添加函数体
        self.body.graphviz(dot, node_id, "body")

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
    def _graphviz_label(self):
        mut = "mut " if self.mutable else ""
        return f"<<B>Param</B><BR/>{mut}{self.name}: {self.typ}>"

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
    def _graphviz_label(self):
        mut = "mut " if self.mutable else ""
        return f"<<B>VarBinding</B><BR/>{mut}{self.name}>"

    def __init__(self, name, mutable=False):
        self.name = name
        self.mutable = mutable
    def __repr__(self):
        return f"VarBinding(name={self.name}, mutable={self.mutable})"

class VarDecl(Stmt):
    def _graphviz_label(self):
        mut_str = "mut " if self.mutable else ""
        type_str = f": {self.typ}" if self.typ else ""
        return f"<<B>VarDecl</B><BR/>{mut_str}{self.name}{type_str}>"

    def __init__(self, name, mutable, typ, init):
        self.name = name
        self.mutable = mutable
        self.typ = typ   # may be None
        self.init = init # may be None or Expr
    def __repr__(self):
        return (f"VarDecl(name={self.name}, mutable={self.mutable}, "
                f"typ={self.typ}, init={self.init})")

class ReturnStmt(Stmt):
    def _graphviz_label(self):
        return f"<<B>Return</B>>"

    def __init__(self, expr):
        self.expr = expr  # may be None or Expr
    def __repr__(self):
        return f"ReturnStmt({self.expr})"
    def __str__(self):
        return f"ReturnStmt({self.expr})"

class AssignStmt(Stmt):
    def _graphviz_label(self):
        return f"<<B>Assign</B>>"

    def __init__(self, target, expr):
        self.target = target  # an Expr (Ident, IndexExpr, MemberExpr, etc.)
        self.expr = expr      # Expr
    def __repr__(self):
        return f"AssignStmt(target={self.target}, expr={self.expr})"
    def __str__(self):
        return f"AssignStmt(\n  target={self.target},\n  expr={self.expr}\n)"

class IfStmt(Stmt):
    def _graphviz_label(self):
        return f"<<B>If</B>>"

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
    def _graphviz_label(self):
        return f"<<B>While</B>>"

    def __init__(self, cond, body):
        self.cond = cond  # Expr
        self.body = body  # Block
    def __repr__(self):
        return f"WhileStmt(cond={self.cond}, body={self.body})"

class ForStmt(Stmt):
    def _graphviz_label(self):
        mut = "mut " if self.mutable else ""
        return f"<<B>For</B><BR/>{mut}{self.name}>"

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
    def _graphviz_label(self):
        return f"<<B>Loop</B>>"

    def __init__(self, body):
        self.body = body  # Block
    def __repr__(self):
        return f"LoopStmt(body={self.body})"

class BreakStmt(Stmt):
    def _graphviz_label(self):
        return f"<<B>Break</B>>"

    def __init__(self, expr=None):        # ← 默认为 None
        self.expr = expr                  # 可能是 None，也可能是一个 Expr
    def __repr__(self):
        return f"BreakStmt({self.expr})" if self.expr is not None else "BreakStmt()"

class ContinueStmt(Stmt):
    def _graphviz_label(self):
        return f"<<B>Continue</B>>"

    def __repr__(self):
        return "ContinueStmt()"

class ExprStmt(Stmt):
    def _graphviz_label(self):
        return f"<<B>ExprStmt</B>>"

    def __init__(self, expr):
        self.expr = expr  # Expr
    def __repr__(self):
        return f"ExprStmt({self.expr})"

class EmptyStmt(Stmt):
    def _graphviz_label(self):
        return f"<<B>Empty</B>>"

    def __repr__(self):
        return "EmptyStmt()"

class Block(ASTNode):
    def _graphviz_label(self):
        return f"<<B>Block</B><BR/>{len(self.stmts)} statements>"

    def _graphviz_children(self, dot, node_id):
        # 为每个语句创建子节点
        for idx, stmt in enumerate(self.stmts):
            stmt.graphviz(dot, node_id, f"stmt[{idx}]")

    def __init__(self, stmts):
        self.stmts = stmts  # list of Stmt nodes
    def __repr__(self):
        return f"Block({self.stmts})"
    def __str__(self):
        body = ',\n    '.join(str(stmt).replace('\n', '\n    ') for stmt in self.stmts)
        return f"Block([\n    {body}\n  ])"


# Expression nodes

class Expr(ASTNode):
    #pass

    def graphviz(self, dot=None, parent=None, edge_label=""):
        node = super().graphviz(dot, parent, edge_label)
        # 统一表达式节点样式
        node.node(str(id(self)),
                  shape='oval',
                  color='#f28e2b',
                  style='filled',
                  fillcolor='#ffd8b2')
        return node

class BinaryOp(Expr):
    def _graphviz_label(self):
        return f"<<B>Operator</B><BR/>{self.op}>"

    def _graphviz_children(self, dot, node_id):
        self.left.graphviz(dot, node_id, "left")
        self.right.graphviz(dot, node_id, "right")

    def __init__(self, op, left, right):
        self.op = op          # string, e.g. '+', '=='
        self.left = left      # Expr
        self.right = right    # Expr
    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"
    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

class NumberLit(Expr):
    def _graphviz_label(self):
        return f"<<B>Number</B><BR/>{self.value}>"


    def __init__(self, value):
        self.value = value    # int
    def __repr__(self):
        return f"NumberLit({self.value})"

class Ident(Expr):
    def _graphviz_label(self):
        return f"<<B>Identifier</B><BR/>{self.name}>"

    def __init__(self, name):
        self.name = name      # string
    def __repr__(self):
        return f"Ident({self.name})"

class FuncCall(Expr):
    def _graphviz_label(self):
        return f"<<B>Call</B>>"

    def __init__(self, func, args):
        self.func = func      # Expr, typically Ident
        self.args = args      # list of Expr
    def __repr__(self):
        return f"FuncCall(func={self.func}, args={self.args})"
    def __str__(self):
        args_str = ', '.join(str(arg) for arg in self.args)
        return f"FuncCall(func={self.func}, args=[{args_str}])"

class ArrayLiteral(Expr):
    def _graphviz_label(self):
        return f"<<B>Array</B><BR/>{len(self.elements)} elements>"

    def __init__(self, elements):
        self.elements = elements  # list of Expr
    def __repr__(self):
        return f"ArrayLiteral({self.elements})"

class TupleLiteral(Expr):
    def _graphviz_label(self):
        return f"<<B>Tuple</B><BR/>{len(self.elements)} elements>"

    def __init__(self, elements):
        self.elements = elements  # list of Expr
    def __repr__(self):
        return f"TupleLiteral({self.elements})"

class DerefExpr(Expr):
    def _graphviz_label(self):
        return f"<<B>Deref</B>>"

    def __init__(self, expr):
        self.expr = expr  # Expr
    def __repr__(self):
        return f"DerefExpr({self.expr})"

class BorrowExpr(Expr):
    def _graphviz_label(self):
        kind = "mut " if self.mutable else ""
        return f"<<B>Borrow</B><BR/>{kind}>"

    def __init__(self, expr, mutable=False):
        self.expr = expr        # Expr
        self.mutable = mutable  # bool
    def __repr__(self):
        return f"BorrowExpr(expr={self.expr}, mutable={self.mutable})"

class IndexExpr(Expr):
    def _graphviz_label(self):
        return f"<<B>Index</B>>"

    def __init__(self, base, index):
        self.base = base    # Expr
        self.index = index  # Expr
    def __repr__(self):
        return f"IndexExpr(base={self.base}, index={self.index})"

class MemberExpr(Expr):
    def _graphviz_label(self):
        return f"<<B>Member</B><BR/>{self.field}>"

    def __init__(self, base, field):
        self.base = base    # Expr
        self.field = field  # int or string
    def __repr__(self):
        return f"MemberExpr(base={self.base}, field={self.field})"
