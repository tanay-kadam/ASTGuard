import pytest

from scripts import queue_strengthening_all_gpus as queue


def test_big_runs_have_separate_pool():
    assert queue.pool_for({'family': 'real', 'condition': 'attention_authentic'}) == 'attention'
    assert queue.pool_for({'family': 'real', 'condition': 'adapter_centered'}) == 'adapter'
    assert set(queue.BLOCKERS) == {5, 6}
    with pytest.raises(ValueError):
        queue.pool_for({'family': 'synthetic', 'condition': 'attention_authentic'})


def test_claim_is_atomic_and_not_reused(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, 'PLAN', tmp_path)
    job = {'tag': 'real_adapter_centered_s42'}
    assert queue.claim(job, 2)
    assert not queue.claim(job, 3)


def test_available_excludes_claims_and_running(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, 'PLAN', tmp_path)
    monkeypatch.setattr(queue, 'status', lambda tag: 'running' if tag == 'active' else 'not_started')
    jobs = [{'tag': 'active'}, {'tag': 'claimed'}, {'tag': 'pending'}]
    assert queue.claim(jobs[1], 2)
    assert queue.available(jobs) == [jobs[2]]
