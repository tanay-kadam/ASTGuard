"""Resume a SHA256-verified import using the user's existing SSH configuration."""
import argparse
import concurrent.futures
import hashlib
import json
import threading
import time
from pathlib import Path, PurePosixPath

import paramiko

# Serialize authentication to respect OpenSSH MaxStartups while parallelizing reads.
CONNECT_LOCK = threading.Lock()

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def connect(alias):
    config = paramiko.SSHConfig.from_path(str(Path.home() / '.ssh/config')).lookup(alias)
    c = paramiko.SSHClient()
    c.load_host_keys(str(Path.home() / '.ssh/known_hosts'))
    hostname = config.get('hostname', alias)
    hostalias = config.get('hostkeyalias', hostname)
    keys = c.get_host_keys().lookup(hostalias)
    if not keys: raise ValueError('No trusted SSH host key for configured alias')
    for kind, key in keys.items(): c.get_host_keys().add(hostname, kind, key)
    c.set_missing_host_key_policy(paramiko.RejectPolicy())
    with CONNECT_LOCK:
        c.connect(hostname, port=int(config.get('port', 22)), username=config.get('user'),
                  key_filename=[str(Path(p).expanduser()) for p in config.get('identityfile', [])],
                  allow_agent=False, look_for_keys=False, timeout=20, auth_timeout=20)
    c.get_transport().set_keepalive(20)
    return c

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host', default='seeklab')
    p.add_argument('--destination', type=Path, default=Path('artifacts/ssh_import_20261009'))
    p.add_argument('--inventory-remote', default='/tmp/astguard_corrected_artifact_inventory_20261009.json')
    p.add_argument('--workers', type=int, default=8)
    args = p.parse_args()
    out = args.destination.resolve(); out.mkdir(parents=True, exist_ok=True)
    manifest = out / 'inventory.json'
    if not manifest.exists():
        c = connect(args.host)
        try: c.open_sftp().get(args.inventory_remote, str(manifest))
        finally: c.close()
    inv = json.loads(manifest.read_text()); snapshot = out / 'snapshot'; snapshot.mkdir(exist_ok=True)
    state = {'verified': {}, 'failed': {}, 'requested_files': len(inv['files']), 'requested_bytes': inv['total_bytes']}
    lock = threading.Lock(); tls = threading.local(); clients = []
    def get(entry):
        rel = PurePosixPath(entry['path'])
        if rel.is_absolute() or '..' in rel.parts: raise ValueError('Unsafe inventory path')
        dest = snapshot.joinpath(*rel.parts)
        if not dest.resolve().is_relative_to(snapshot): raise ValueError('Escaping inventory path')
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            if dest.stat().st_size == entry['bytes'] and sha(dest) == entry['sha256']:
                with lock: state['verified'][str(rel)] = entry
                return
            raise FileExistsError('Refusing to overwrite different imported file: ' + str(rel))
        partial = dest.with_name(dest.name + '.download_partial')
        for attempt in range(3):
            try:
                if getattr(tls, 'client', None) is None:
                    tls.client = connect(args.host); tls.sftp = tls.client.open_sftp()
                    tls.sftp.get_channel().settimeout(60)
                    with lock: clients.append(tls.client)
                offset = partial.stat().st_size if partial.exists() else 0
                if offset > entry['bytes']: raise ValueError('Oversized partial')
                with tls.sftp.open(inv['source_root'] + '/' + str(rel), 'rb') as source, partial.open('ab') as target:
                    source.seek(offset)
                    source.prefetch(entry['bytes'], max_concurrent_requests=64)
                    while offset < entry['bytes']:
                        b = source.read(min(1024 * 1024, entry['bytes'] - offset))
                        if not b: raise EOFError(str(rel))
                        target.write(b); offset += len(b)
                if sha(partial) != entry['sha256']: raise ValueError('SHA256 mismatch: ' + str(rel))
                partial.replace(dest)
                with lock: state['verified'][str(rel)] = entry
                return
            except Exception as exc:
                if getattr(tls, 'client', None): tls.client.close(); tls.client = None
                if attempt == 2:
                    with lock: state['failed'][str(rel)] = str(exc)
                else:
                    time.sleep(2*(attempt+1))
    entries = sorted(inv['files'], key=lambda e: (e['bytes'] > 100_000_000, e['bytes']))
    started = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(get, e) for e in entries}
        while pending:
            done, pending = concurrent.futures.wait(pending, timeout=10, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                try: future.result()
                except Exception as exc:
                    with lock: state['failed']['worker_error_'+str(id(future))] = str(exc)
            with lock:
                view = dict(state); view['verified'] = dict(state['verified']); view['failed'] = dict(state['failed'])
            verified_bytes = sum(e['bytes'] for e in view['verified'].values())
            view.update(verified_bytes=verified_bytes, elapsed_seconds=time.time() - started, complete=not pending and not view['failed'])
            temp = out / 'transfer_state.json.partial'; temp.write_text(json.dumps(view, indent=2)); temp.replace(out/'transfer_state.json')
            if not pending or time.time() - getattr(main, 'last_report', 0) > 15:
                print(json.dumps({k: view[k] for k in ['requested_files', 'requested_bytes', 'verified_bytes', 'elapsed_seconds', 'complete']} | {'verified_files':len(view['verified']), 'failed_files':len(view['failed'])}), flush=True)
                main.last_report = time.time()
    for c in clients: c.close()
    if state['failed']: raise RuntimeError('Transfer incomplete; inspect transfer_state.json and rerun to resume')

if __name__ == '__main__': main()
