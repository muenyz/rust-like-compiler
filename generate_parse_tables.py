# generate_parse_tables.py

import pickle
import json
from grammar import build_grammar, build_lr1_states, build_parse_table

def main():
    # 1) 构建文法和 LR(1) 状态机
    G = build_grammar()
    C, first = build_lr1_states(G)
    ACTION, GOTO = build_parse_table(C, G, first)

    # 2) 保存为 pickle（二进制，用于 parser 加载）
    with open('parse_tables.pkl', 'wb') as f:
        pickle.dump((G, ACTION, GOTO), f)
    print(f"Saved parse_tables.pkl ({len(C)} states)")

    # 3) 保存为 JSON（文本，可人类阅读）
    def format_action(act):
        if isinstance(act, tuple):
            cmd, val = act
            return f"{cmd.upper()} {val}"
        return str(act)

    action_json = {
        str(state): {str(tok): format_action(act) for tok, act in row.items()}
        for state, row in ACTION.items()
    }

    goto_json = {
        str(state): {str(nonterm): target for nonterm, target in row.items()}
        for state, row in GOTO.items()
    }

    with open('parse_tables_debug.json', 'w', encoding='utf-8') as f:
        json.dump({
            "ACTION": action_json,
            "GOTO": goto_json
        }, f, indent=2)

    print("Saved parse_tables_debug.json (human-readable ACTION/GOTO)")

if __name__ == '__main__':
    main()