"""Fresh, scoped replacements for the two user-selected maintenance attempts.

The general maintenance hold is intentionally retained. No resume flag is used.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from astguard.utils.atomic_io import atomic_write_json
from scripts.queue_strengthening import ROOT, run_job, stamp

TAGS = ('real_attention_sequence_s456', 'real_attention_authentic_s42')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', choices=TAGS, required=True)
    parser.add_argument('--gpu', type=int, choices=(5, 6), required=True)
    args = parser.parse_args()
    authorization = json.loads((ROOT/'fresh_rerun_authorization.json').read_text())
    assert authorization['fresh_only'] is True and args.tag in authorization['tags']
    jobs = json.loads((ROOT/'jobs.json').read_text())['jobs']
    job = next(item for item in jobs if item['tag'] == args.tag)
    config_path = Path(job['config'])
    config = json.loads(config_path.read_text())
    assert config['training']['epochs'] == 5
    assert config['training']['seed'] == job['seed']
    assert config['training']['max_optimizer_steps'] is None
    for filename in ('real/train.jsonl', 'real/tune.jsonl', 'real/manifest.json',
                     'smoke/train.jsonl', 'smoke/tune.jsonl'):
        assert (Path('data/strengthening_20261006')/filename).is_file(), filename
    target = ROOT/'jobs'/args.tag
    old_state = json.loads((target/'status.json').read_text())
    assert old_state['status'] == 'interrupted', old_state
    # Complete a new smoke test with the same model/seed/effective batch before
    # moving any original run. Its distinct tag cannot reuse an older smoke gate.
    preflight_tag = args.tag+'_fresh_preflight'
    assert not (ROOT/'jobs'/(preflight_tag+'_smoke')).exists(), 'preflight already exists; inspect before retry'
    preflight_base = ROOT/'fresh_reruns'/f'{args.tag}.yaml'
    config['training'].update(epochs=1, min_epochs=1, patience=1, max_optimizer_steps=2)
    atomic_write_json(str(preflight_base).replace('.yaml', '_smoke.yaml'), config)
    smoke_job = dict(job, tag=preflight_tag, config=str(preflight_base))
    run_job(smoke_job, args.gpu, smoke=True, maintenance_rerun_tag=args.tag)
    # Resolve both targets under this campaign and refuse to overwrite anything.
    archive = ROOT/'maintenance_interrupted_20261007'/'jobs'/args.tag
    root = ROOT.resolve()
    assert target.resolve().is_relative_to(root)
    assert archive.resolve().is_relative_to(root)
    assert not archive.exists(), 'archive already exists; manual inspection required'
    archive.parent.mkdir(parents=True, exist_ok=True)
    target.rename(archive)
    record_path = ROOT/'fresh_reruns'/f'{args.tag}_record.json'
    record = dict(tag=args.tag, gpu=args.gpu, status='starting', utc=stamp(),
                  restart_mode='fresh_from_epoch_1', resume_checkpoint=None,
                  original_attempt=str(archive), original_status=old_state,
                  config=str(config_path), config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),
                  preflight=str(ROOT/'jobs'/(preflight_tag+'_smoke')))
    atomic_write_json(record_path, record)
    try:
        run_job(job, args.gpu, maintenance_rerun_tag=args.tag)
        record.update(status='complete', completed_utc=stamp())
    except Exception as exc:
        record.update(status='failed', error=str(exc), completed_utc=stamp())
        raise
    finally:
        atomic_write_json(record_path, record)


if __name__ == '__main__':
    main()
