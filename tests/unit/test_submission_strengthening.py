import importlib.util
from pathlib import Path

import numpy as np
import pytest
import torch

from astguard.baselines.regvd import ReGCN
from astguard.baselines.regvd_audit import native_graph,permute_edges,NativeGraphCollator
from scripts.prepare_strengthening_inputs import corrected_manifest


def test_outlier_filter_keeps_all_manifest_columns_aligned():
    m={'ordered_sample_ids':['a','b','c'],'roles':['train','tune','test'],'component_ids':['A','B','C'],
       'original_splits':['train','valid','test'],'counts':{},'exclusion_reasons':{},'file_hash':'parent','rule_hash':'r'}
    result=corrected_manifest(m,{'a'})
    assert list(zip(result['ordered_sample_ids'],result['roles'],result['component_ids'],result['original_splits'])) == [('b','tune','B','valid'),('c','test','C','test')]
    broken=m|{'roles':['train','tune']}
    with pytest.raises(ValueError):corrected_manifest(broken,{'a'})


def test_native_regvd_graph_matches_upstream_including_padding():
    path=next(Path('third_party/sources/ReGVD').glob('*/code/modelGNN_updates.py'))
    spec=importlib.util.spec_from_file_location('regvd_pinned',path)
    upstream=importlib.util.module_from_spec(spec);spec.loader.exec_module(upstream)
    ids=[0,7,8,9,7,2,1,1,1,1]
    embedding=np.zeros((20,4));embedding[:,0]=np.arange(20)
    graphs,features=upstream.build_graph(np.array([ids]),embedding,window_size=5)
    order=[int(r[0]) for r in features[0]]
    nodes,edges=native_graph(ids)
    actual=np.zeros((len(order),len(order)))
    positions={n:i for i,n in enumerate(order)}
    for a,b in edges:actual[positions[nodes[a]],positions[nodes[b]]]=1
    np.testing.assert_array_equal(actual,graphs[0].toarray())
    assert 1 in nodes
    adj=graphs[0].toarray();degree=adj.sum(1);inverse=np.where(degree>0,1/np.sqrt(np.maximum(degree,1)),0)
    expected=adj*inverse[:,None]*inverse[None,:]
    batch=NativeGraphCollator()([{'input_ids':ids,'sample_id':'s','label':0}])
    reorder=[nodes.index(n) for n in order]
    np.testing.assert_allclose(batch['adjacency'][0].numpy()[np.ix_(reorder,reorder)],expected)


def test_regcn_forward_matches_pinned_upstream():
    path=next(Path('third_party/sources/ReGVD').glob('*/code/modelGNN_updates.py'))
    spec=importlib.util.spec_from_file_location('regvd_forward_pinned',path)
    upstream=importlib.util.module_from_spec(spec);spec.loader.exec_module(upstream)
    original=upstream.ReGCN(12,8,2,0.).eval()
    local=ReGCN(12,8,2,0.).double().eval()
    for a,b in zip(local.layers,original.gnnlayers):a.weight.data.copy_(b.weight.data)
    local.soft_attention.load_state_dict(original.soft_att.state_dict());local.transform.load_state_dict(original.ln.state_dict())
    values=torch.randn(2,5,12,dtype=torch.float64);adj=torch.randn(2,5,5,dtype=torch.float64).abs();mask=torch.ones(2,5,1,dtype=torch.float64)
    torch.testing.assert_close(local(values,adj,mask),original(values,adj,mask),rtol=1e-10,atol=1e-10)


def test_native_null_preserves_per_node_degree():
    nodes,edges=native_graph([0,2,3,4,5,6,7,8,9,10,11,12])
    new,change=permute_edges(nodes,[list(e) for e in edges],42,'s')
    assert len(new)==len(edges) and 0<=change<=1
    assert {tuple(reversed(e)) for e in new}==set(new)
