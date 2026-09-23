from __future__ import annotations

import argparse,subprocess,sys
from pathlib import Path


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--install",action="store_true"); p.add_argument("--output",default="requirements.lock"); args=p.parse_args(argv)
    if sys.version_info[:2] != (3,11): raise RuntimeError("run this resolver with Python 3.11")
    if args.install: subprocess.run([sys.executable,"-m","pip","install","-e",".[research,test]"],check=True)
    subprocess.run([sys.executable,"-m","pytest","-p","no:cacheprovider"],check=True)
    import importlib.metadata
    frozen='\n'.join(sorted(f"{dist.metadata['Name']}=={dist.version}" for dist in importlib.metadata.distributions() if dist.metadata['Name'].lower()!='astguard'))+'\n'
    Path(args.output).write_text(frozen,encoding="utf-8",newline="\n")
    print(f"wrote tested lock to {args.output}"); return 0


if __name__ == "__main__": raise SystemExit(main())
