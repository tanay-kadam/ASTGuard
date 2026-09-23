from __future__ import annotations

try:
    import torch
    from torch import nn
except ImportError:  # pragma: no cover - exercised on dependency-free smoke host
    torch = None
    nn = None


if nn is not None:
    class RelationGate(nn.Module):
        def __init__(self, hidden_size: int, heads: int, relations: int, sharing='none'):
            super().__init__()
            self.heads = heads
            self.relations = relations
            self.projected_heads = 1 if sharing=='head' else heads
            self.projected_relations = 1 if sharing=='relation' else relations
            self.projection = nn.Linear(hidden_size, self.projected_heads * self.projected_relations)
            nn.init.zeros_(self.projection.weight)
            nn.init.zeros_(self.projection.bias)

        def forward(self, hidden_states):
            batch, length, _ = hidden_states.shape
            value=torch.sigmoid(self.projection(hidden_states)).view(batch,length,self.projected_heads,self.projected_relations)
            return value.expand(batch,length,self.heads,self.relations).permute(0,2,1,3)
else:
    class RelationGate:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise RuntimeError("RelationGate requires PyTorch")
