import copy
import json
from pathlib import Path

import pytest
import torch
from transformers import RobertaConfig, RobertaModel

from astguard.models.codebert import ASTGuardClassifier
from astguard.models.edge_gates import EdgeRelationGate, intervene_edge_gates


def model(variant, beta=None):
    torch.manual_seed(17)
    config = RobertaConfig(vocab_size=128, hidden_size=32, num_attention_heads=4,
                          num_hidden_layers=2, intermediate_size=64, max_position_embeddings=80,
                          hidden_dropout_prob=0., attention_probs_dropout_prob=0.)
    config._attn_implementation = 'eager'
    return ASTGuardClassifier(RobertaModel(config, add_pooling_layer=False), variant=variant,
                              structural_layers=(0, 1), head_dropout=0., beta_init=beta,
                              plumbing_only=True).eval()


def batch():
    ids = torch.tensor([[0, 5, 6, 7, 2], [0, 8, 9, 2, 1]])
    masks = torch.zeros(2, 2, 5, 5, dtype=torch.bool)
    masks[0, 0, 1, 2:4] = True
    masks[0, 1, 1, 2] = True  # overlapping relations must add
    masks[1, 1, 1, 2] = True
    return dict(input_ids=ids, attention_mask=ids != 1, relation_masks=masks,
                special_tokens_mask=(ids == 0) | (ids == 1) | (ids == 2))


def test_query_alias_preserves_checkpoint_and_exact_outputs():
    old, alias = model('astguard'), model('query_gated_astguard')
    alias.load_state_dict(old.state_dict(), strict=True)
    assert list(old.state_dict()) == list(alias.state_dict())
    torch.testing.assert_close(old(**batch())['logits'], alias(**batch())['logits'], atol=0, rtol=0)


@pytest.mark.parametrize('variant', ['edge_gated_astguard', 'query_capacity_matched'])
def test_zero_bias_and_initial_matched_scores(variant):
    edge = model(variant)
    fixed = model('ast_dfg_fixed')
    args = batch()
    actual, expected = edge(**args, output_hidden_states=True), fixed(**args, output_hidden_states=True)
    for left, right in zip(actual['hidden_states'], expected['hidden_states']):
        torch.testing.assert_close(left, right, atol=1e-6, rtol=1e-5)
    torch.testing.assert_close(actual['logits'], expected['logits'], atol=1e-6, rtol=1e-5)
    for layer in edge.layers:
        layer.structural_attention.beta.data.zero_()
    actual, expected = edge(**args, output_hidden_states=True), model('sequence_only')(**args, output_hidden_states=True)
    for left, right in zip(actual['hidden_states'], expected['hidden_states']):
        torch.testing.assert_close(left, right, atol=1e-6, rtol=1e-5)
    torch.testing.assert_close(actual['logits'], expected['logits'], atol=1e-6, rtol=1e-5)


def test_sparse_gate_matches_dense_formula_and_gradients_across_chunks():
    torch.manual_seed(5)
    gate = EdgeRelationGate(8, 3, 2, chunk_size=2).double()
    for parameter in gate.parameters():
        torch.nn.init.normal_(parameter, std=.1)
    reference = copy.deepcopy(gate)
    hidden = torch.randn(2, 5, 8, dtype=torch.float64, requires_grad=True)
    other = hidden.detach().clone().requires_grad_(True)
    edges = torch.tensor([[0, 1, 2], [0, 1, 3], [0, 2, 1], [1, 1, 2], [1, 2, 1]])
    values = gate(hidden, edges, 1)
    b, i, j = edges.unbind(1)
    expected = torch.sigmoid(reference.projections[1](torch.cat([other[b, i], other[b, j], other[b, i]*other[b, j]], -1)))
    assert values.shape == (5, 3) and ((values >= 0) & (values <= 1)).all()
    torch.testing.assert_close(values, expected)
    values.square().sum().backward()
    expected.square().sum().backward()
    torch.testing.assert_close(hidden.grad, other.grad)
    torch.testing.assert_close(gate.projections[1].weight.grad, reference.projections[1].weight.grad)
    assert not torch.equal(values[0], values[1])
    gate.query_only = True
    query_values = gate(hidden, edges, 1)
    torch.testing.assert_close(query_values[0], query_values[1], atol=0, rtol=0)


def test_edge_attention_dense_oracle_and_unrestricted_semantic_attention():
    edge = model('edge_gated_astguard')
    attention = edge.layers[0].structural_attention
    hidden = torch.randn(2, 5, 32)
    args = batch()
    for parameter in attention.gate.parameters():
        torch.nn.init.normal_(parameter, std=.1)
    _, probabilities = attention(hidden, args['attention_mask'], args['relation_masks'], True, args['special_tokens_mask'])
    q, k = attention._heads(attention.query(hidden)), attention._heads(attention.key(hidden))
    scores = (q @ k.transpose(-1, -2)) / (8 ** .5)
    for r in range(2):
        for b, i, j in args['relation_masks'][:, r].nonzero().tolist():
            features = torch.cat((hidden[b, i], hidden[b, j], hidden[b, i]*hidden[b, j]))
            scores[b, :, i, j] += torch.sigmoid(attention.gate.projections[r](features)) * attention.beta[:, r]
    scores = scores.masked_fill(~args['attention_mask'][:, None, None, :], torch.finfo(scores.dtype).min)
    torch.testing.assert_close(probabilities, scores.softmax(-1))
    assert (probabilities[0, :, 1, 0] > 0).all()  # no edge, still semantic attention
    output = edge(**args)['logits']
    output.square().sum().backward()
    # CLS has no structural edges. Final-layer gates cannot affect its output.
    for layer in edge.layers[:-1]:
        for parameter in layer.structural_attention.gate.parameters():
            assert parameter.grad is not None and torch.isfinite(parameter.grad).all()
            assert parameter.grad.abs().sum() > 0
        assert layer.structural_attention.beta.grad.abs().sum() > 0
    assert edge.layers[-1].structural_attention.beta.grad.abs().sum() == 0


@pytest.mark.parametrize('endpoint', [0, 3, 4])
def test_reject_special_and_padding_edges(endpoint):
    args = batch()
    args['relation_masks'][1, 0, 1, endpoint] = True
    with pytest.raises(ValueError, match='padding or a special'):
        model('edge_gated_astguard')(**args)


def test_empty_graph_padding_checkpoint_and_capacity():
    edge = model('edge_gated_astguard')
    args = batch()
    args['relation_masks'].zero_()
    torch.testing.assert_close(edge(**args)['logits'], model('sequence_only')(**args)['logits'])
    args = batch()
    single = {key: (value[1:, :, :4, :4] if key == 'relation_masks' else value[1:, :4]) for key, value in args.items()}
    torch.testing.assert_close(edge(**args)['logits'][1:], edge(**single)['logits'], atol=1e-6, rtol=1e-5)
    restored = model('edge_gated_astguard')
    restored.load_state_dict(edge.state_dict(), strict=True)
    torch.testing.assert_close(edge(**args)['logits'], restored(**args)['logits'], atol=0, rtol=0)
    assert sum(p.numel() for p in edge.parameters()) == sum(p.numel() for p in model('query_capacity_matched').parameters())
    edge.train()
    edge.gradient_checkpointing = True
    edge(**args)['logits'].sum().backward()
    assert edge.layers[0].structural_attention.gate.projections[0].weight.grad.abs().sum() > 0


def test_interventions_preserve_within_query_distribution():
    edges = torch.tensor([[0, 1, 2], [0, 1, 3], [0, 2, 1], [1, 1, 2]])
    gates = torch.tensor([[.1, .2], [.8, .9], [.4, .5], [.6, .7]])
    kwargs = dict(sample_ids=['a', 'b'], seed=1, layer=0, relation=0)
    shuffled = intervene_edge_gates(gates, edges, 'within_query_permutation', **kwargs)
    torch.testing.assert_close(shuffled[:2].sort(0).values, gates[:2].sort(0).values)
    torch.testing.assert_close(shuffled[2:], gates[2:])
    mean = intervene_edge_gates(gates, edges, 'row_mean', **kwargs)
    torch.testing.assert_close(mean[:2], gates[:2].mean(0).expand(2, -1))
    edge = model('edge_gated_astguard')
    with pytest.raises(ValueError, match='set_edge_intervention'):
        edge.set_gate_intervention('original', sample_ids=['a', 'b'])


def test_product_term_permits_query_dependent_neighbor_rank_reversal():
    gate = EdgeRelationGate(1, 1, 1)
    states = torch.tensor([[[1.], [-1.], [2.], [-2.]]])
    edges = torch.tensor([[0, 0, 2], [0, 0, 3], [0, 1, 2], [0, 1, 3]])
    with torch.no_grad():
        gate.projections[0].weight[0, 2] = 1.
    values = gate(states, edges, 0).flatten()
    assert values[0] > values[1] and values[2] < values[3]
    with torch.no_grad():
        gate.projections[0].weight.copy_(torch.tensor([[.3, .5, 0.]]))
    values = gate(states, edges, 0).flatten()
    assert values[0] > values[1] and values[2] > values[3]


def test_final_layer_structure_cannot_change_cls_logits():
    edge = model('edge_gated_astguard')
    args = batch()
    before = edge(**args)['logits']
    with torch.no_grad():
        edge.layers[-1].structural_attention.beta.fill_(100.)
    torch.testing.assert_close(before, edge(**args)['logits'], atol=0, rtol=0)


def test_eval_intervention_and_gradient_checkpointing_guard():
    edge = model('edge_gated_astguard')
    args = batch()
    edge.set_edge_intervention('zero', sample_ids=['a', 'b'])
    torch.testing.assert_close(edge(**args)['logits'], model('sequence_only')(**args)['logits'])
    edge.train()
    with pytest.raises(ValueError, match='evaluation-only'):
        edge(**args)
    edge.clear_gate_intervention()
    edge.eval()
    assert torch.isfinite(edge(**args)['logits']).all()


def test_pretrained_edge_zero_bias_all_hidden_states_and_logits():
    source = Path('artifacts/environment/development_sources.json')
    if not source.exists():
        pytest.skip('local pinned public CodeBERT checkpoint not acquired')
    info = json.loads(source.read_text())
    if not Path(info['codebert_path']).exists():
        pytest.skip('local pinned public CodeBERT checkpoint not acquired')
    from astguard.alignment.tokenizer import CanonicalTokenizer
    encoded = CanonicalTokenizer(info['codebert_path']).encode('int f(int x) { return x + 1; }')
    ids = torch.tensor([encoded.input_ids])
    mask = torch.ones_like(ids)
    specials = torch.tensor([encoded.special_tokens_mask])
    backbone = RobertaModel.from_pretrained(info['codebert_path'], add_pooling_layer=False, attn_implementation='eager').eval()
    with torch.no_grad():
        expected = backbone(ids, attention_mask=mask, output_hidden_states=True)
    edge = ASTGuardClassifier(backbone, variant='edge_gated_astguard', beta_init=0.).eval()
    relations = torch.zeros(1, 2, ids.shape[1], ids.shape[1], dtype=torch.bool)
    relations[0, :, 1, 2] = True
    with torch.no_grad():
        actual = edge(ids, mask, relations, special_tokens_mask=specials, output_hidden_states=True)
    for left, right in zip(actual['hidden_states'], expected.hidden_states):
        torch.testing.assert_close(left, right, atol=1e-6, rtol=1e-5)
    torch.testing.assert_close(actual['logits'], edge.classifier(expected.last_hidden_state), atol=1e-6, rtol=1e-5)
