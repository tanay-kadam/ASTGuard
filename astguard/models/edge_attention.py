"""Additional edge-gated path; the original structural attention is unchanged."""
from __future__ import annotations

import math
import torch
from torch import nn

from .attention import StructuralSelfAttention
from .edge_gates import EdgeRelationGate, intervene_edge_gates


class EdgeStructuralSelfAttention(StructuralSelfAttention):
    def __init__(self, upstream_attention, hidden_size, heads, relations, mode, beta_init, adapter=False):
        if adapter or mode != 'edge':
            raise ValueError('edge attention requires mode=edge and no adapter')
        super().__init__(upstream_attention, hidden_size, heads, relations, 'sequence', beta_init)
        self.mode = 'edge'
        self.gate = EdgeRelationGate(hidden_size, heads, relations)
        self.beta = nn.Parameter(torch.full((heads, relations), float(beta_init)))

    def forward(self, hidden_states, attention_mask, relation_masks=None, output_attentions=False, special_tokens_mask=None):
        self.last_diagnostics = None
        query = self._heads(self.query(hidden_states))
        key = self._heads(self.key(hidden_states))
        value = self._heads(self.value(hidden_states))
        scores = torch.matmul(query.float(), key.float().transpose(-1, -2)) / math.sqrt(self.head_dim)
        batch_size, length, _ = hidden_states.shape
        diagnostics = []
        if relation_masks is not None:
            if relation_masks.shape != (batch_size, self.relations, length, length):
                raise ValueError('relation_masks must have shape [B,R,L,L]')
            if relation_masks.dtype != torch.bool:
                raise ValueError('edge relations must be binary boolean masks')
            if attention_mask.shape != (batch_size, length) or special_tokens_mask is None:
                raise ValueError('edge attention requires token attention and special-token masks')
            if special_tokens_mask.shape != attention_mask.shape:
                raise ValueError('special-token mask shape mismatch')
            eligible = attention_mask.bool() & ~special_tokens_mask.bool()
            head_index = torch.arange(self.heads, device=scores.device)[None, :]
            for relation in range(self.relations):
                edges = relation_masks[:, relation].nonzero(as_tuple=False)
                batch, left, right = edges.unbind(1)
                if not (eligible[batch, left] & eligible[batch, right]).all():
                    raise ValueError('structural edge touches padding or a special token')
                gates = self.gate(hidden_states, edges, relation).float()
                if self.intervention is not None:
                    if self.training:
                        raise ValueError('edge interventions are evaluation-only')
                    gates = intervene_edge_gates(gates, edges, relation=relation, **self.intervention)
                coefficients = gates * self.beta[:, relation][None, :]
                if self.degree_normalization:
                    degrees = relation_masks[:, relation].sum(-1)
                    coefficients = coefficients / degrees[batch, left, None].clamp_min(1).sqrt()
                # Only E*H coefficients; no [B,H,R,L,L] gate/bias allocation.
                scores = scores.index_put((batch[:, None], head_index, left[:, None], right[:, None]),
                                          coefficients, accumulate=True)
                if output_attentions:
                    diagnostics.append({'relation': relation, 'edge_index': edges.detach(),
                                        'gates': gates.detach(), 'coefficients': coefficients.detach()})
        if attention_mask.ndim == 2:
            scores = scores.masked_fill(~attention_mask[:, None, None, :].bool(), torch.finfo(scores.dtype).min)
        else:
            scores = scores + attention_mask.float()
        probabilities = torch.softmax(scores, dim=-1).to(value.dtype)
        context = torch.matmul(self.dropout(probabilities), value)
        context = context.permute(0, 2, 1, 3).contiguous().view(batch_size, length, -1)
        if output_attentions:
            self.last_diagnostics = {'edge_relations': diagnostics}
        return (context, probabilities) if output_attentions else (context,)
