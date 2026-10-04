from pathlib import Path
import subprocess

from astguard.utils.provenance import source_identity


def test_source_identity_hashes_untracked_files(tmp_path):
    subprocess.run(['git','init'],cwd=tmp_path,check=True,capture_output=True)
    subprocess.run(['git','config','user.email','test@example.com'],cwd=tmp_path,check=True)
    subprocess.run(['git','config','user.name','Test'],cwd=tmp_path,check=True)
    (tmp_path/'tracked.py').write_text('x=1\n',encoding='utf-8')
    subprocess.run(['git','add','tracked.py'],cwd=tmp_path,check=True)
    subprocess.run(['git','commit','-m','initial'],cwd=tmp_path,check=True,capture_output=True)
    (tmp_path/'new.py').write_text('value=1\n',encoding='utf-8')
    first=source_identity(tmp_path)
    (tmp_path/'new.py').write_text('value=2\n',encoding='utf-8')
    second=source_identity(tmp_path)
    assert first['untracked_file_count']==1
    assert first['untracked_files_hash']!=second['untracked_files_hash']
