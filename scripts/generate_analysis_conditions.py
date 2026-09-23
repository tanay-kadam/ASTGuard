from __future__ import annotations
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from astguard.utils.atomic_io import atomic_write_json


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',default='artifacts/analysis_conditions');args=parser.parse_args(argv)
    root=Path(args.output_dir);root.mkdir(parents=True,exist_ok=True)
    e7=[{'id':'original','type':'original'}]
    for operation in ('delete','swap'):
        for relation in ('ast','dfg','both'):
            for rate in (0.,.05,.10,.20,.40,1.):
                for seed in (1001,1002,1003,1004,1005):
                    if rate==0 and seed!=1001:continue
                    e7.append({'id':f'{operation}_{relation}_{rate:.2f}_{seed}','type':'corruption','operation':operation,
                               'relation':relation,'rate':rate,'seed':seed})
    a2=[{'id':'original','type':'original'},
        {'id':'training_mean','type':'gate','mode':'training_mean','training_means':'RUN_DIR/analysis/gates/training_means.json'},
        {'id':'function_mean','type':'gate','mode':'function_mean'},
        {'id':'zero_ast','type':'gate','mode':'zero_ast'},{'id':'zero_dfg','type':'gate','mode':'zero_dfg'}]
    a2 += [{'id':f'degree_bin_permutation_{seed}','type':'gate','mode':'degree_bin_permutation','seed':seed}
           for seed in (1001,1002,1003,1004,1005)]
    atomic_write_json(root/'E7.json',e7);atomic_write_json(root/'A2.json',a2)
    print(root);return 0

if __name__=='__main__':raise SystemExit(main())
