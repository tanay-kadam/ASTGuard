"""Send worker and ephemeral GitHub authentication over SSH; no large local files."""
import json
from pathlib import Path
import subprocess
import sys

from archive_completed_campaign_20261020 import connect,REPO

def main():
    token=subprocess.check_output([r'C:\Program Files\GitHub CLI\gh.exe','auth','token'],text=True).strip()
    assert token
    c=connect();s=c.open_sftp()
    remote='/tmp/astguard_cloud_archive_worker_20261020.py'
    s.put(str(REPO/'scripts/cloud_archive_worker_20261020.py'),remote);s.chmod(remote,0o700);s.close()
    stdin,stdout,stderr=c.exec_command('python3 '+remote,timeout=90)
    stdin.write(json.dumps({'token':token,'detach':True}));stdin.channel.shutdown_write();token=None
    result=stdout.read().decode();err=stderr.read().decode();code=stdout.channel.recv_exit_status()
    assert code==0,err
    data=json.loads(result);assert data['status']=='started'
    p=REPO/'artifacts/audits/ssh_storage_change_20261020/cloud_launch.json'
    p.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data),flush=True);c.close()

if __name__=='__main__':main()
