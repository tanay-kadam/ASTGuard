import json

for name in ["stage0_ast_dfg_fixed_trained", "stage0_astguard_trained"]:
    d = json.load(open("artifacts/audits/diagnostics/" + name + ".json"))
    print("===", name, "===")
    print("top-level keys:", list(d.keys()))
    for k, v in d.items():
        if isinstance(v, (dict, list)):
            print(f"  {k}: type={type(v).__name__} len={len(v)}")
        else:
            print(f"  {k}: {v}")
    print()
