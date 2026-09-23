"""Pinned ReGVD ReGCN adapter for the common ASTGuard training contract.

Graph construction and the residual GCN/readout follow the official ICSE 2022
implementation at revision b5e6657. Node ordering is deterministic; this does
not change the permutation-invariant graph computation.
"""
from __future__ import annotations

import math

import torch
from torch import nn


UPSTREAM_REVISION = 'b5e6657b003ada704b7c75e4bd237c1eee1d8138'
STATUS = {
    'model_id': 'regvd', 'status': 'implemented',
    'upstream_revision': UPSTREAM_REVISION,
    'upstream_url': 'https://github.com/daiquocnguyen/GNN-ReGVD',
    'architecture': 'ReGCN', 'readout': 'soft-attention then sum-times-max',
    'graph': 'unique token IDs with unweighted sliding-window co-occurrence',
}


def _document_graph(token_ids: torch.Tensor, valid: torch.Tensor, window_size: int):
    sequence = token_ids[valid].tolist()
    nodes = list(dict.fromkeys(sequence))
    if not nodes:
        nodes = [0]
    index = {token: position for position, token in enumerate(nodes)}
    adjacency = torch.zeros(len(nodes), len(nodes), dtype=torch.float32, device=token_ids.device)
    windows = [sequence] if len(sequence) <= window_size else [sequence[i:i+window_size] for i in range(len(sequence)-window_size+1)]
    for window in windows:
        for right in range(1, len(window)):
            for left in range(right):
                a, b = index[window[left]], index[window[right]]
                if a != b:
                    adjacency[a,b] = adjacency[b,a] = 1.
    degree = adjacency.sum(1)
    inverse = degree.clamp_min(1).rsqrt()
    adjacency = inverse[:,None] * adjacency * inverse[None,:]
    return torch.tensor(nodes, dtype=torch.long, device=token_ids.device), adjacency


def build_token_graph_batch(input_ids: torch.Tensor, attention_mask: torch.Tensor, window_size: int):
    graphs = [_document_graph(ids, mask.bool(), window_size) for ids,mask in zip(input_ids,attention_mask)]
    size = max(len(nodes) for nodes,_ in graphs)
    node_ids = input_ids.new_zeros((len(graphs),size))
    adjacency = torch.zeros(len(graphs),size,size,dtype=torch.float32,device=input_ids.device)
    mask = torch.zeros(len(graphs),size,1,dtype=torch.float32,device=input_ids.device)
    for batch,(nodes,graph) in enumerate(graphs):
        count=len(nodes);node_ids[batch,:count]=nodes;adjacency[batch,:count,:count]=graph;mask[batch,:count]=1
    return node_ids,adjacency,mask


class GraphConvolution(nn.Module):
    def __init__(self, input_size: int, output_size: int, dropout: float):
        super().__init__()
        self.weight=nn.Parameter(torch.empty(input_size,output_size))
        self.dropout=nn.Dropout(dropout)
        bound=math.sqrt(6/(input_size+output_size));nn.init.uniform_(self.weight,-bound,bound)

    def forward(self, values, adjacency):
        return torch.relu(adjacency @ (self.dropout(values) @ self.weight))


class ReGCN(nn.Module):
    def __init__(self, feature_size=768, hidden_size=128, layers=2, dropout=.1):
        super().__init__()
        self.layers=nn.ModuleList([GraphConvolution(feature_size if i==0 else hidden_size,hidden_size,dropout) for i in range(layers)])
        self.soft_attention=nn.Linear(hidden_size,1)
        self.transform=nn.Linear(hidden_size,hidden_size)

    def forward(self, features, adjacency, mask):
        hidden=features
        for index,layer in enumerate(self.layers):
            update=layer(hidden,adjacency)*mask
            hidden=update if index==0 else hidden+update
        weights=torch.sigmoid(self.soft_attention(hidden))
        hidden=torch.relu(self.transform(hidden))*weights*mask
        maximum=hidden.masked_fill(~mask.bool(),torch.finfo(hidden.dtype).min).amax(1)
        return hidden.sum(1)*maximum


class ReGVDClassifier(nn.Module):
    def __init__(self, embedding_weight, *, hidden_size=128, layers=2, window_size=5, dropout=.1):
        super().__init__()
        self.embedding=nn.Embedding.from_pretrained(embedding_weight.detach().clone(),freeze=True)
        self.gnn=ReGCN(embedding_weight.shape[1],hidden_size,layers,dropout)
        self.dropout=nn.Dropout(dropout)
        self.dense=nn.Linear(hidden_size,hidden_size)
        self.out_proj=nn.Linear(hidden_size,2)
        self.window_size=window_size

    @classmethod
    def from_pretrained(cls, checkpoint, revision=None, **kwargs):
        from transformers import RobertaModel
        backbone=RobertaModel.from_pretrained(checkpoint,revision=revision,add_pooling_layer=False)
        return cls(backbone.embeddings.word_embeddings.weight,
                   dropout=backbone.config.hidden_dropout_prob,**kwargs)

    def forward(self,input_ids,attention_mask,relation_masks=None,special_tokens_mask=None):
        node_ids,adjacency,mask=build_token_graph_batch(input_ids,attention_mask,self.window_size)
        graph=self.gnn(self.embedding(node_ids),adjacency,mask)
        logits=self.out_proj(self.dropout(torch.tanh(self.dense(self.dropout(graph)))))
        return {'logits':logits[:,0]}
