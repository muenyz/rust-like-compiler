# grammar.py

from collections import defaultdict
from ast import *    # 引入 AST 节点定义

class Production:
    def __init__(self, lhs: str, rhs: list[str]):
        self.lhs = lhs
        self.rhs = rhs
    def __repr__(self):
        return f"{self.lhs} → {' '.join(self.rhs)}"

class Grammar:
    def __init__(self):
        self.productions = []
        self.nonterminals = set()
        self.terminals = set()
        self.start = ''

    def add_prod(self, lhs: str, rhs: list[str]):
        self.productions.append(Production(lhs, rhs))
        self.nonterminals.add(lhs)
        for sym in rhs:
            # 约定：大写开头为非终结符，否则为终结符
            if sym and sym[0].isupper():
                self.nonterminals.add(sym)
            else:
                self.terminals.add(sym)

    def augment(self):
        # 增强文法：在最前插入 S' → start
        new_start = self.start + "'"
        self.productions.insert(0, Production(new_start, [self.start]))
        self.nonterminals.add(new_start)
        self.start = new_start

def compute_first_sets(G: Grammar) -> dict[str, set[str]]:
    # 初始化：对每个非终结符，FIRST(NT) = ∅
    first = { nt: set() for nt in G.nonterminals }

    changed = True
    while changed:
        changed = False
        # 遍历每条产生式 A → X1 X2 … Xn
        for p in G.productions:
            A, rhs = p.lhs, p.rhs
            # 若是空产生式 A → ε
            if not rhs:
                if '' not in first[A]:
                    first[A].add('')
                    changed = True
                continue

            # 否则按 X1, X2, ... 顺序处理
            nullable_prefix = True
            for X in rhs:
                # 如果 X 是非终结符
                if X in first:
                    # FIRST(A) 包含 FIRST(X) 除 ε 外的全部符号
                    before = len(first[A])
                    first[A] |= (first[X] - {''})
                    if len(first[A]) > before:
                        changed = True
                    # 如果 X 的 FIRST 中不含 ε，就停止
                    if '' not in first[X]:
                        nullable_prefix = False
                        break
                else:
                    # X 是终结符
                    if X not in first[A]:
                        first[A].add(X)
                        changed = True
                    nullable_prefix = False
                    break

            # 如果所有 X 都能推出 ε，则 ε ∈ FIRST(A)
            if nullable_prefix and '' not in first[A]:
                first[A].add('')
                changed = True

    return first

def first_of_sequence(seq: list[str], first: dict[str, set[str]]) -> set[str]:
    """
    计算串 X1 X2 … Xk 的 FIRST:
    从左往右，把每个 Xi 的 FIRST(Xi)-{ε} 加进来；
    如果 Xi 能出 ε，就继续看下一个；否则停止。
    如果所有 Xi 都能出 ε，则最后加入 ε。
    """
    result = set()
    for X in seq:
        if X in first:
            result |= (first[X] - {''})
            if '' in first[X]:
                continue
            else:
                return result
        else:
            # X 是终结符
            result.add(X)
            return result
    result.add('')
    return result

def build_grammar() -> Grammar:
    G = Grammar()
    G.start = 'Program'

    # TODO: 在这里添加所有“类Rust”文法产生式，用 G.add_prod(lhs, rhs)
    # 示例：
    G.add_prod('Program', ['StmtList'])
    G.add_prod('StmtList', [])
    G.add_prod('StmtList', ['Stmt', 'StmtList'])

    # 变量声明语句
    # let_decl -> 'let' 'mut'? IDENT (':' IDENT)? ('=' Expr)? ';'
    G.add_prod('Stmt', ['let', 'IDENT', ';'])     # 简化示例
    # 表达式语句
    G.add_prod('Stmt', ['Expr', ';'])

    # 表达式产生式
    G.add_prod('Expr', ['Expr', '+', 'Term'])
    G.add_prod('Expr', ['Term'])
    G.add_prod('Term', ['Term', '*', 'Factor'])
    G.add_prod('Term', ['Factor'])
    G.add_prod('Factor', ['(', 'Expr', ')'])
    G.add_prod('Factor', ['NUMBER'])
    G.add_prod('Factor', ['IDENT'])

    # … 继续添加 if/else/while/for/loop/return/比较/函数调用/数组/元组等规则 …

    # 增强文法
    G.augment()
    return G

# 测试：打印所有产生式
if __name__ == '__main__':
    G = build_grammar()
    for p in G.productions:
        print(p)
    first = compute_first_sets(G)
    print("FIRST sets:")
    for nt in sorted(G.nonterminals):
        print(f"  FIRST({nt}) = {first[nt]}")
