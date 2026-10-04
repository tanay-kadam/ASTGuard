from __future__ import annotations

try:
    import torch
    from torch import nn
except ImportError:  # pragma: no cover
    torch = None
    nn = None

from .heads import FunctionClassificationHead


if nn is not None:
    class GraphResponseAdapter(nn.Module):
        """Low-rank endpoint-interaction adapter returning one graph response/logit."""

        def __init__(self, hidden_size: int, adapter_size: int, relations: int):
            super().__init__()
            self.relations = relations
            self.token_projection = nn.Linear(hidden_size, adapter_size)
            self.response = nn.Sequential(
                nn.LayerNorm(adapter_size * relations),
                nn.Linear(adapter_size * relations, adapter_size),
                nn.GELU(),
                nn.Linear(adapter_size, 1),
            )
            nn.init.zeros_(self.response[-1].weight)
            nn.init.zeros_(self.response[-1].bias)

        def forward(self, hidden_states, relation_masks, attention_mask, special_tokens_mask=None):
            if relation_masks.ndim != 4 or relation_masks.shape[1] != self.relations:
                raise ValueError("relation_masks must have shape [B,R,L,L]")
            projected = torch.nn.functional.gelu(self.token_projection(hidden_states))
            eligible = attention_mask.bool()
            if special_tokens_mask is not None:
                eligible = eligible & ~special_tokens_mask.bool()
            summaries = []
            for relation in range(self.relations):
                adjacency = relation_masks[:, relation].to(projected.dtype)
                degrees = adjacency.sum(-1, keepdim=True)
                neighbors = torch.bmm(adjacency, projected) / degrees.clamp_min(1)
                interactions = projected * neighbors
                active = eligible & degrees.squeeze(-1).gt(0)
                summary = (interactions * active[..., None]).sum(1) / active.sum(1, keepdim=True).clamp_min(1)
                summaries.append(summary)
            return self.response(torch.cat(summaries, dim=-1)).squeeze(-1)


    class NullCenteredGraphClassifier(nn.Module):
        """Sequence classifier plus a shared real-minus-null graph response."""

        def __init__(self, backbone, *, relations=("ast", "dfg"), adapter_size=64,
                     head_dropout=.1, beta_init=1.0, centered=True):
            super().__init__()
            self.backbone = backbone
            self.classifier = FunctionClassificationHead(backbone.config.hidden_size, head_dropout)
            self.graph_adapter = GraphResponseAdapter(
                backbone.config.hidden_size, adapter_size, len(relations))
            self.graph_adapter.beta = nn.Parameter(torch.tensor(float(beta_init), dtype=torch.float32))
            self.relations = tuple(relations)
            self.centered = centered

        @classmethod
        def from_pretrained(cls, checkpoint="microsoft/codebert-base", revision=None, **kwargs):
            try:
                from transformers import RobertaModel
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("NullCenteredGraphClassifier requires transformers") from exc
            backbone = RobertaModel.from_pretrained(
                checkpoint, revision=revision, add_pooling_layer=False, attn_implementation="eager")
            return cls(backbone, **kwargs)

        def _select_relations(self, masks):
            relation_indices = {"ast": 0, "dfg": 1}
            selected = [relation_indices[name] for name in self.relations]
            return masks[:, selected]

        def forward(self, input_ids, attention_mask, relation_masks=None, null_relation_masks=None,
                    special_tokens_mask=None, output_hidden_states=False):
            if relation_masks is None:
                raise ValueError("graph adapter variants require relation masks")
            encoded = self.backbone(
                input_ids=input_ids, attention_mask=attention_mask,
                output_hidden_states=output_hidden_states, return_dict=True)
            hidden = encoded.last_hidden_state
            base_logits = self.classifier(hidden)
            real_masks = self._select_relations(relation_masks)
            real_response = self.graph_adapter(hidden, real_masks, attention_mask, special_tokens_mask)
            null_response = torch.zeros_like(real_response)
            if self.centered:
                if null_relation_masks is None or null_relation_masks.ndim != 5:
                    raise ValueError("null-centered graph adapter requires [B,K,R,L,L] null masks")
                batch, draws = null_relation_masks.shape[:2]
                flat_masks = null_relation_masks[:, :, [0 if r == "ast" else 1 for r in self.relations]].reshape(
                    batch * draws, len(self.relations), *null_relation_masks.shape[-2:])
                expanded_hidden = hidden[:, None].expand(-1, draws, -1, -1).reshape(
                    batch * draws, *hidden.shape[1:])
                expanded_attention = attention_mask[:, None].expand(-1, draws, -1).reshape(
                    batch * draws, attention_mask.shape[-1])
                expanded_special = None
                if special_tokens_mask is not None:
                    expanded_special = special_tokens_mask[:, None].expand(-1, draws, -1).reshape(
                        batch * draws, special_tokens_mask.shape[-1])
                null_response = self.graph_adapter(
                    expanded_hidden, flat_masks, expanded_attention, expanded_special).reshape(batch, draws).mean(1)
            correction = self.graph_adapter.beta * (real_response - null_response)
            return {
                "logits": base_logits + correction,
                "base_logits": base_logits,
                "graph_response": real_response,
                "null_graph_response": null_response,
                "structural_correction": correction,
                "last_hidden_state": hidden,
                "hidden_states": encoded.hidden_states if output_hidden_states else (),
            }
else:
    class GraphResponseAdapter:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise RuntimeError("GraphResponseAdapter requires PyTorch")

    class NullCenteredGraphClassifier:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise RuntimeError("NullCenteredGraphClassifier requires PyTorch")
