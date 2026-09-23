import importlib.util
from pathlib import Path
import torch
from transformers import RobertaConfig,RobertaModel
from astguard.baselines.linevul import LineVulFunction
from astguard.baselines.graphcodebert import GraphCodeBERTClassifier,GraphCollator
from astguard.baselines.regvd import ReGVDClassifier,build_token_graph_batch


def backbone():
    config=RobertaConfig(vocab_size=40,hidden_size=16,num_attention_heads=2,num_hidden_layers=1,intermediate_size=32,
                         hidden_dropout_prob=0.,attention_probs_dropout_prob=0.,max_position_embeddings=40)
    config._attn_implementation='eager'
    return RobertaModel(config,add_pooling_layer=False)


def test_linevul_official_head_parity():
    path=next(Path('third_party/sources/LineVul').glob('*/linevul/linevul_model.py'))
    spec=importlib.util.spec_from_file_location('linevul_official',path)
    upstream=importlib.util.module_from_spec(spec);spec.loader.exec_module(upstream)
    encoder=backbone();model=LineVulFunction(encoder).eval()
    original=upstream.RobertaClassificationHead(encoder.config).eval()
    original.dense.load_state_dict(model.classifier['dense'].state_dict())
    original.out_proj.load_state_dict(model.classifier['out_proj'].state_dict())
    ids=torch.tensor([[0,5,6,2]])
    hidden=encoder(ids,attention_mask=ids.ne(1)).last_hidden_state
    expected=original(hidden).softmax(-1)[:,1]
    actual=model(ids,ids.ne(1))['logits'].sigmoid()
    torch.testing.assert_close(actual,expected)


def test_graph_features_and_neural_forward():
    feature={'sample_id':'s','label':1,'input_ids':[0,5,6,2],'leaf_to_bpe':{0:[1],1:[2]},'lexical_dfg_edges':[(1,0)]}
    batch=GraphCollator()([feature])
    assert batch['position_ids'].tolist()==[[2,3,4,5,0,0]]
    mask=batch['graph_attention_mask'][0]
    assert mask[5,4] and not mask[4,5]
    assert mask[4,1] and mask[1,4]
    model=GraphCodeBERTClassifier(backbone())
    value=model(batch['input_ids'],batch['position_ids'],batch['graph_attention_mask'])['logits']
    value.sum().backward()
    assert torch.isfinite(value).all()


def test_regvd_graph_and_forward_are_padding_invariant():
    ids=torch.tensor([[0,5,6,5,2,1],[0,5,6,5,2,1]])
    mask=ids.ne(1)
    nodes,adjacency,node_mask=build_token_graph_batch(ids,mask,window_size=3)
    assert nodes[0,:4].tolist()==[0,5,6,2]
    assert torch.allclose(adjacency,adjacency.transpose(1,2))
    embedding=torch.randn(40,16)
    model=ReGVDClassifier(embedding,hidden_size=8,layers=2,window_size=3,dropout=0.).eval()
    logits=model(ids,mask)['logits']
    torch.testing.assert_close(logits[0],logits[1])
    logits.sum().backward()
    assert model.embedding.weight.grad is None
