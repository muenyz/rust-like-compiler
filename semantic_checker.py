from ast_nodes import *
import sys
import  traceback

class SemanticError(Exception):
    def __init__(self, message,line=None, col=None):
        if line and col:
            super().__init__(f"错误 (第 {line} 行, 第 {col} 列): {message}")
        else:
            super().__init__(message)

class Type:
    """所有类型的基类"""
    def __eq__(self, other):
        return isinstance(other,Type) and self.__class__ == other.__class__
    def __repr__(self):
        return self.__class__.__name__


class PrimitiveType(Type):
    """基本类型的基类"""
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return super().__eq__(other) and self.name == other.name
    def __repr__(self):
        return self.name


class RefType(Type):
    """引用类型"""
    def __init__(self,target_type: Type, is_mutable:bool):
        self.target_type = target_type
        self.is_mutable = is_mutable
    def __eq__(self, other):
        return (super().__eq__(other) and
                self.target_type == other.target_type and
                self.is_mutable == other.is_mutable)

    def __repr__(self):
        return f"&{'mut ' if self.is_mutable else ''}{self.target_type}"

class ArrayType(Type):
    """数组类型, e.g., [i32; 3]"""

    def __init__(self, element_type: Type, size: int):
        self.element_type = element_type
        self.size = size

    def __eq__(self, other):
        return super().__eq__(other) and self.element_type == other.element_type and self.size == other.size

    def __repr__(self):
        return f"[{self.element_type}; {self.size}]"

class TupleType(Type):
    """元组类型, e.g., (i32, &i32)"""

    def __init__(self, member_types: list[Type]):
        self.member_types = member_types

    def __eq__(self, other):
        return super().__eq__(other) and self.member_types == other.member_types

    def __repr__(self):
        return f"({', '.join(map(str, self.member_types))})"

class FunctionType(Type):
    """函数类型, e.g., fn(i32) -> i32"""

    def __init__(self, param_types: list[Type], return_type: Type):
        self.param_types = param_types
        self.return_type = return_type

    def __eq__(self, other):
        return super().__eq__(
            other) and self.param_types == other.param_types and self.return_type == other.return_type

    def __repr__(self):
        params = ', '.join(map(str, self.param_types))
        return f"fn({params}) -> {self.return_type}"



class Symbol:
    """存储在符号表中的对象"""
    def __init__(self, name, typ: Type, is_mutable=False, is_initialized=False, kind='variable'):
        self.name = name
        self.type = typ
        self.is_mutable = is_mutable
        self.is_initialized = is_initialized
        self.kind = kind # 'variable', 'function', 'parameter' 等
        #...

# 预定义一些类型
I32 = PrimitiveType('i32')
VOID = PrimitiveType('void')
ERROR_TYPE = PrimitiveType('error')

class SemanticChecker:
    def __init__(self):
        """
        初始化语义检查器。
        - env_stack: 符号表栈，用于管理作用域。列表中的每个元素是一个字典，代表一个作用域。
        - current_function_return_type: 用于检查函数内的return语句是否正确。
        """
        # WHY: 使用栈来管理作用域，是处理嵌套作用域（如函数、if块、循环块）的最经典、最有效的方法。
        self.env_stack = [{'$borrows':{}}]  # 全局作用域
        self.loop_break_type_stack=[]
        self.current_function_return_type = None
        self.in_loop_count = 0  # 跟踪循环嵌套深度，便于处理 break 和 continue 语句。

    class BorrowInfo:
        def __init__(self):
            self.mutable_borrow_active=False
            self.immutable_borrow_count=0

    # --- 作用域管理 ---
    def enter_scope(self):
        """进入一个新的作用域。"""
        self.env_stack.append({'$borrows':{}})

    def exit_scope(self):
        """退出当前作用域。"""
        self.env_stack.pop()

    # --- 符号表操作 ---
    def add_symbol(self, symbol: Symbol):
        """向当前作用域添加一个新符号。"""
        # WHY: 新声明的变量总是添加到最内层的作用域中。
        current_scope = self.env_stack[-1]
        if symbol.name in current_scope:
            # 允许重影。
            pass
        current_scope[symbol.name] = symbol

    def lookup_symbol(self, name: str) -> Symbol | None:
        """从内到外查找一个符号。"""
        # WHY: 查找时要从最内层作用域开始，这符合语言的变量查找规则。
        for scope in reversed(self.env_stack):
            if name in scope:
                return scope[name]
        return None

    def _resolve_type(self, type_node) -> Type:
        """将AST中的类型注解（字符串或元组）转换为内部的Type对象。"""
        if type_node == 'i32':
            return I32
        if isinstance(type_node, tuple):
            if type_node[0] == '&':
                return RefType(self._resolve_type(type_node[1]), is_mutable=False)
            if type_node[0] == '&mut':
                return RefType(self._resolve_type(type_node[1]), is_mutable=True)
            if type_node[0] == 'array':
                element_type = self._resolve_type(type_node[1])
                size = type_node[2]
                return ArrayType(element_type, size)

        if isinstance(type_node, TupleLiteral):
            member_types = [self._resolve_type(t) for t in type_node.elements]
            return TupleType(member_types)
        raise SemanticError(f"未知的类型注解：'{type_node}'")

    # --- Visitor Mode ---
    def check(self, node: ASTNode):
        """
        根据节点类型动态地调用对应的 `check_...` 方法，
        避免了在代码里写大量的 if/isinstance 判断，让代码更清晰、更易于扩展。
        """
        method_name = 'check_' + node.__class__.__name__
        if hasattr(self, method_name):
            return getattr(self, method_name)(node)
        else:
            # 提供一个默认的处理方式，用于遍历那些不需要特殊检查的节点
            self._check_children(node)
            return None # 大部分语句节点本身没有类型，返回None

    def _check_children(self, node: ASTNode):
        """一个默认的遍历所有子节点的方法。"""
        for field_name in vars(node):
            attr = getattr(node, field_name)
            if isinstance(attr, ASTNode):
                self.check(attr)
            elif isinstance(attr, list):
                for item in attr:
                    if isinstance(item, ASTNode):
                        self.check(item)

    def check_Program(self, node: Program):
        self._check_children(node)

    def check_NumberLit(self,node: NumberLit)-> Type:
        # 数字字面量的类型是 i32
        node.computed_type = I32
        return I32

    def check_Ident(self, node: Ident) -> Type:
        # 在符号表中查找标识符
        symbol = self.lookup_symbol(node.name)
        if not symbol:
            raise SemanticError(f"未声明的标识符 '{node.name}'", node.line, node.col)
        if not symbol.is_initialized:
            raise SemanticError(f"使用未初始化的变量 '{node.name}'", node.line, node.col)
        node.computed_type = symbol.type
        node.symbol_info = symbol
        return symbol.type

    def check_VarDecl(self,node:VarDecl):
        # 1.有初始值：检查初始值类型
        init_type=None
        if node.init:
            init_type=self.check(node.init)

            if init_type==VOID:
                raise SemanticError(f"不能将 'void' 类型的值赋给变量 '{node.name}'", node.line, node.col)

        # 2.确定变量类型
        var_type_from_annotation=None
        if node.typ:
            var_type_from_annotation = self._resolve_type(node.typ)

        final_type = var_type_from_annotation or init_type
        if final_type is None:
            raise SemanticError(f"变量 '{node.name}' 没有类型信息", node.line, node.col)

        if var_type_from_annotation and init_type and not (var_type_from_annotation == init_type):
            raise SemanticError(
                f"类型不匹配：变量 '{node.name}' 声明为 '{var_type_from_annotation}'，但初始值类型是 '{init_type}'",
                node.line, node.col)

        current_scope= self.env_stack[-1]
        if node.name in current_scope:
            current_borrows = current_scope['$borrows']
            if node.name in current_borrows:
                del current_borrows[node.name]  # 重置

        symbol = Symbol(
            name=node.name,
            typ=final_type,
            is_mutable=node.mutable,
            is_initialized=(node.init is not None)
        )
        self.add_symbol(symbol)

    def check_FuncDecl(self,node:FuncDecl):
        # 1.解析参数和返回类型，构建函数签名
        param_types = []
        for param in node.params:
            param_types.append(self._resolve_type(param.typ))

        return_type= VOID
        if node.ret_type:
            return_type = self._resolve_type(node.ret_type)

        func_type = FunctionType(param_types, return_type)

        # 在作用域注册
        func_symbol=Symbol(node.name, func_type, is_mutable=False, is_initialized=True,kind='function')
        self.add_symbol(func_symbol)

        # 2.进入函数作用域

        outer_return_type = self.current_function_return_type
        self.current_function_return_type = return_type

        self.enter_scope()

        # 将参数加入符号表
        for param in node.params:
            param_type = self._resolve_type(param.typ)
            param_symbol = Symbol(param.name, param_type, param.mutable, is_initialized=True, kind='parameter')
            self.add_symbol(param_symbol)

        # 3.检查函数体
        body_block_type=self.check(node.body)

        # if self.current_function_return_type != VOID and not (body_block_type == self.current_function_return_type):
        #     # # 特殊处理：如果函数期望返回 VOID，但块有值，在 Rust 中这也是一个警告或错误
        #     # if self.current_function_return_type == VOID and body_block_type != VOID:
        #     #     raise SemanticError(f"函数期望无返回值，但实际返回了 '{body_block_type}'", node.line, node.col)
        #
        #     print(f"!!DEBUG: {node.body.stmts[-1]}的类型是 {body_block_type}, 期望是 {self.current_function_return_type}")
        #     if body_block_type != self.current_function_return_type:
        #         raise SemanticError(
        #             f"函数返回类型不匹配：期望 '{self.current_function_return_type}'，但实际返回 '{body_block_type}'",
        #             node.line, node.col)

        # 4.退出函数作用域
        self.exit_scope()
        self.current_function_return_type = outer_return_type

    def check_ReturnStmt(self, node: ReturnStmt):
        if node.expr:
            actual_return_type=self.check(node.expr)
            if not actual_return_type == self.current_function_return_type:
                raise SemanticError(
                    f"返回类型不匹配：期望 '{self.current_function_return_type}'，但实际返回 '{actual_return_type}'",
                    node.line, node.col)
        else:
            if self.current_function_return_type != VOID:
                raise SemanticError(
                    f"函数 期望'{self.current_function_return_type}'类型的返回值，但没有提供",
                    node.line, node.col)

    def check_AssignStmt(self,node:AssignStmt):
        # 1.特殊处理left，不check
        if isinstance(node.target,Ident):
            target_name=node.target.name
            symbol = self.lookup_symbol(target_name)
            if not symbol:
                raise SemanticError(f"未声明的变量 '{target_name}'", node.line, node.col)
            if not symbol.is_mutable:
                if symbol.is_initialized:
                    raise SemanticError(f"不可变变量 '{target_name}' 不能被二次赋值", node.line, node.col)

            # 2.检查right
            expr_type=self.check(node.expr)

            # 3.类型匹配
            if not symbol.type == expr_type:
                raise SemanticError(
                    f"类型不匹配：变量 '{target_name}' 的类型是 '{symbol.type}'，但赋值表达式的类型是 '{expr_type}'",
                    node.line, node.col)

            # 4.更新符号状态
            symbol.is_initialized = True

            # 5.注解AST节点
            node.target.symbol_info = symbol
            node.target.computed_type = symbol.type
        elif isinstance(node.target,IndexExpr):
            target_element_type=self.check(node.target)

            if isinstance(node.target.base,Ident):
                base_symbol=self.lookup_symbol(node.target.base.name)
                if base_symbol and not base_symbol.is_mutable:
                    raise SemanticError(
                        f"不可变数组 '{base_symbol.name}' 不能被修改",
                        node.line, node.col)

            rhs_type=self.check(node.expr)
            if not target_element_type == rhs_type:
                raise SemanticError(
                    f"数组元素类型不匹配：期望 '{target_element_type}'，但实际是 '{rhs_type}'",
                    node.line, node.col)
        elif isinstance(node.target,MemberExpr):
            # 处理元组成员赋值
            member_type = self.check(node.target)

            if isinstance(node.target.base, Ident):
                base_symbol = self.lookup_symbol(node.target.base.name)
                if base_symbol and not base_symbol.is_mutable:
                    raise SemanticError(
                        f"不可变元组 '{base_symbol.name}' 不能被修改",
                        node.line, node.col)

            rhs_type = self.check(node.expr)
            if not member_type == rhs_type:
                raise SemanticError(
                    f"元组成员类型不匹配：期望 '{member_type}'，但实际是 '{rhs_type}'",
                    node.line, node.col)
        else:
            raise SemanticError(
                f"不支持的赋值目标： '{type(node.target).__name__}'",
                node.line, node.col)

    def check_FuncCall(self, node: FuncCall)->Type:
        # 1.查找函数符号
        if not isinstance(node.func,Ident):
            raise SemanticError("函数调用目标必须是一个标识符",node.func.line,node.func.col)

        func_name=node.func.name
        symbol=self.lookup_symbol(func_name)

        if not symbol:
            raise SemanticError(f"使用了未声明的函数 '{func_name}'", node.line, node.col)
        if symbol.kind != 'function':
            raise SemanticError(f"'{func_name}' 不是一个函数", node.line, node.col)
        # 2.获取函数签名
        if not isinstance(symbol.type,FunctionType):
            raise SemanticError(f"'{func_name}' 的类型不是函数", node.line, node.col)

        func_type:FunctionType =symbol.type

        # 3.检查实参数量
        expected_param_count = len(func_type.param_types)
        actual_param_count = len(node.args)

        if expected_param_count != actual_param_count:
            raise SemanticError(
                f"函数 '{func_name}' 期望 {expected_param_count} 个参数，但实际提供了 {actual_param_count} 个",
                node.line, node.col)

        # 4.检查实参类型
        for i,(arg_node,expected_param_type) in enumerate(zip(node.args,func_type.param_types)):
            actual_arg_type = self.check(arg_node)
            if actual_arg_type != expected_param_type:
                raise SemanticError(
                    f"参数 {i+1} 的类型不匹配：期望 '{expected_param_type}'，但实际是 '{actual_arg_type}'",
                    node.line, node.col)

        # 5.注解AST节点并返回
        node.computed_type = func_type.return_type
        node.func.symbol_info = symbol
        node.func.computed_type = func_type

        return func_type.return_type

    def check_BinaryOp(self,node:BinaryOp)->Type:
        # 1.检查左右操作数
        left_type = self.check(node.left)
        right_type = self.check(node.right)

        # 2.根据操作符和操作数类型进行类型推断
        if node.op in ('+', '-', '*', '/','==','!=','<','>','<=','>='):
            if left_type != I32 or right_type != I32:
                raise SemanticError(
                    f"运算 '{node.op}' 需要两个 'i32' 类型的操作数，但实际是 '{left_type}' 和 '{right_type}'",
                    node.line, node.col)
            node.computed_type = I32
            return I32

        # elif node.op in ('==', '!=', '<', '>', '<=', '>='):
        #     if left_type != I32 or right_type != I32:
        #         raise SemanticError(
        #             f"比较运算 '{node.op}' 需要两个 'i32' 类型的操作数，但实际是 '{left_type}' 和 '{right_type}'",
        #             node.line, node.col)
        #     node.computed_type = PrimitiveType('bool')
        #     return PrimitiveType('bool')


        else:
            raise SemanticError(f"未知的二元运算符 '{node.op}'", node.line, node.col)

    def check_IfStmt(self, node: IfStmt)->Type:
        # 1.检查条件表达式
        cond_type = self.check(node.cond)

        if cond_type != I32:
            raise SemanticError(f"if 条件表达式必须是 'i32' 类型，但实际是 '{cond_type}'", node.line, node.col)

        # 2.检查then
        then_type=self.check(node.then_body)

        # 3.检查else
        else_type=VOID
        if node.else_body is not None:
            else_type=self.check(node.else_body)
        if then_type == else_type:
            node.computed_type = then_type
            return then_type
        else:
            node.computed_type = VOID
            return VOID

    def check_Block(self, node: Block)->Type:
        self.enter_scope()
        block_type=VOID
        if not node.stmts:
            pass
        else:
            for stmt in node.stmts:
                self.check(stmt)
            # 最后一个语句可能有返回值
            last_stmt = node.stmts[-1]
            if isinstance(last_stmt, Expr):
                block_type = last_stmt.computed_type
        self.exit_scope()
        node.computed_type = block_type
        return block_type

    def check_WhileStmt(self, node: WhileStmt):
        # 1.检查条件表达式
        cond_type = self.check(node.cond)

        if cond_type != I32:
            raise SemanticError(f"while 条件表达式必须是 'i32' 类型，但实际是 '{cond_type}'", node.line, node.col)

        # 2.检查循环体
        self.in_loop_count+=1
        self.check(node.body)
        self.in_loop_count-=1

    def check_ForStmt(self,node:ForStmt):
        # 1.进入循环上下文
        self.in_loop_count += 1
        # 2.检查可迭代结构
        if node.end is not None:#start..end
            start_type = self.check(node.start)
            end_type = self.check(node.end)

            if start_type != I32 or end_type != I32:
                raise SemanticError(
                    f"for 循环的范围必须是 'i32' 类型，但实际是 '{start_type}' 和 '{end_type}'",
                    node.line, node.col)
            loop_var_type = I32
        else:
            #数组
            iterable_node=node.start
            iterable_type=self.check(iterable_node)

            if isinstance(iterable_type, ArrayType):
                loop_var_type = iterable_type.element_type
            else:
                raise SemanticError(f"for 循环的可迭代对象必须是数组，但实际是 '{iterable_type}'", node.line, node.col)

        # 3.创建作用域，添加循环变量符号
        self.enter_scope()
        loop_var_symbol = Symbol(
            name=node.name,
            typ=loop_var_type,
            is_mutable=node.mutable,
            is_initialized=True,
            kind='variable'
        )
        self.add_symbol(loop_var_symbol)

        # 4.检查循环体
        self.check(node.body)

        #退出作用域和循环上下文
        self.exit_scope()
        self.in_loop_count -= 1

    def check_LoopStmt(self, node: LoopStmt)->Type:
        """
        检查 loop 语句。
        - loop 语句本身没有条件，直接进入循环体。
        - 需要在循环体内处理 break 和 continue。
        """
        self.in_loop_count += 1
        self.loop_break_type_stack.append(None)
        self.check(node.body)
        self.in_loop_count -= 1
        break_type= self.loop_break_type_stack.pop()
        if break_type is None:
            # 如果没有明确的 break 类型，默认是 VOID
            break_type = VOID
        node.computed_type = break_type
        return break_type

    def check_BreakStmt(self, node: BreakStmt):
        if self.in_loop_count == 0:
            raise SemanticError("break 语句只能在循环内部使用", node.line, node.col)

        if not self.loop_break_type_stack:
            if node.expr:
                raise SemanticError("在没有循环上下文的情况下使用带值的 break 语句", node.line, node.col)
            return

        expected_break_type = self.loop_break_type_stack[-1]
        if node.expr:
            # break <expr>;
            break_expr_type = self.check(node.expr)
            if expected_break_type is None:
                self.loop_break_type_stack[-1]= break_expr_type
            elif not (break_expr_type==expected_break_type):
                raise SemanticError(f"循环表达式中break的返回类型不一致： '{expected_break_type}' vs '{break_expr_type}'",
                                    node.line, node.col)
        else:
            # break;
            if expected_break_type is None:
                self.loop_break_type_stack[-1] = VOID
            elif expected_break_type!=VOID:
                raise SemanticError(f"在循环中使用无值的 break 语句，但期望有返回值", node.line, node.col)



    def check_ContinueStmt(self, node: ContinueStmt):
        if self.in_loop_count == 0:
            raise SemanticError("continue 语句只能在循环内部使用", node.line, node.col)


    def _get_borrow_info(self, var_name:str)->BorrowInfo:
        current_borrows= self.env_stack[-1]['$borrows']
        if var_name not in current_borrows:
            current_borrows[var_name] = self.BorrowInfo()
        return current_borrows[var_name]

    def _lookup_borrow_info(self, var_name:str)->BorrowInfo|None:
        for scope in reversed(self.env_stack):
            if var_name in scope['$borrows']:
                return scope['$borrows'][var_name]
        return None

    def check_BorrowExpr(self,node:BorrowExpr)->Type:
        # 1.检查被借用的表达式
        if not isinstance(node.expr, Ident):
            raise SemanticError("借用操作只能用于具名变量", node.line, node.col)

        target_name = node.expr.name
        target_symbol=self.lookup_symbol(target_name)
        if not target_symbol:
            raise SemanticError(f"未声明的变量 '{target_name}'", node.line, node.col)
        # 2.查找已存在借用信息
        existing_borrow = self._lookup_borrow_info(target_name)

        #3.根据借用类型进行处理
        if node.mutable:
            # 可变借用
            if existing_borrow and (existing_borrow.mutable_borrow_active or existing_borrow.immutable_borrow_count > 0):
                raise SemanticError(f"变量 '{target_name}' 已经被借用，不能进行可变借用", node.line, node.col)
            if not target_symbol.is_mutable:
                raise SemanticError(f"变量 '{target_name}' 不是可变的，不能进行可变借用", node.line, node.col)
            # 更新借用信息
            borrow_info = self._get_borrow_info(target_name)
            borrow_info.mutable_borrow_active = True
        else:
            if existing_borrow and existing_borrow.mutable_borrow_active:
                raise SemanticError(f"变量 '{target_name}' 已经被可变借用，不能进行不可变借用", node.line, node.col)
            # 更新借用信息
            borrow_info = self._get_borrow_info(target_name)
            borrow_info.immutable_borrow_count += 1
        # 4.创建引用类型
        result_type = RefType(target_symbol.type, is_mutable=node.mutable)
        node.computed_type = result_type
        return result_type


    def check_DerefExpr(self,node:DerefExpr)->Type:
        # 1.检查被解引用的表达式
        ref_type = self.check(node.expr)

        # 2.检查类型
        if not isinstance(ref_type, RefType):
            raise SemanticError(f"解引用操作只能用于引用类型，但实际是 '{ref_type}'", node.line, node.col)

        # 3.返回被引用的类型
        result_type = ref_type.target_type
        node.computed_type = result_type
        return result_type

    def check_ArrayLiteral(self,node:ArrayLiteral)->Type:
        if not node.elements:
            #空数组不支持
            return ArrayType(ERROR_TYPE, 0)

        # 1.检查元素类型
        first_type = self.check(node.elements[0])
        for elem in node.elements[1:]:
            elem_type = self.check(elem)
            if elem_type != first_type:
                raise SemanticError(
                    f"数组元素类型不一致：第一个元素是 '{first_type}'，但后续元素是 '{elem_type}'",
                    node.line, node.col)

        # 2.构造数组类型
        array_type = ArrayType(first_type, len(node.elements))
        node.computed_type = array_type
        return array_type

    def check_IndexExpr(self,node:IndexExpr)->Type:
        # 1.检查Base
        base_type = self.check(node.base)
        if not isinstance(base_type, ArrayType):
            raise SemanticError(f"索引操作只能用于数组类型，但实际是 '{base_type}'", node.line, node.col)

        # 2.检查idx
        index_type = self.check(node.index)
        if not (index_type == I32):
            raise SemanticError(f"索引操作的索引必须是 'i32' 类型，但实际是 '{index_type}'", node.line, node.col)

        #检查数组越界
        if isinstance(node.index, NumberLit):
            index_value = node.index.value
            if not (0 <= index_value < base_type.size):
                raise SemanticError(
                    f"数组索引越界：索引 {index_value} 超出数组范围 [0, {base_type.size - 1}]",
                    node.line, node.col)


        # 3.返回元素类型
        element_type = base_type.element_type
        node.computed_type = element_type
        return element_type


    def check_TupleLiteral(self, node: TupleLiteral) -> Type:
        # 1.收集所有元素的类型
        member_types = []
        for elem in node.elements:
            elem_type = self.check(elem)
            member_types.append(elem_type)

        # 2.构造元组类型
        tuple_type = TupleType(member_types)
        node.computed_type = tuple_type
        return tuple_type

    def check_MemberExpr(self,node:MemberExpr)->Type:
        # 1.检查base
        base_type = self.check(node.base)
        if not isinstance(base_type,TupleType):
            raise SemanticError(f"成员访问只能用于元组类型，但实际是 '{base_type}'", node.line, node.col)
        # 2.检查成员索引
        index = node.field

        if not (0 <= index < len(base_type.member_types)):
            raise SemanticError(
                f"元组索引越界：索引 {index} 超出元组范围 [0, {len(base_type.member_types) - 1}]",
                node.line, node.col)
        # 3.返回成员类型
        member_type = base_type.member_types[index]
        node.computed_type = member_type
        return member_type


if __name__ == "__main__":
    from lexer import tokenize_file
    from lr1_parser import LR1Parser
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'tmp.rs'
    try:
        tokens=tokenize_file(filepath)
        parser = LR1Parser()
        ast = parser.parse(tokens)
        checker = SemanticChecker()
        checker.check(ast)
        print("语义检查通过！")
        #中间代码生成
        from ir_generator import IRGenerator
        ir_gen = IRGenerator()
        ir_gen.generate(ast)
        for quad in ir_gen.code:
            print(quad)
    except (SemanticError,SyntaxError) as e:
        print(f"错误：{e}")
        sys.exit(1)
    except Exception:
        print("发生了一个意外错误：")
        traceback.print_exc()
        sys.exit(1)