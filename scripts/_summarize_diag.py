import json

for name in ["stage0_ast_dfg_fixed_trained", "stage0_astguard_trained"]:
    d = json.load(open("artifacts/audits/diagnostics/" + name + ".json"))
    print("===", name, "===")
    print("variant:", d.get("variant"))
    print("mean_abs_logit_delta_vs_empty:", d.get("mean_abs_logit_delta_vs_empty"))
    gvs = d.get("gate_value_summary", {})
    for layer, stats in gvs.items():
        print("  gate layer", layer, stats)
    grs = d.get("gradient_reach")
    if grs:
        print("gradient_reach keys:", list(grs.keys())[:10])
    print()
