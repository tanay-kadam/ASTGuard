from __future__ import annotations

from typing import Any

try:
    import torch
    from torch import nn
except ImportError:
    torch = None
    nn = None

from .attention import StructuralSelfAttention
from .bias import active_relations, attention_mode
from .heads import FunctionClassificationHead


if nn is not None:
    class _ControlledLayer(nn.Module):
        def __init__(self, upstream_layer, structural_attention=None):
            super().__init__()
            self.layer = upstream_layer
            self.structural_attention = structural_attention

        def forward(self, hidden_states, extended_attention_mask, raw_attention_mask, relation_masks, output_attentions=False, special_tokens_mask=None):
            if self.structural_attention is None:
                output = self.layer(hidden_states, attention_mask=extended_attention_mask, output_attentions=output_attentions)
                return output[0], output[1] if output_attentions else None
            attention = self.structural_attention(hidden_states, raw_attention_mask, relation_masks, output_attentions, special_tokens_mask)
            attention_output = self.layer.attention.output(attention[0], hidden_states)
            intermediate = self.layer.intermediate(attention_output)
            output = self.layer.output(intermediate, attention_output)
            return output, attention[1] if output_attentions else None


    class ASTGuardClassifier(nn.Module):
        """Explicit CodeBERT encoder path; no runtime monkey-patching."""

        def __init__(self, backbone, *, variant: str = "astguard", structural_layers=(2, 5, 8, 11), head_dropout=.1, beta_init=None, plumbing_only=False, gate_sharing='none', freeze_beta=False, degree_normalization=False):
            super().__init__()
            config = backbone.config
            if not plumbing_only and (config.hidden_size, config.num_attention_heads, config.num_hidden_layers) != (768, 12, 12):
                raise ValueError("controlled checkpoint must be CodeBERT-base shaped (768/12/12)")
            self.config = config
            self.embeddings = backbone.embeddings
            self.classifier = FunctionClassificationHead(config.hidden_size, head_dropout)
            self.gradient_checkpointing = False
            relations = active_relations(variant)
            mode = attention_mode(variant)
            beta_init = (.05 if mode == "fixed" else .10) if beta_init is None else beta_init
            layers = []
            for index, layer in enumerate(backbone.encoder.layer):
                structural = None
                if index in structural_layers and mode != 'sequence':
                    with torch.random.fork_rng(devices=[]):
                        torch.manual_seed(100000 + index)
                        structural = StructuralSelfAttention(
                            layer.attention.self, config.hidden_size, config.num_attention_heads,
                            len(relations), mode, beta_init, adapter=variant == 'fixed_adapter',
                        )
                layers.append(_ControlledLayer(layer, structural))
            self.layers = nn.ModuleList(layers)
            from .gates import RelationGate
            shared_gate=None
            for layer in self.layers:
                attention=layer.structural_attention
                if attention is None:continue
                attention.degree_normalization=degree_normalization
                if attention.gate is not None and gate_sharing in {'head','relation'}:
                    with torch.random.fork_rng(devices=[]):
                        attention.gate=RelationGate(config.hidden_size,config.num_attention_heads,len(relations),gate_sharing)
                if attention.gate is not None and gate_sharing=='layer':
                    if shared_gate is None:shared_gate=attention.gate
                    attention.gate=shared_gate
                if attention.beta is not None and freeze_beta:attention.beta.requires_grad_(False)
            self.variant = variant
            self.relations = relations

        @classmethod
        def from_pretrained(cls, checkpoint="microsoft/codebert-base", revision=None, **kwargs):
            try:
                from transformers import RobertaModel  # type: ignore
            except ImportError as exc:
                raise RuntimeError("ASTGuardClassifier requires transformers") from exc
            attn_implementation=kwargs.pop('attn_implementation','eager')
            backbone = RobertaModel.from_pretrained(checkpoint, revision=revision, add_pooling_layer=False,
                                                    attn_implementation=attn_implementation)
            return cls(backbone, **kwargs)

        def forward(self, input_ids, attention_mask, relation_masks=None, output_attentions=False, special_tokens_mask=None, output_hidden_states=False):
            hidden = self.embeddings(input_ids=input_ids)
            extended = (1.0 - attention_mask[:, None, None, :].to(hidden.dtype)) * torch.finfo(hidden.dtype).min
            attentions = []
            states = [hidden] if output_hidden_states else []
            if relation_masks is not None:
                relation_indices = {name: i for i, name in enumerate(("ast", "dfg"))}
                selected = [relation_indices[name] for name in self.relations]
                relation_masks = relation_masks[:, selected]
            for layer in self.layers:
                if self.gradient_checkpointing and self.training and not output_attentions:
                    from torch.utils.checkpoint import checkpoint
                    def step(value, current=layer):
                        return current(value, extended, attention_mask, relation_masks, False, special_tokens_mask)[0]
                    hidden = checkpoint(step, hidden, use_reentrant=False)
                    attention = None
                else:
                    hidden, attention = layer(hidden, extended, attention_mask, relation_masks, output_attentions, special_tokens_mask)
                if output_hidden_states:
                    states.append(hidden)
                if output_attentions:
                    attentions.append(attention)
            logits = self.classifier(hidden)
            return {"logits": logits, "last_hidden_state": hidden, "hidden_states": tuple(states), "attentions": tuple(attentions) if output_attentions else None}

        def set_gate_intervention(self, mode, *, sample_ids, seed=1001, training_means=None):
            """Install one registered A2 intervention for the next forward(s)."""
            for index,layer in enumerate(self.layers):
                attention=layer.structural_attention
                if attention is None or attention.mode!='adaptive':continue
                mean=None if training_means is None else training_means.get(str(index),training_means.get(index))
                attention.intervention={'mode':mode,'sample_ids':sample_ids,'layer':index,
                                        'seed':seed,'training_mean':mean}

        def clear_gate_intervention(self):
            for layer in self.layers:
                if layer.structural_attention is not None:layer.structural_attention.intervention=None
else:
    class ASTGuardClassifier:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise RuntimeError("ASTGuardClassifier requires PyTorch and Transformers; install astguard[research]")
