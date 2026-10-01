import json
import statistics as st

for name in ["stage0_ast_dfg_fixed_trained", "stage0_astguard_trained"]:
    d = json.load(open("artifacts/audits/diagnostics/" + name + ".json"))
    print("===", name, "variant:", d["variant"], "===")
    print("n_examples:", d["n_examples"], "n_positive:", d["n_positive"], "n_batches:", d["n_batches"])

    eg = d["empty_graph_sensitivity"]
    print("empty_graph_sensitivity[0] sample:", eg[0] if eg else None)
    # try to pull a scalar summary out of each batch entry
    if eg and isinstance(eg[0], dict):
        keys = list(eg[0].keys())
        print("  keys:", keys)
        for k in keys:
            vals = [b[k] for b in eg if isinstance(b.get(k), (int, float))]
            if vals:
                print(f"  {k}: mean={st.mean(vals):.6g} max={max(vals):.6g} min={min(vals):.6g}")

    gr = d["gradient_reach"]
    print("gradient_reach[0] sample:", gr[0] if gr else None)

    gv = d["gate_values"]
    print("gate_values[0] sample:", gv[0] if gv else None)
    print()
