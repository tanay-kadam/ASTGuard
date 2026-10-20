"""Delete only the named remote scratch campaign after verified backup and push."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from archive_completed_campaign_20261020 import DEST,REMOTE,connect

def main():
    state=json.loads((DEST/'transfer_state.json').read_text())
    inventory=json.loads((DEST/'inventory.json').read_text())
    pushed=json.loads((DEST/'github_push.json').read_text())
    assert json.loads((DEST/'shared_inputs_verification.json').read_text())['status']=='passed'
    assert pushed['status']=='pushed' and pushed['commit'].startswith('b60dbf7')
    assert state.get('status')=='passed' and not state['errors']
    assert len(state['verified'])==len(inventory['files'])==3185
    assert inventory['root']==REMOTE and inventory['selected_checkpoints']==66 and not inventory['symlinks']
    assert sum(r['relative'].startswith('original_regvd/') and r['relative'].endswith('/best.safetensors') for r in inventory['files'])==9
    # Every local path must still exist at its verified size. Transfer verified SHA256
    # on each completed file before committing its final name.
    for r in inventory['files']:
        p=DEST/r['relative'];assert p.resolve().is_relative_to(DEST.resolve())
        assert p.is_file() and p.stat().st_size==r['bytes'] and state['verified'][r['relative']]==r['bytes']
    payload=r'''
import hashlib,json,os,shutil,time
from pathlib import Path
root=Path('/tmp/astguard_seven_day_20261012')
assert str(root)=='/tmp/astguard_seven_day_20261012' and root.resolve()==root and root.is_dir() and not root.is_symlink()
manifest=json.loads(Path('/tmp/astguard_campaign_archive_inventory_20261020.json').read_text())
assert manifest['root']==str(root) and manifest['selected_checkpoints']==66
known={r['source'] for r in manifest['files']}|{str(root/r['path']) for r in manifest['omitted']}
for parent,dirs,files in os.walk(root,followlinks=False):
    dirs[:]=[d for d in dirs if d not in {'.git','.venv','__pycache__','.pytest_cache'}]
    for name in dirs:
        p=Path(parent)/name
        if p.is_symlink():
            assert p==root/'data/strengthening_20261006' and p.resolve()==Path('/home/tkadam/ASTGuard/data/strengthening_20261006')
    for name in files:
        p=Path(parent)/name
        assert str(p) in known,'Unexpected file since inventory: '+str(p)
# Rehash required server files immediately before removing the isolated root.
for r in manifest['files']:
    p=Path(r['source']);assert p.is_file() and p.stat().st_size==r['bytes']
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    assert h.hexdigest()==r['sha256'],str(p)
for entry in Path('/proc').iterdir():
    if not entry.name.isdigit():continue
    try:
        if entry.stat().st_uid!=os.getuid():continue
        cmd=(entry/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
    except (FileNotFoundError,PermissionError,ProcessLookupError):continue
    if int(entry.name)!=os.getpid():
        assert not any(s in cmd for s in ['scripts/seven_day_campaign.py','scripts/seven_day_finalize.py','scripts/seven_day_evaluate_external.py','scripts/seven_day_holdout.py']),cmd
before=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
shutil.rmtree(root)
assert not root.exists()
result={'status':'deleted','target':str(root),'logical_bytes_removed':before,'required_files_rehashed':len(manifest['files']),'original_project_preserved':Path('/home/tkadam/ASTGuard').is_dir(),'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
assert result['original_project_preserved']
Path('/tmp/astguard_campaign_retirement_20261020.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
'''
    c=connect();stdin,stdout,stderr=c.exec_command('python3 -',timeout=1800)
    stdin.write(payload);stdin.channel.shutdown_write()
    text=stdout.read().decode();err=stderr.read().decode();code=stdout.channel.recv_exit_status()
    assert code==0,(text,err)
    report=json.loads(text);(DEST/'retirement.json').write_text(json.dumps(report,indent=2)+'\n')
    c.close();print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
