"""Endpoint-conditioned gates evaluated only on explicitly supplied edges."""
from __future__ import annotations

import torch
from torch import nn
from torch.utils.checkpoint import checkpoint

EDGE_INTERVENTIONS = {'original', 'row_mean', 'within_query_permutation', 'zero'}


class EdgeRelationGate(nn.Module):
    """g[e,h] = sigmoid(W[r,h] [hi; hj; hi*hj] + b[r,h]).

    Relation IDs index a ModuleList: the gate has no AST/DFG-specific logic.
    Checkpoint chunks to avoid retaining O(E*D) endpoint feature activations.
    query_only is a capacity control, with [hi; hi; hi*hi] and identical size.
    """
    def __init__(self, hidden_size, heads, relations, chunk_size=1024):
        super().__init__()
        if chunk_size <= 0:
            raise ValueError('chunk_size must be positive')
        self.heads, self.relations = heads, relations
        self.chunk_size = chunk_size
        self.query_only = False
        self.projections = nn.ModuleList(nn.Linear(3 * hidden_size, heads) for _ in range(relations))
        for projection in self.projections:
            nn.init.zeros_(projection.weight)
            nn.init.zeros_(projection.bias)

    def forward(self, hidden_states, edge_index, relation):
        if edge_index.ndim != 2 or edge_index.shape[1] != 3 or edge_index.dtype != torch.long:
            raise ValueError('edge_index must be int64 [E,3] (batch,query,key)')
        if not 0 <= relation < self.relations:
            raise ValueError('unknown relation index')
        projection = self.projections[relation]

        def project(states, indices):
            batch, query, key = indices.unbind(1)
            left = states[batch, query]
            right = left if self.query_only else states[batch, key]
            return torch.sigmoid(projection(torch.cat((left, right, left * right), dim=-1)))

        chunks = []
        for indices in edge_index.split(self.chunk_size):
            if torch.is_grad_enabled():
                chunks.append(checkpoint(project, hidden_states, indices, use_reentrant=False))
            else:
                chunks.append(project(hidden_states, indices))
        return torch.cat(chunks, dim=0) if chunks else hidden_states.new_empty((0, self.heads))


def intervene_edge_gates(gates, edge_index, mode, *, sample_ids, seed, layer, relation):
    """Preserve per-query/head gate multiset when permuting edge assignments.

    These are evaluation interventions, not causal explanations of the label.
    Stable sample IDs make the permutation independent of batch composition.
    """
    from astguard.utils.hashing import sha256_text
    if mode not in EDGE_INTERVENTIONS:
        raise ValueError(f'unknown edge intervention {mode}')
    if mode == 'original':
        return gates
    if mode == 'zero':
        return torch.zeros_like(gates)
    result = gates.clone()
    for batch, query in torch.unique(edge_index[:, :2], dim=0).tolist():
        indices = torch.where((edge_index[:, 0] == batch) & (edge_index[:, 1] == query))[0]
        if mode == 'row_mean':
            result[indices] = gates[indices].mean(0)
        else:
            for head in range(gates.shape[1]):
                generator = torch.Generator(device='cpu')
                identity = f'{seed}|{sample_ids[batch]}|{layer}|{relation}|{query}|{head}'
                generator.manual_seed(int(sha256_text(identity)[:16], 16))
                order = torch.randperm(len(indices), generator=generator).to(indices.device)
                result[indices, head] = gates[indices[order], head]
    return result
