import importlib.util
from pathlib import Path
import pytest
from astguard.evaluation.bootstrap import ClusterBootstrap,holm_adjust
from astguard.evaluation.metrics import average_precision,official_vds_oracle
from astguard.protocol import verify_test_lock


def test_official_vds_parity():
    path=next(Path('third_party/sources/PrimeVul').glob('*/calc_vd_score.py'))
    spec=importlib.util.spec_from_file_location('official_vds',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    y=[0,1,0,1,0,1];p=[.1,.9,.4,.4,.7,.2]
    expected,_=module.calculate_vul_det_score(p,y)
    assert official_vds_oracle(y,p)['official_vds_oracle']==pytest.approx(expected)


def test_hierarchical_identical_models_are_zero():
    y=[0,1]*20;p=[.1,.8]*20;components=[str(i//2) for i in range(40)]
    predictions={seed:p for seed in [42,123,456,789,1024]}
    result=ClusterBootstrap().hierarchical(y,predictions,predictions,components,replicates=50)
    assert result['hierarchical_interval']==[0.,0.]
    assert result['seed_t_interval']==[0.,0.]
    assert not result['strong_positive']


def test_holm_and_locked_test():
    assert holm_adjust([.01,.04,.03])==pytest.approx([.03,.06,.06])
    with pytest.raises(RuntimeError):verify_test_lock()


def test_single_class_null():
    assert average_precision([1,1],[.2,.8]) is None
