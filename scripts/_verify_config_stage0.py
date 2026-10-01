from astguard.config import load_config

c = load_config("configs/structure_usage/astguard.yaml")
print("CONFIG_OK", c.model.structural_layers, c.dataset.manifest_hash[:12], c.preprocessing.cache_hash[:12])
