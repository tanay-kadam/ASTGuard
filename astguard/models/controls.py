from __future__ import annotations

try:
    import torch
    from torch import nn
except ImportError:
    torch = None
    nn = None


if nn is not None:
    class FixedAdapter(nn.Module):
        def __init__(self, hidden_size: int = 768, rank: int = 12):
            super().__init__()
            self.down = nn.Linear(hidden_size, rank, bias=True)
            self.up = nn.Linear(rank, hidden_size, bias=False)
            nn.init.zeros_(self.up.weight)

        def forward(self, hidden):
            return hidden + self.up(torch.nn.functional.gelu(self.down(hidden)))


    class LinearRelationCoefficient(nn.Module):
        def __init__(self, hidden_size=768, heads=12, relations=2):
            super().__init__()
            self.heads, self.relations, self.hidden_size = heads, relations, hidden_size
            self.projection = nn.Linear(hidden_size, heads * relations, bias=False)
            self.offset = nn.Parameter(torch.full((heads, relations), .05))
            nn.init.zeros_(self.projection.weight)

        def forward(self, hidden):
            batch, length, _ = hidden.shape
            value = self.projection(hidden).view(batch, length, self.heads, self.relations).permute(0, 2, 1, 3)
            return self.offset[None, :, None, :] + value / (self.hidden_size ** .5)
else:
    class FixedAdapter:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("controls require PyTorch")
    class LinearRelationCoefficient(FixedAdapter):
        pass
