# semantic_checker.py

from ast_nodes import *

class SemanticError(Exception):
    pass

def run_semantic_checks(ast_root):
    checker = SemanticChecker()
    checker.check(ast_root)

class SemanticChecker:
    def __init__(self):
        self.env_stack = [{}]
        self.mutable = {}
        self.initialized = {}

    def current_env(self):
        return self.env_stack[-1]

    def check(self, node):
        method = 'check_' + node.__class__.__name__
        if hasattr(self, method):
            return getattr(self, method)(node)
        else:
            raise SemanticError(f"不支持的语法节点：{node.__class__.__name__}")

    def check_Program(self, node):
        for item in node.items:
            self.check(item)

    def check_FuncDecl(self, node):
        self.env_stack.append({})
        for param in node.params:
            self.current_env()[param.name] = param.typ
            self.mutable[param.name] = param.mutable
        self.check(node.body)
        self.env_stack.pop()

    def check_Block(self, block):
        for stmt in block.stmts:
            self.check(stmt)

    def check_VarDecl(self, node):
        name = node.name
        if name in self.current_env():
            raise SemanticError(f"变量 `{name}` 已被声明")

        # 默认类型推导为 None
        inferred_type = None
        if node.init:
            inferred_type = self.check_expr(node.init)

        # 如果有显式类型，使用；否则使用推导结果
        final_type = node.typ or inferred_type
        if final_type is None:
            pass #TODO:现在还没类型推导，先跳了不报错
            #raise SemanticError(f"变量 `{name}` 缺少类型注解，且无法从初始值推导类型")

        # 注册变量信息
        self.current_env()[name] = final_type
        self.mutable[name] = node.mutable
        self.initialized[name] = node.init is not None

        # 如果两者都存在，还需一致性检查
        if node.typ and inferred_type and not self.type_equals(node.typ, inferred_type):
            raise SemanticError(f"类型不匹配：声明为 `{node.typ}`，但赋值为 `{inferred_type}`")

    def check_AssignStmt(self, node):
        if isinstance(node.target, Ident):
            name = node.target.name
            typ = self.lookup(name)
            if typ is None:
                raise SemanticError(f"变量 `{name}` 未声明")
            if not self.mutable.get(name, False):
                if not self.initialized.get(name, False):
                    self.initialized[name] = True  # 首次赋值允许
                else:
                    raise SemanticError(f"变量 `{name}` 是不可变的，不能赋值")
            target_type = typ
            expr_type = self.check_expr(node.expr)
            if not self.type_equals(target_type, expr_type):
                raise SemanticError(f"赋值类型不匹配：变量 `{name}` 是 `{target_type}`，但赋值为 `{expr_type}`")

    def check_ForStmt(self, node):
        if node.end is not None:
            # 情况：for i in a .. b
            start_type = self.check_expr(node.start)
            end_type = self.check_expr(node.end)
            if start_type != 'i32' or end_type != 'i32':
                raise SemanticError("for 循环的区间边界必须是 i32 类型")
        else:
            # 情况：for i in array
            iterable_type = self.check_expr(node.start)
            if not (isinstance(iterable_type, tuple) and iterable_type[0] == 'array'):
                raise SemanticError("for 循环只能遍历数组")

        new_scope = self.current_env().copy()
        new_scope[node.name] = 'i32'
        self.env_stack.append(new_scope)
        self.mutable[node.name] = node.mutable
        self.check(node.body)
        self.env_stack.pop()

    def check_ExprStmt(self, node):
        self.check_expr(node.expr)

    def check_EmptyStmt(self, node):
        pass

    def check_IfStmt(self, node):
        pass

    def check_WhileStmt(self, node):
        pass
    def check_ReturnStmt(self, node):
        pass
    def check_LoopStmt(self, node):
        pass

    def type_equals(self, t1, t2):
        if isinstance(t1, TupleLiteral) and isinstance(t2, TupleLiteral):
            return len(t1.elements) == len(t2.elements) and all(
                self.type_equals(a, b) for a, b in zip(t1.elements, t2.elements))
        return t1 == t2

    def check_expr(self, expr):
        if isinstance(expr, NumberLit):
            return 'i32'
        if isinstance(expr, Ident):
            name = expr.name
            typ = self.lookup(name)
            if typ is None:
                if name in self.current_env():
                    raise SemanticError(f"变量 `{name}` 没有类型")
                raise SemanticError(f"使用了未声明的变量 `{name}`")
            return typ
        if isinstance(expr, BinaryOp):
            left = self.check_expr(expr.left)
            right = self.check_expr(expr.right)
            if not self.type_equals(left, right):
                raise SemanticError(f"二元运算符两侧类型不一致：{left} 和 {right}")
            return left
        if isinstance(expr, ArrayLiteral):
            for e in expr.elements:
                if self.check_expr(e) != 'i32':
                    raise SemanticError("目前仅支持元素为 i32 的数组")
            return ('array', 'i32', len(expr.elements))
        if isinstance(expr, TupleLiteral):
            elements = [self.check_expr(e) for e in expr.elements]
            return TupleLiteral(elements)
        elif isinstance(expr, BorrowExpr):
            inner_type = self.check_expr(expr.expr)
            if expr.mutable:
                return ('&mut', inner_type)
            else:
                return ('&', inner_type)
        elif isinstance(expr, DerefExpr):
            inner_type = self.check_expr(expr.expr)
            if isinstance(inner_type, tuple) and inner_type[0] in ('&', '&mut'):
                return inner_type[1]
            raise SemanticError(f"无法对非引用类型做解引用：{inner_type}")
        return 'i32'  # 默认返回

    def lookup(self, name):
        for env in reversed(self.env_stack):
            if name in env:
                return env[name]
        return None
