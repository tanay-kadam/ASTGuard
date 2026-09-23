from __future__ import annotations


def active_relations(variant: str) -> tuple[str, ...]:
    allowed = {'sequence_only', 'ast_fixed', 'dfg_fixed', 'ast_dfg_fixed', 'astguard', 'query_gated_astguard', 'edge_gated_astguard', 'query_capacity_matched', 'astguard_dropout', 'astguard_ast_only', 'astguard_dfg_only', 'linear_relation', 'function_gate', 'fixed_adapter'}
    if variant not in allowed:
        raise ValueError(f'{variant} requires its own verified baseline adapter')
    if variant in {"sequence_only"}:
        return ()
    if variant in {"ast_fixed", "astguard_ast_only"}:
        return ("ast",)
    if variant in {"dfg_fixed", "astguard_dfg_only"}:
        return ("dfg",)
    return ("ast", "dfg")


def attention_mode(variant: str) -> str:
    if variant in {'edge_gated_astguard', 'query_capacity_matched'}:
        return 'edge'
    if variant == "sequence_only":
        return "sequence"
    if variant.endswith("_fixed") or variant == "fixed_adapter":
        return "fixed"
    if variant == 'linear_relation':
        return 'linear'
    if variant == 'function_gate':
        return 'function'
    return "adaptive"
