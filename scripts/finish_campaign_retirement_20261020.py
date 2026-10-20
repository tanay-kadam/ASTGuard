"""Wait for verified preservation, then retire the exact scratch root and push receipt."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

from archive_completed_campaign_20261020 import DEST,REPO

def git(*args):
    return subprocess.check_output(['git',*args],cwd=REPO,text=True,stderr=subprocess.STDOUT).strip()

def main():
    status=DEST/'completion.json'
    def record(state,**extra):
        status.write_text(json.dumps({'status':state,'updated_unix':time.time(),**extra},indent=2)+'\n')
        print(state,extra,flush=True)
    record('waiting_for_verified_backup')
    end=time.time()+8*3600
    while time.time()<end:
        try:
            transfer=json.loads((DEST/'transfer_state.json').read_text())
            shared=json.loads((DEST/'shared_inputs_verification.json').read_text())
        except (FileNotFoundError,json.JSONDecodeError):time.sleep(15);continue
        if transfer.get('errors'):raise RuntimeError(transfer['errors'])
        if transfer.get('status')=='passed' and shared.get('status')=='passed':break
        time.sleep(15)
    else:raise TimeoutError('Backup incomplete; remote deletion was not attempted.')
    assert git('branch','--show-current')=='stage0-length-matched-shuffle'
    assert git('remote','get-url','origin')=='https://github.com/tanay-kadam/ASTGuard.git'
    assert git('merge-base','--is-ancestor','b60dbf7','HEAD')==''
    # Recheck every local backup SHA256 once more before destructive cleanup.
    record('rechecking_local_backup')
    inventory=json.loads((DEST/'inventory.json').read_text())
    for r in inventory['files']:
        p=DEST/r['relative'];assert p.resolve().is_relative_to(DEST.resolve())
        with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        assert digest==r['sha256'],r['relative']
    record('verified_backup_deleting_named_remote_campaign')
    subprocess.run([sys.executable,str(REPO/'scripts/retire_verified_campaign_20261020.py')],cwd=REPO,check=True)
    retirement=json.loads((DEST/'retirement.json').read_text())
    assert retirement['status']=='deleted' and retirement['original_project_preserved']
    public={k:v for k,v in retirement.items() if k!='target'}
    public.update({'backup_files':len(inventory['files']),'backup_bytes':inventory['bytes'],
        'selected_campaign_checkpoints':66,'reused_regvd_checkpoints':9,'shared_real_input_files':4,
        'portable_evidence_commit':'b60dbf7','backup_location':'archive/ssh_campaign_20261020 (ignored; author-local)',
        'omissions':'Unselected optimizer/last/smoke checkpoints, caches and duplicate exports; see private inventory.',
        'scope':'Only the isolated seven-day campaign was removed; the original remote project remains.'})
    report=REPO/'docs/CAMPAIGN_PRESERVATION_20261020.json'
    report.write_text(json.dumps(public,indent=2)+'\n')
    git('add',str(report.relative_to(REPO)))
    git('commit','--only','-m','Record verified campaign preservation and scratch cleanup','--',str(report.relative_to(REPO)))
    git('push','origin','HEAD')
    record('complete',git_commit=git('rev-parse','HEAD'),backup_files=len(inventory['files']),
        backup_bytes=inventory['bytes'],remote_campaign_deleted=True,original_remote_project_preserved=True)

if __name__=='__main__':
    try:main()
    except Exception:
        DEST.mkdir(exist_ok=True,parents=True)
        (DEST/'completion_failure.txt').write_text(traceback.format_exc())
        print(traceback.format_exc(),flush=True)
        raise
