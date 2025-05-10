# lr1_parser.py

import os
import pickle
import sys
from lexer import tokenize_file, TokenKind, Token
from ast_nodes import *
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

PARSE_TABLE_FILE = 'parse_tables.pkl'


class LR1Parser:
    def __init__(self):
        # 尝试加载离线生成的解析表
        if os.path.exists(PARSE_TABLE_FILE):
            with open(PARSE_TABLE_FILE, 'rb') as f:
                G, ACTION, GOTO = pickle.load(f)
        else:
            # 动态构建并保存
            from grammar import build_grammar, build_lr1_states, build_parse_table
            G = build_grammar()
            C, first = build_lr1_states(G)
            ACTION, GOTO = build_parse_table(C, G, first)
            with open(PARSE_TABLE_FILE, 'wb') as f:
                pickle.dump((G, ACTION, GOTO), f)

        self.grammar = G
        self.ACTION  = ACTION
        self.GOTO    = GOTO

    def parse(self, tokens, trace_output=None):
        def _symbol_repr(s):
            # print(f"type: {type(s)}, isinstance(s, ASTNode): {isinstance(s, ASTNode)}")
            if isinstance(s, Token):
                return f"{s.kind.name}({s.value})"
            elif isinstance(s, ASTNode):
                return s.__class__.__name__
            elif isinstance(s, tuple):
                return f"tuple({', '.join(str(x) for x in s)})"
            else:
                return str(s)

        state_stack = [0]
        symbol_stack = []
        idx = 0

        while True:
            state = state_stack[-1]
            tok = tokens[idx]

            if tok.kind == TokenKind.IDENT:
                look = 'IDENT'
            elif tok.kind == TokenKind.NUMBER:
                look = 'NUMBER'
            else:
                look = tok.value if tok.value != '' else '$'

            action = self.ACTION[state].get(look)
            if action is None:
                raise SyntaxError(f"Unexpected token {tok!r} (lookahead={look}) in state {state}")

            cmd, arg = action

            if cmd == 'shift':
                if trace_output is not None:
                    trace_output.append({
                        'state': list(state_stack),
                        'symbol': [_symbol_repr(s) for s in symbol_stack],
                        'input': [str(t.value) for t in tokens[idx:]],
                        'action': f'shift {arg}'
                    })
                state_stack.append(arg)
                symbol_stack.append(tok)
                idx += 1

            elif cmd == 'reduce':
                prod = arg
                if trace_output is not None:
                    rhs_str = ' '.join(prod.rhs) if prod.rhs else 'ε'
                    trace_output.append({
                        'state': list(state_stack),
                        'symbol': [_symbol_repr(s) for s in symbol_stack],
                        'input': [str(t.value) for t in tokens[idx:]],
                        'action': f'reduce {prod.lhs} → {rhs_str}'
                    })

                n = len(prod.rhs)

                if n == 0:
                    goto_state = self.GOTO[state_stack[-1]].get(prod.lhs)
                    if goto_state == state_stack[-1]:
                        raise RuntimeError(
                            f"infinite ε‑reduce on {prod} with lookahead {look}"
                        )

                children = [symbol_stack.pop() for _ in range(n)]
                children.reverse()
                for _ in range(n):
                    state_stack.pop()

                node = self._make_node(prod, children)
                symbol_stack.append(node)

                goto_state = self.GOTO[state_stack[-1]][prod.lhs]
                state_stack.append(goto_state)

            elif cmd == 'accept':
                if trace_output is not None:
                    trace_output.append({
                        'state': list(state_stack),
                        'symbol': [_symbol_repr(s) for s in symbol_stack],
                        'input': [],
                        'action': 'accept'
                    })
                return symbol_stack[-1]

    def _make_node(self, prod, children):
        """
        根据 prod.lhs 和 prod.rhs，用 children 列表构造对应 AST 节点。
        children 是一个列表，按产生式右侧符号的顺序对应。
        """
        lhs, rhs = prod.lhs, prod.rhs
        # print(f"==> MAKING NODE: {lhs} ← {rhs}")
        # print(f"BUILD NODE: {lhs}  <- {[type(c) for c in children]}")
        # ① 语句块 ----------------------------------------------------------
        # Block → { StmtList }
        if lhs == 'Block' and rhs == ['{', 'StmtList', '}']:
            stmt_list = children[1]  # children = ['{', StmtList, '}']
            return Block(stmt_list)

        # Block → { Stmt StmtList }
        if lhs == 'Block' and rhs == ['{', 'Stmt', 'StmtList', '}']:
            return Block([children[1]] + children[2])

        if lhs == 'Block' and rhs == ['{', '}']:
            return Block([])

        # ② 语句串 ----------------------------------------------------------
        # if lhs == 'StmtList':
        #     print("==> STMTLIST", rhs, children)
        # StmtList → ε
        if lhs == 'StmtList' and not rhs:
            return []

        # StmtList → Stmt
        if lhs == 'StmtList' and rhs == ['Stmt']:
            # print("!!! DEBUG: StmtList → Stmt, got:", children[0])
            return [children[0]]

        # StmtList → Stmt StmtList
        if lhs == 'StmtList' and rhs == ['Stmt', 'StmtList']:
            return [children[0]] + children[1]

        # VariableInternal -> mut IDENT
        if lhs == 'VariableInternal' and rhs == ['mut', 'IDENT']:
            ident_tok = children[1]  # Token of kind IDENT
            return VarBinding(ident_tok.value, mutable=True)

        # VariableInternal -> IDENT
        if lhs == 'VariableInternal' and rhs == ['IDENT']:
            ident_tok = children[0]
            return VarBinding(ident_tok.value, mutable=False)

        # Program → DeclList
        if lhs == 'Program' and rhs == ['DeclList']:
            decls = children[0]
            return Program(decls)

        # DeclList → ε
        if lhs == 'DeclList' and not rhs:
            return []

        # DeclList → Decl DeclList
        if lhs == 'DeclList' and rhs == ['Decl', 'DeclList']:
            # print("!!! DEBUG: DeclList join", children[0])
            return [children[0]] + children[1]

        # Decl → FnDecl
        if lhs == 'Decl' and rhs == ['FnDecl']:
            return children[0]

        # FnDecl → FnHead Block
        if lhs == 'FnDecl' and rhs == ['FnHead', 'Block']:
            # print(f"!!! DEBUG FnDecl children[0]: {children[0]}")
            name, params, ret = children[0]
            body = children[1]
            return FuncDecl(name, params, ret, body)

        # FnDecl → FnHead FuncExprBlock
        if lhs == 'FnDecl' and rhs == ['FnHead', 'FuncExprBlock']:
            name, params, ret = children[0]
            body = children[1]
            return FuncDecl(name, params, ret, body)

        # FnHead → fn IDENT ( ParamList ) [-> Type]
        if lhs == 'FnHead':
            # print(f"!!! DEBUG: FnHead match {rhs}")
            # 带返回类型
            if rhs == ['fn', 'IDENT', '(', 'ParamList', ')', '->', 'Type']:
                name_tok = children[1]
                plist    = children[3]
                typ      = children[6]
                return (name_tok.value, plist, typ)
            # 无返回类型
            if rhs == ['fn', 'IDENT', '(', 'ParamList', ')']:
                name_tok = children[1]
                plist    = children[3]
                return (name_tok.value, plist, None)

        # ParamList 相关
        if lhs == 'ParamList':
            if not rhs:
                return []
            if rhs == ['Param']:
                return [children[0]]
            if rhs == ['Param', ',', 'ParamList']:
                return [children[0]] + children[2]

        # Param → VariableInternal : Type
        if lhs == 'Param' and rhs == ['VariableInternal', ':', 'Type']:
            var, typ = children[0], children[2]
            return Param(var.name, var.mutable, typ)

        # ReturnStmt
        if lhs == 'ReturnStmt':
            if rhs == ['return', ';']:
                print("!!! building ReturnStmt(None)")
                return ReturnStmt(None)
            if rhs == ['return', 'Expr', ';']:
                return ReturnStmt(children[1])

        # SelectExpr → if Expr FuncExprBlock else FuncExprBlock
        if lhs == 'SelectExpr':
            cond, then_blk, else_blk = children[1], children[2], children[4]
            return IfStmt(cond, then_blk, else_blk)  # 复用现有 IfStmt AST

        # LoopExpr → loop FuncExprBlock
        if lhs == 'LoopExpr':
            body = children[1]
            return LoopStmt(body)  # 或自定义 LoopExpr 节点


        elif lhs == 'FuncExprBlock':
            stmts = children[1]
            if not isinstance(stmts, list):
                stmts = [ExprStmt(stmts)]
            elif stmts and isinstance(stmts[-1], (NumberLit, Ident, BinaryOp, FuncCall, IndexExpr, MemberExpr)):
                last = stmts.pop()
                stmts.append(ReturnStmt(last))
            return Block(stmts)

        elif lhs == 'Block':
            # 普通 Block 不自动包裹 ReturnStmt（避免 main 中的问题）
            stmts = children[1]
            if not isinstance(stmts, list):
                stmts = [ExprStmt(stmts)]
            for i, stmt in enumerate(stmts):
                print(f"[Block] stmt[{i}] = {stmt}")
            return Block(stmts)

        # break Expr ;
        # if lhs == 'Stmt' and rhs == ['break', 'Expr', ';']:
        #     return BreakStmt(children[1])  # 带值 break
        if lhs == 'FuncStmtList':
            if rhs == ['Stmt']:
                stmt = children[0]
                if isinstance(stmt, Expr):
                    stmt = ReturnStmt(stmt)
                return [stmt]

            if rhs == ['Stmt', 'FuncStmtList']:
                first = children[0]
                rest = children[1]
                if not isinstance(rest, list):
                    rest = [rest]
                if rest and isinstance(rest[-1], Expr):
                    last = rest.pop()
                    rest.append(ReturnStmt(last))
                return [first] + rest

        # 变量声明与赋值
        if lhs == 'Stmt':
            stmt = children[0]

            # 处理裸分号 => EmptyStmt
            if isinstance(stmt, Token) and stmt.kind == TokenKind.DELIM and stmt.value == ';':
                return EmptyStmt()
            # return ;
            if rhs == ['ReturnStmt']:
                return children[0]
            if rhs == ['return', ';']:
                return ReturnStmt(None)
            if rhs == ['return', 'Expr', ';']:
                return ReturnStmt(children[1])


            # break Expr ;
            if rhs == ['break', 'Expr', ';']:
                expr = children[1]
                return BreakStmt(expr)
            # let VariableInternal : Type = Expr ;
            if rhs == ['let', 'VariableInternal', '=', 'Expr', ';']:
                var = children[1]
                expr = children[3]
                if isinstance(expr, ExprStmt):
                    expr = expr.expr
                return VarDecl(var.name, var.mutable, None, expr)

            # let VariableInternal : Type = Expr ;
            if rhs == ['let', 'VariableInternal', ':', 'Type', '=', 'Expr', ';']:
                var = children[1]
                typ = children[3]
                expr = children[5]
                if isinstance(expr, ExprStmt):
                    expr = expr.expr
                return VarDecl(var.name, var.mutable, typ, expr)
            # let VariableInternal : Type ;
            if rhs == ['let', 'VariableInternal', ':', 'Type', ';']:
                var = children[1]
                typ = children[3]
                return VarDecl(var.name, var.mutable, typ, None)
            # let VariableInternal ;
            if rhs == ['let', 'VariableInternal', ';']:
                var = children[1]
                return VarDecl(var.name, var.mutable, None, None)
            # Assignable = Expr ;
            if rhs == ['Assignable', '=', 'Expr', ';']:
                target = children[0]
                expr = children[2]
                if isinstance(expr, ExprStmt):
                    expr = expr.expr
                if isinstance(target, ExprStmt):  # <<< 需要加这句
                    target = target.expr
                return AssignStmt(target, expr)
            # if Expr Block ElsePart
            if rhs == ['if', 'Expr', 'Block', 'ElsePart']:
                cond = children[1]
                then_blk = children[2]
                else_blk = children[3]
                return IfStmt(cond, then_blk, else_blk)
            # while Expr Block
            if rhs == ['while', 'Expr', 'Block']:
                return WhileStmt(children[1], children[2])
            if rhs == ['for', 'VariableInternal', 'in', 'Iterable', 'Block']:
                var = children[1]
                iterable = children[3]
                body_blk = children[4]

                # 如果 iterable 是 range 形式（通过上面 grammar 的 ['Expr', '..', 'Expr'] 规则构造）
                if isinstance(iterable, tuple) and iterable[0] == 'range':
                    start, end = iterable[1], iterable[2]
                    return ForStmt(var.name, var.mutable, start, end, body_blk)

                # 否则直接留给语义检查处理
                return ForStmt(var.name, var.mutable, iterable, None, body_blk)
            # loop Block
            if rhs == ['loop', 'Block']:
                return LoopStmt(children[1])
            # break ;
            if rhs == ['break', ';']:
                return BreakStmt()
            # continue ;
            if rhs == ['continue', ';']:
                return ContinueStmt()
            # Stmt → Expr ;
            if rhs == ['Expr', ';']:
                expr = children[0]
                return ExprStmt(expr)

        if lhs == 'Iterable' and rhs == ['Expr', '..', 'Expr']:
            return ('range', children[0], children[2])
        if lhs == 'Iterable' and rhs == ['Expr']:
            return children[0]

        # Expr → comparisons or AddExpr
        if lhs == 'Expr':
            # 比较运算
            for op in ('==','!=','<','<=','>','>='):
                if rhs == ['Expr', op, 'Expr']:
                    return BinaryOp(op, children[0], children[2])
            # 回退到 AddExpr
            if rhs == ['AddExpr']:
                return children[0]

        if lhs == 'ElsePart' and rhs == ['else', 'Block']:
            return children[1]

        if lhs == 'ElsePart' and rhs == ['else', 'if', 'Expr', 'Block', 'ElsePart']:
            cond = children[2]
            then_blk = children[3]
            else_blk = children[4]
            return Block([IfStmt(cond, then_blk, else_blk)])

        if lhs == 'ElsePart' and not rhs:
            return None

        # AddExpr / MulExpr
        if lhs == 'AddExpr':
            if rhs == ['AddExpr', '+', 'MulExpr']:
                return BinaryOp('+', children[0], children[2])
            if rhs == ['AddExpr', '-', 'MulExpr']:
                return BinaryOp('-', children[0], children[2])
            if rhs == ['MulExpr']:
                return children[0]

        if lhs == 'MulExpr':
            if rhs == ['MulExpr', '*', 'Primary']:
                return BinaryOp('*', children[0], children[2])
            if rhs == ['MulExpr', '/', 'Primary']:
                return BinaryOp('/', children[0], children[2])
            if rhs == ['Primary']:
                return children[0]

        # Primary
        if lhs == 'Primary':
            # IDENT ( ArgList )
            if rhs == ['IDENT', '(', 'ArgList', ')']:
                args = children[2] if children[2] is not None else []
                return FuncCall(Ident(children[0].value), args)
            # ( Expr )
            if rhs == ['(', 'Expr', ')']:
                return children[1]
            # NUMBER
            if rhs == ['NUMBER']:
                return NumberLit(int(children[0].value,0))
            # Assignable
            if rhs == ['Assignable']:
                return children[0]
            # * Primary
            if rhs == ['*', 'Primary']:
                return DerefExpr(children[1])
            # & Primary
            if rhs == ['&', 'Primary']:
                return BorrowExpr(children[1], mutable=False)
            # & mut Primary
            if rhs == ['&', 'mut', 'Primary']:
                return BorrowExpr(children[2], mutable=True)
            # [ ExprList ]
            if rhs == ['[', 'ExprList', ']']:
                return ArrayLiteral(children[1])
            # ( ExprList )
                # 单元素元组 (Expr, )
            if rhs == ['(', 'Expr', ',', ')']:
                return TupleLiteral([children[1]])

            # 多元素元组 (Expr, ExprList)
            if rhs == ['(', 'Expr', ',', 'ExprList', ')']:
                return TupleLiteral([children[1]] + children[3])

            # 空元组 ()
            if rhs == ['(', ')']:
                return TupleLiteral([])
            if rhs == ['IDENT']:
                return Ident(children[0].value)

        # ExprList
        if lhs == 'ExprList':
            if not rhs:
                return []
            if rhs == ['Expr']:
                return [children[0]]
            if rhs == ['Expr', ',', 'ExprList']:
                return [children[0]] + children[2]

        # Assignable
        if lhs == 'Assignable':
            if rhs == ['Primary', '[', 'Expr', ']']:
                return IndexExpr(children[0], children[2])
            if rhs == ['Primary', '.', 'NUMBER']:
                return MemberExpr(children[0], int(children[2].value,0))
            if rhs == ['IDENT']:
                return Ident(children[0].value)
            if rhs == ['*', 'Primary']:
                return DerefExpr(children[1])

        # Type (keep as simple strings or tuples)
        if lhs == 'Type':
            if rhs == ['i32']:
                return 'i32'
            if rhs == ['&', 'Type']:
                return ('&', children[1])
            if rhs == ['&', 'mut', 'Type']:
                return ('&mut', children[2])
            if rhs == ['[', 'Type', ';', 'NUMBER', ']']:
                return ('array', children[1], int(children[3].value,0))
            if rhs == ['(', ')']:
                return TupleLiteral([])
            if rhs == ['(', 'TypeList', ')']:
                return TupleLiteral(children[1])

        if lhs == 'TypeList':
            if rhs == ['Type']:
                return [children[0]]
            if rhs == ['Type', ',', 'TypeList']:
                return [children[0]] + children[2]

        # Fallback
        if not children:
            return None
        last = children[-1]
        if isinstance(last, Expr):
            return last
        while isinstance(last, ExprStmt):
            last = last.expr
        if isinstance(last, Token):
            return Ident(last.value)
        return last


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("用法: python lr1_parser.py <源文件.rs>")
        sys.exit(1)

    # 分词
    tokens = tokenize_file(sys.argv[1])

    # 解析
    parser = LR1Parser()
    ast = parser.parse(tokens)

    # 格式化输出 AST
    print(str(ast))

    dot = ast.graphviz()
    dot.format = 'png'
    dot.render('ast', view=True)