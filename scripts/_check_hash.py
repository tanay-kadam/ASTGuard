import sys
sys.path.insert(0, ".")
from astguard.data.preprocess import _preprocessing_hash
from astguard.alignment.tokenizer import CanonicalTokenizer

tok = CanonicalTokenizer("data/raw/checkpoints/codebert/3b0952feddeffad0063f274080e3c23d75e7eb39")
h = _preprocessing_hash(tok.identity_hash, 512, False, "leaf_path_radius4", False, "full_function", "clean", "a_priori_v1")
print("COMPUTED", h)
