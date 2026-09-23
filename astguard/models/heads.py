from __future__ import annotations

try:
    from torch import nn
except ImportError:
    nn = None


if nn is not None:
    class FunctionClassificationHead(nn.Module):
        def __init__(self, hidden_size: int = 768, dropout: float = .1):
            super().__init__()
            self.dropout = nn.Dropout(dropout)
            self.dense = nn.Linear(hidden_size, hidden_size)
            self.output = nn.Linear(hidden_size, 1)

        def forward(self, hidden_states):
            pooled = hidden_states[:, 0, :]
            pooled = self.dropout(pooled)
            pooled = self.dense(pooled).tanh()
            pooled = self.dropout(pooled)
            return self.output(pooled).squeeze(-1)
else:
    class FunctionClassificationHead:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise RuntimeError("FunctionClassificationHead requires PyTorch")

