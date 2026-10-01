from astguard.config import load_config

c1 = load_config("configs/structure_usage/ast_dfg_fixed_stage0fullprobe.yaml")
c2 = load_config("configs/structure_usage/astguard_stage0fullprobe.yaml")
print("OK", c1.training.max_optimizer_steps, c2.training.max_optimizer_steps)
