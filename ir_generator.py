from ast_nodes import *

class IRGenerator:
    def __init__(self):
        self.code = []          # 存储四元组列表，形如 (op, arg1, arg2, result)
        self.temp_count = 0     # 临时变量计数器
        self.temp_label=0
        self.loop_stack = []  # 用于管理 break/goto label

    def new_temp(self): #生成唯一的临时变量名t1, t2...
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.temp_label += 1
        return f"L{self.temp_label}"

    def generate(self, node): #根据传入AST节点类型，动态调用对应的gen_类型名函数生成IR
        """主入口，根据节点类型调度到对应方法"""
        method_name = 'gen_' + node.__class__.__name__
        method = getattr(self, method_name, self.gen_default)
        return method(node)

    def gen_default(self, node):
        raise NotImplementedError(f"IR generation not implemented for {node.__class__.__name__}")

    def gen_Program(self, node): #遍历程序根节点的所有子节点，递归生成IR
        for item in node.items:
            self.generate(item)

    def gen_FuncDecl(self, node: FuncDecl):
        # 生成函数声明，生成label，处理参数，生成函数体
        self.code.append(('func_start', node.name, None, None))
        for param in node.params:
            self.generate(param)
        ret_val = self.generate(node.body)  # 获取 block 的返回值
        if ret_val is not None:
            self.code.append(('return', ret_val, None, None))
        self.code.append(('func_end', node.name, None, None))

    def gen_Param(self, node: Param):
        self.code.append(('param', node.name, node.typ, None))
        pass

    def gen_VarBinding(self, node: VarBinding):
        # 生成绑定表达式的值
        val = self.generate(node.expr)  # 递归生成表达式结果
        # 生成赋值代码，将表达式结果赋给变量名
        var_name = node.name if isinstance(node.name, str) else self.generate(node.name)
        self.code.append(('assign', val, None, var_name))
        return var_name

    def gen_VarDecl(self, node):
        # 先生成变量声明
        self.code.append(('decl', node.name, node.typ, None))
        # 若有初始化表达式，再生成赋值四元组
        if node.init:
            # 如果初始化是 Block或 IfStmt，则标记为表达式上下文
            if isinstance(node.init, (Block,IfStmt)):
                node.init.as_expr = True
            val = self.generate(node.init)
            self.code.append(('assign', val, None, node.name))
        else:
            # 无初始化不生成代码，假设声明在符号表
            pass

    def gen_AssignStmt(self, node):
        val = self.generate(node.expr)
        # 赋值四元组 (assign, val, None, target)
        target_name = node.target.name if hasattr(node.target, 'name') else str(node.target)
        self.code.append(('assign', val, None, target_name))

    def gen_ReturnStmt(self, node): #生成返回语句四元组
        if node.expr is not None:
            val = self.generate(node.expr)
        else:
            val = None
        self.code.append(('return', val, None, None))

    def gen_IfStmt(self, node: IfStmt):
        cond = self.generate(node.cond)
        label_then = self.new_label()
        label_else = self.new_label()
        label_end = self.new_label()

        # 如果当前 If 是表达式上下文（例如 let x = if ...）
        if getattr(node, 'as_expr', False):
            result_temp = self.new_temp()
            self.code.append(('if_false_goto', cond, None, label_else))
            val_then = self.generate(node.then_body)
            self.code.append(('assign', val_then, None, result_temp))
            self.code.append(('goto', None, None, label_end))
            self.code.append(('label', None, None, label_else))
            val_else = self.generate(node.else_body)
            self.code.append(('assign', val_else, None, result_temp))
            self.code.append(('label', None, None, label_end))
            return result_temp
        else:
            # 普通语句形式的 if 处理逻辑不变
            self.code.append(('if_false_goto', cond, None, label_else))
            self.generate(node.then_body)
            self.code.append(('goto', None, None, label_end))
            self.code.append(('label', None, None, label_else))
            if node.else_body:
                self.generate(node.else_body)
            self.code.append(('label', None, None, label_end))

    def gen_WhileStmt(self, node: WhileStmt):
        start_label = self.new_label()
        end_label = self.new_label()

        # 压栈循环信息
        self.loop_stack.append({'break': end_label, 'continue': start_label})

        self.code.append(('label', None, None, start_label))
        cond = self.generate(node.cond)
        self.code.append(('if_false_goto', cond, None, end_label))
        self.generate(node.body)
        # 判断上一条语句是不是 break 或 return 或 continue 跳转了
        if not self.code or self.code[-1][0] not in ('goto', 'return'):
            self.code.append(('goto', None, None, start_label))
        self.code.append(('label', None, None, end_label))

        # 弹出当前循环上下文
        self.loop_stack.pop()

    def gen_ForStmt(self, node: ForStmt):
        loop_var = node.name  # 循环变量名
        start_temp = self.generate(node.start)  # 计算起始值
        self.code.append(('assign', start_temp, None, loop_var))  # i = start

        label_cond = self.new_label()  # 条件检查位置
        label_body = self.new_label()  # 循环体
        label_end = self.new_label()  # 循环结束

        # 压栈循环信息
        self.loop_stack.append({'break': label_end, 'continue': label_cond})

        # 条件判断标签
        self.code.append(('goto', None, None, label_cond))  # 初始跳转到条件判断
        self.code.append(('label', None, None, label_body))  # 循环体开始

        # 生成循环体代码
        self.generate(node.body)

        # i = i + 1
        i_plus_1 = self.new_temp()
        self.code.append(('+', loop_var, '1', i_plus_1))
        self.code.append(('assign', i_plus_1, None, loop_var))

        # 条件判断
        self.code.append(('label', None, None, label_cond))
        end_temp = self.generate(node.end)
        cond_temp = self.new_temp()
        self.code.append(('<', loop_var, end_temp, cond_temp))
        self.code.append(('if_false_goto', cond_temp, None, label_end))  # 如果条件不满足，跳出
        self.code.append(('goto', None, None, label_body))  # 否则执行循环体

        self.code.append(('label', None, None, label_end))  # 循环结束
        self.loop_stack.pop()

    def gen_LoopStmt(self, node: LoopStmt):
        label_start = self.new_label()
        label_end = self.new_label()
        result_temp = self.new_temp()

        # 压栈循环信息
        self.loop_stack.append({'break': label_end, 'continue': label_start,'result': result_temp})

        self.code.append(('label', None, None, label_start))
        self.generate(node.body)
        # 判断上一条语句是不是 break 或 return 或 continue 跳转了
        if not self.code or self.code[-1][0] not in ('goto', 'return'):
            self.code.append(('goto', None, None, label_start))
        #self.code.append(('goto', None, None, label_start))
        self.code.append(('label', None, None, label_end))
        #  出栈，离开 loop 环境
        self.loop_stack.pop()
        return result_temp

    def gen_BreakStmt(self, node: BreakStmt):
        if not self.loop_stack:
            raise Exception(f"break not inside loop at line {node.line}")
        break_label = self.loop_stack[-1]['break']
        result_temp = self.loop_stack[-1].get('result')

        if node.expr and result_temp:
            val = self.generate(node.expr)
            self.code.append(('assign', val, None, result_temp))
        self.code.append(('goto', None, None, break_label))

    def gen_ContinueStmt(self, node: ContinueStmt):
        if not self.loop_stack:
            raise Exception(f"continue not inside loop at line {node.line}")
        continue_label = self.loop_stack[-1]['continue']
        self.code.append(('goto', None, None, continue_label))

    def gen_ExprStmt(self, node: ExprStmt):
        val=self.generate(node.expr)
        self.code.append(('eval', val, None, None))  # 记录被求值但未使用的表达式?

    def gen_EmptyStmt(self, node: EmptyStmt):
        pass  # 不生成代码

    def gen_Block(self, node: Block):
        # 判断是否作为表达式使用，例如 let x = { ... };
        if getattr(node, 'as_expr', False):
            for stmt in node.stmts[:-1]:
                self.generate(stmt)
            last_stmt = node.stmts[-1]
            if isinstance(last_stmt, ExprStmt):
                return self.generate(last_stmt.expr)
            else:
                return self.generate(last_stmt)
        else:
            ret_val = None
            for stmt in node.stmts:
                val = self.generate(stmt)
                if isinstance(stmt, (BreakStmt, ContinueStmt, ReturnStmt)):
                    break
                ret_val = val  # 记录最后一个表达式语句的值
            return ret_val

    def gen_BinaryOp(self, node): #递归生成左、右子表达式的值，生成二元操作四元组，结果存入新临时变量
        left = self.generate(node.left)
        right = self.generate(node.right)
        temp = self.new_temp()
        self.code.append((node.op, left, right, temp))
        return temp

    def gen_NumberLit(self, node): #直接返回数字常量字符串
        return str(node.value)

    def gen_Ident(self, node): #返回标识符名字
        return node.name

    def gen_FuncCall(self, node): #递归生成函数名和参数表达式，生成调用四元组，结果存入临时变量
        args = []
        for arg in node.args:
            val = self.generate(arg)
            args.append(val)
        temp = self.new_temp()
        func_name = self.generate(node.func) if isinstance(node.func, ASTNode) else str(node.func)
        # 假设四元组：('call', func_name, arg_list, result)
        self.code.append(('call', func_name, args, temp))
        return temp

    def gen_ArrayLiteral(self, node: ArrayLiteral):
        elements = [self.generate(elem) for elem in node.elements]
        temp = self.new_temp()
        self.code.append(('array_literal', elements, None, temp))
        return temp

    def gen_TupleLiteral(self, node: TupleLiteral):
        elements = [self.generate(elem) for elem in node.elements]
        temp = self.new_temp()
        self.code.append(('tuple_literal', elements, None, temp))
        return temp

    def gen_DerefExpr(self, node: DerefExpr):
        addr = self.generate(node.expr)
        temp = self.new_temp()
        self.code.append(('deref', addr, None, temp))
        return temp

    def gen_BorrowExpr(self, node: BorrowExpr):
        expr = self.generate(node.expr)
        temp = self.new_temp()
        self.code.append(('borrow_mut' if node.mutable else 'borrow', expr, None, temp))
        return temp

    def gen_IndexExpr(self, node: IndexExpr):
        base = self.generate(node.base)
        index = self.generate(node.index)
        temp = self.new_temp()
        self.code.append(('index', base, index, temp))
        return temp

    def gen_MemberExpr(self, node: MemberExpr):
        base = self.generate(node.base)
        temp = self.new_temp()
        self.code.append(('member_access', base, node.field, temp))
        return temp