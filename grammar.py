# grammar.py  – 覆盖版
from collections import defaultdict
from ast_nodes import *   # 若 AST 模块需要

# ─────────── 文法结构 ────────────
class Production:
    def __init__(self, lhs: str, rhs: list[str]):
        self.lhs, self.rhs = lhs, rhs
    def __repr__(self):
        return f"{self.lhs} → {' '.join(self.rhs) if self.rhs else 'ε'}"

class Grammar:
    def __init__(self):
        self.productions = []
        self.nonterminals, self.terminals = set(), set()
        self.start = ''
    def add_prod(self, lhs: str, rhs: list[str]):
        self.productions.append(Production(lhs, rhs))
        self.nonterminals.add(lhs)
    def compute_terminals(self):
        syms = {s for p in self.productions for s in p.rhs if s}
        self.terminals = syms - self.nonterminals
    def augment(self):
        ns = self.start + "'"
        self.productions.insert(0, Production(ns, [self.start]))
        self.nonterminals.add(ns)
        self.start = ns

# ─────────── 构建文法 ────────────
def build_grammar() -> Grammar:
    G = Grammar()
    G.start = 'Program'

    # 0.x
    G.add_prod('VariableInternal', ['mut', 'IDENT'])
    G.add_prod('VariableInternal', ['IDENT'])
    G.add_prod('Type', ['i32'])
    G.add_prod('Assignable', ['IDENT'])

    # 1.1
    G.add_prod('Program', ['DeclList'])
    G.add_prod('DeclList', [])
    G.add_prod('DeclList', ['Decl', 'DeclList'])
    G.add_prod('Decl', ['FnDecl'])
    G.add_prod('FnDecl', ['FnHead', 'Block'])
    G.add_prod('FnDecl', ['FnHead', 'FuncExprBlock'])
    G.add_prod('FnHead', ['fn', 'IDENT', '(', 'ParamList', ')'])
    G.add_prod('FnHead', ['fn', 'IDENT', '(', 'ParamList', ')', '->', 'Type'])
    G.add_prod('ParamList', [])
    G.add_prod('ParamList', ['Param'])
    G.add_prod('ParamList', ['Param', ',', 'ParamList'])
    G.add_prod('Param', ['VariableInternal', ':', 'Type'])

    # Block & StmtList
    G.add_prod('Block', ['{', '}'])
    G.add_prod('Block', ['{', 'Stmt', 'StmtList', '}'])
    G.add_prod('StmtList', [])  # ε
    G.add_prod('StmtList', ['Stmt'])  # 单条语句
    G.add_prod('StmtList', ['Stmt', 'StmtList'])  # 左递归

    # 基本 Stmt
    G.add_prod('Stmt', [';'])
    G.add_prod('Stmt', ['Expr', ';'])
    G.add_prod('Stmt', ['return', ';'])
    G.add_prod('Stmt', ['return', 'Expr', ';'])

    # 变量声明 / 赋值
    G.add_prod('Stmt', ['let', 'VariableInternal', ':', 'Type', ';'])
    G.add_prod('Stmt', ['let', 'VariableInternal', ';'])
    G.add_prod('Stmt', ['Assignable', '=', 'Expr', ';'])
    G.add_prod('Stmt', ['let', 'VariableInternal', ':', 'Type', '=', 'Expr', ';'])
    G.add_prod('Stmt', ['let', 'VariableInternal', '=', 'Expr', ';'])

    # 2.x 允许 Primary 做左值
    # G.add_prod('Assignable', ['Primary'])              # 保留单向
    G.add_prod('Primary', ['Assignable'])
    G.add_prod('Assignable', ['*', 'Primary'])

    # 3.x Expr
    G.add_prod('Expr', ['AddExpr'])
    for op in ['==','!=','<','<=','>','>=']:
        G.add_prod('Expr', ['Expr', op, 'Expr'])
    G.add_prod('AddExpr', ['AddExpr', '+', 'MulExpr'])
    G.add_prod('AddExpr', ['AddExpr', '-', 'MulExpr'])
    G.add_prod('AddExpr', ['MulExpr'])
    G.add_prod('MulExpr', ['MulExpr', '*', 'Primary'])
    G.add_prod('MulExpr', ['MulExpr', '/', 'Primary'])
    G.add_prod('MulExpr', ['Primary'])

    # Primary
    G.add_prod('Primary', ['IDENT'])
    G.add_prod('Primary', ['IDENT', '(', 'ArgList', ')'])
    G.add_prod('Primary', ['(', 'Expr', ')'])
    G.add_prod('Primary', ['NUMBER'])
    # ★ 修改：删除反向别名 Primary→Assignable
    G.add_prod('ArgList', [])
    G.add_prod('ArgList', ['Expr'])
    G.add_prod('ArgList', ['Expr', ',', 'ArgList'])

    # 4.1 if-else
    G.add_prod('Stmt', ['if', 'Expr', 'Block', 'ElsePart'])
    G.add_prod('ElsePart', [])
    G.add_prod('ElsePart', ['else', 'if', 'Expr', 'Block', 'ElsePart'])
    G.add_prod('ElsePart', ['else', 'Block'])

    # 5.x 循环 / 跳转（保留）
    G.add_prod('Stmt', ['while', 'Expr', 'Block'])
    G.add_prod('Stmt', ['for', 'VariableInternal', 'in', 'Expr', '..', 'Expr', 'Block'])
    G.add_prod('Stmt', ['loop', 'Block'])
    G.add_prod('Stmt', ['break', ';'])
    G.add_prod('Stmt', ['continue', ';'])

    # 6.2 借用 / 解引用
    G.add_prod('Primary', ['*', 'Primary'])
    G.add_prod('Primary', ['&', 'Primary'])
    G.add_prod('Primary', ['&', 'mut', 'Primary'])

    # ---------- 7.1 表达式块 ----------
    G.add_prod('FuncExprBlock', ['{', 'FuncStmtList', '}'])
    G.add_prod('FuncStmtList', ['Stmt', 'FuncStmtList'])  # 多语句 + 表达式
    G.add_prod('FuncStmtList', ['Stmt'])
    G.add_prod('FuncStmtList', ['Expr'])  # 仅表达式
    G.add_prod('Primary', ['FuncExprBlock'])

    # ---------- 7.3 选择表达式 ----------  ★ 新增
    G.add_prod('Expr', ['SelectExpr'])  # Expr → 选择表达式
    G.add_prod('SelectExpr',
               ['if', 'Expr', 'FuncExprBlock', 'else', 'FuncExprBlock'])

    # ---------- 7.4 循环表达式 ----------
    G.add_prod('Expr', ['LoopExpr'])  # Expr  → 循环表达式
    G.add_prod('LoopExpr', ['loop', 'FuncExprBlock'])  # LoopExpr → loop {...}

    # break 可携带表达式
    G.add_prod('Stmt', ['break', 'Expr', ';'])  # break Expr ;

    # 8.1 数组
    G.add_prod('Type', ['[', 'Type', ';', 'NUMBER', ']'])
    G.add_prod('Primary', ['[', 'ExprList', ']'])
    G.add_prod('ExprList', [])
    G.add_prod('ExprList', ['Expr'])
    G.add_prod('ExprList', ['Expr', ',', 'ExprList'])
    G.add_prod('Assignable', ['Primary', '[', 'Expr', ']'])

    # 9.1 元组
    G.add_prod('Type', ['(', ')'])
    G.add_prod('Type', ['(', 'TypeList', ')'])
    G.add_prod('TypeList', ['Type'])
    G.add_prod('TypeList', ['Type', ',', 'TypeList'])
    G.add_prod('Primary', ['(', ')'])  # 空元组 ()
    G.add_prod('Primary', ['(', 'Expr', ')'])  # 括号表达式
    G.add_prod('Primary', ['(', 'Expr', ',', ')'])  # 单元素元组 (1,)
    G.add_prod('Primary', ['(', 'Expr', ',', 'ExprList', ')'])  # 多元素元组 (1, 2, 3)

    # ExprList 维持不变，用于多元素
    G.add_prod('ExprList', ['Expr'])
    G.add_prod('ExprList', ['Expr', ',', 'ExprList'])
    G.add_prod('Assignable', ['Primary', '.', 'NUMBER'])

    # &T / &mut T
    G.add_prod('Type', ['&', 'Type'])
    G.add_prod('Type', ['&', 'mut', 'Type'])

    G.augment()
    G.compute_terminals()
    return G

# ─────────── FIRST / closure / goto (保持原实现) ────────────
class Item:
    def __init__(self, prod, dot, la):
        self.prod, self.dot, self.la = prod, dot, la
    def next_symbol(self):
        return self.prod.rhs[self.dot] if self.dot < len(self.prod.rhs) else None
    def __eq__(self, o): return (self.prod,self.dot,self.la)==(o.prod,o.dot,o.la)
    def __hash__(self): return hash((id(self.prod), self.dot, self.la))
    def __repr__(self):
        rhs=self.prod.rhs[:]; rhs.insert(self.dot,'·')
        return f"[{self.prod.lhs} → {' '.join(rhs) if rhs else 'ε'}, {self.la}]"

def compute_first_sets(G):
    first={nt:set() for nt in G.nonterminals}
    changed=True
    while changed:
        changed=False
        for p in G.productions:
            A, rhs = p.lhs, p.rhs
            if not rhs:
                if '' not in first[A]:
                    first[A].add(''); changed=True
                continue
            nullable=True
            for X in rhs:
                if X in first:
                    before=len(first[A])
                    first[A]|=(first[X]-{''})
                    if len(first[A])!=before: changed=True
                    if '' in first[X]: continue
                    nullable=False; break
                else:
                    if X not in first[A]:
                        first[A].add(X); changed=True
                    nullable=False; break
            if nullable and '' not in first[A]:
                first[A].add(''); changed=True
    return first

def first_seq(seq, first):
    out=set()
    for X in seq:
        if X in first:
            out|=(first[X]-{''})
            if '' in first[X]: continue
            return out
        else:
            out.add(X); return out
    out.add(''); return out

def closure(items, G, first):
    C=set(items)
    while True:
        new=set(C)
        for it in C:
            B=it.next_symbol()
            if B in G.nonterminals:
                beta=it.prod.rhs[it.dot+1:]
                for p in G.productions:
                    if p.lhs==B:
                        for la in first_seq(beta+[it.la], first):
                            new.add(Item(p,0,la))
        if new==C: break
        C=new
    return C

def goto(I,X,G,first):
    moved={Item(it.prod,it.dot+1,it.la) for it in I if it.next_symbol()==X}
    return closure(moved,G,first)

def build_lr1_states(G):
    first=compute_first_sets(G)
    I0=closure({Item(G.productions[0],0,'$')},G,first)
    C=[I0]; changed=True
    while changed:
        changed=False
        for I in list(C):
            for X in G.nonterminals|G.terminals:
                J=goto(I,X,G,first)
                if J and J not in C:
                    C.append(J); changed=True
    return C,first

# ─────────── ACTION / GOTO ────────────
def build_parse_table(C, G, first):
    ACTION, GOTO = defaultdict(dict), defaultdict(dict)
    for i,I in enumerate(C):
        for it in I:
            a = it.next_symbol()
            if a in G.terminals:
                j = C.index(goto(I,a,G,first))
                ACTION[i].setdefault(a, ('shift', j))            # ★ 修改 shift 优先
            if it.dot == len(it.prod.rhs) and it.prod.lhs != G.start:
                ACTION[i].setdefault(it.la, ('reduce', it.prod)) # ★ reduce 若无 shift
            if it.dot == len(it.prod.rhs) and it.prod.lhs == G.start:
                ACTION[i]['$'] = ('accept', None)
        for A in G.nonterminals:
            J = goto(I,A,G,first)
            if J:
                GOTO[i][A] = C.index(J)
    return ACTION, GOTO

# ———— 调试入口 (可选验证) ————
if __name__ == '__main__':
    # G = build_grammar()
    # states, first = build_lr1_states(G)
    # ACTION, GOTO  = build_parse_table(states, G, first)
    import pickle
    import os
    PARSE_TABLE_FILE = 'parse_tables.pkl'
    if os.path.exists(PARSE_TABLE_FILE):
        with open(PARSE_TABLE_FILE, 'rb') as f:
            G, ACTION, GOTO = pickle.load(f)
            # states=build_lr1_states(G)[0]
    else:
        G = build_grammar()
        C, first = build_lr1_states(G)
        ACTION, GOTO = build_parse_table(C, G, first)
        states = C
        with open(PARSE_TABLE_FILE, 'wb') as f:
            pickle.dump((G, ACTION, GOTO), f)

    # target = 82
    # print(f"\n=====  State {target}  =====")
    # for item in states[target]:
    #     print(" ", item)
    # print("\nACTION entries:")
    # for sym, act in ACTION[target].items():
    #     print(f"  {sym!r:10} -> {act}")
    print("所有以 Stmt → 开头的产生式：")
    for prod in G.productions:
        if prod.lhs == 'Stmt':
            print(prod)
