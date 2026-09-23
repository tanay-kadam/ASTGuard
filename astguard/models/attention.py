from __future__ import annotations

import math

try:
    import torch
    from torch import nn
except ImportError:
    torch = None
    nn = None

from .gates import RelationGate
from .controls import FixedAdapter, LinearRelationCoefficient


if nn is not None:
    class StructuralSelfAttention(nn.Module):
        """RoBERTa-compatible self attention with additive soft relation bias."""

        def __init__(self, upstream_attention, hidden_size: int, heads: int, relations: int, mode: str, beta_init: float, adapter=False):
            super().__init__()
            self.query = upstream_attention.query
            self.key = upstream_attention.key
            self.value = upstream_attention.value
            self.dropout = upstream_attention.dropout
            self.heads = heads
            self.head_dim = hidden_size // heads
            self.relations = relations
            self.mode = mode
            self.adapter = FixedAdapter(hidden_size, min(12, hidden_size)) if adapter else None
            self.linear = LinearRelationCoefficient(hidden_size, heads, relations) if mode == 'linear' else None
            self.last_diagnostics = None
            self.degree_normalization=False
            self.intervention=None
            if mode in {"adaptive", "function"}:
                self.gate = RelationGate(hidden_size, heads, relations)
                self.beta = nn.Parameter(torch.full((heads, relations), float(beta_init), dtype=torch.float32))
            elif mode == "fixed":
                self.gate = None
                self.beta = nn.Parameter(torch.full((heads, relations), float(beta_init), dtype=torch.float32))
            elif mode in {"sequence", "linear"}:
                self.gate = None
                self.register_parameter("beta", None)
            else:
                raise ValueError(f"unknown attention mode {mode}")

        def _heads(self, tensor):
            batch, length, _ = tensor.shape
            return tensor.view(batch, length, self.heads, self.head_dim).permute(0, 2, 1, 3)

        def forward(self, hidden_states, attention_mask, relation_masks=None, output_attentions=False, special_tokens_mask=None):
            projected = self.adapter(hidden_states) if self.adapter is not None else hidden_states
            query = self._heads(self.query(projected))
            key = self._heads(self.key(projected))
            value = self._heads(self.value(projected))
            scores = torch.matmul(query.float(), key.float().transpose(-1, -2)) / math.sqrt(self.head_dim)
            if self.mode != "sequence" and relation_masks is not None:
                if relation_masks.ndim != 4 or relation_masks.shape[1] != self.relations:
                    raise ValueError("relation_masks must have shape [B,R,L,L]")
                if self.mode == "adaptive":
                    gates=self.gate(hidden_states).float()
                    if self.intervention is not None:
                        from astguard.analysis.interventions import intervene_gates
                        gates=intervene_gates(gates,relation_masks,**self.intervention)
                    coefficients = gates * self.beta[None, :, None, :]
                elif self.mode == 'function':
                    if special_tokens_mask is None:
                        raise ValueError('function_gate requires special_tokens_mask')
                    eligible = attention_mask.bool() & ~special_tokens_mask.bool()
                    mean = (hidden_states * eligible[..., None]).sum(1) / eligible.sum(1, keepdim=True).clamp_min(1)
                    coefficients = self.gate(mean[:, None]).float() * self.beta[None, :, None, :]
                elif self.mode == 'linear':
                    coefficients = self.linear(hidden_states).float()
                else:
                    coefficients = self.beta[None, :, None, :].expand(hidden_states.shape[0], -1, hidden_states.shape[1], -1)
                for relation in range(self.relations):
                    relation_mask=relation_masks[:,relation,None].float()
                    if self.degree_normalization:
                        relation_mask=relation_mask/relation_mask.sum(-1,keepdim=True).clamp_min(1).sqrt()
                    scores = scores + coefficients[..., relation, None] * relation_mask
                if output_attentions:
                    self.last_diagnostics = {'coefficients': coefficients.detach(),'gates':gates.detach() if self.mode=='adaptive' else None}
            if attention_mask.ndim == 2:
                scores = scores.masked_fill(~attention_mask[:, None, None, :].bool(), torch.finfo(scores.dtype).min)
            else:
                scores = scores + attention_mask.float()
            probabilities = torch.softmax(scores, dim=-1).to(value.dtype)
            context = torch.matmul(self.dropout(probabilities), value)
            context = context.permute(0, 2, 1, 3).contiguous().view(hidden_states.shape[0], hidden_states.shape[1], -1)
            return (context, probabilities) if output_attentions else (context,)
else:
    class StructuralSelfAttention:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise RuntimeError("StructuralSelfAttention requires PyTorch")
