#!/usr/bin/env python3
# generate_parse_tables.py

import pickle
from grammar import build_grammar, build_lr1_states, build_parse_table

def main():
    # 1) 构建文法和 LR(1) 状态机
    G = build_grammar()
    C, first = build_lr1_states(G)
    ACTION, GOTO = build_parse_table(C, G, first)

    # 2) 保存到磁盘
    with open('parse_tables.pkl', 'wb') as f:
        # 我们把 Grammar 实例、ACTION、GOTO 一起存
        pickle.dump((G, ACTION, GOTO), f)

    print(f"Generated parse_tables.pkl: {len(C)} states, ACTION/GOTO saved.")

if __name__ == '__main__':
    main()
