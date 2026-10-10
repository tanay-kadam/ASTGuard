"""Check whether model construction changes the configured CUDA RNG seed."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import torch
from astguard.config import load_config
from astguard.models.factory import create_model
from astguard.training.seeds import set_seed
from astguard.utils.atomic_io import atomic_write_json

def main():
    output=Path(sys.argv[1]);config=load_config('configs/structure_usage/astguard_strong_stage0fullprobe.yaml')
    assert torch.cuda.is_available()
    torch.cuda.init();set_seed(42);before=int(torch.cuda.initial_seed())
    model=create_model(config);after=int(torch.cuda.initial_seed())
    report={'variant':config.model.variant,'requested_seed':42,'cuda_seed_before_construction':before,
            'cuda_seed_after_construction':after,'constructor_preserves_cuda_seed':before==after,
            'model_constructed_on':'cpu','visible_cuda_device':torch.cuda.get_device_name(0)}
    atomic_write_json(output,report);print(json.dumps(report,indent=2))

if __name__=='__main__':main()
