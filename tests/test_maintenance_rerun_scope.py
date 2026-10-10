import json

import pytest

from scripts import queue_strengthening as queue


@pytest.fixture
def held_campaign(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, 'ROOT', tmp_path)
    (tmp_path/'maintenance_hold.json').write_text('{}')
    (tmp_path/'fresh_rerun_authorization.json').write_text(json.dumps({
        'fresh_only': True, 'tags': ['real_attention_sequence_s456']}))
    return tmp_path


def test_general_queue_stays_held(held_campaign):
    with pytest.raises(RuntimeError, match='maintenance hold'):
        queue.run_job({'tag': 'real_attention_sequence_s456'}, 6)


def test_override_cannot_launch_unlisted_job(held_campaign):
    with pytest.raises(RuntimeError, match='maintenance hold'):
        queue.run_job({'tag': 'real_attention_shuffled_s123'}, 6,
                      maintenance_rerun_tag='real_attention_sequence_s456')


def test_scoped_override_accepts_only_selected_tag(held_campaign):
    target = held_campaign/'jobs'/'real_attention_sequence_s456'
    target.mkdir(parents=True)
    (target/'status.json').write_text('{"status": "complete"}')
    # A completed job returns before calling any training or GPU command.
    queue.run_job({'tag': 'real_attention_sequence_s456'}, 6,
                  maintenance_rerun_tag='real_attention_sequence_s456')
    assert (held_campaign/'maintenance_hold.json').is_file()
