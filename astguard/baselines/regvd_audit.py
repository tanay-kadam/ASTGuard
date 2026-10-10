"""Native ReGVD graph interventions; upstream padding behavior is intentional."""
import hashlib
import random
from collections import defaultdict

import torch


def native_graph(ids, window=5):
    nodes = list(dict.fromkeys(ids)); index = {value:i for i,value in enumerate(nodes)}
    edges = set()
    for right in range(len(ids)):
        for left in range(max(0, right-window+1), right):
            a,b = index[ids[left]], index[ids[right]]
            if a != b: edges.update(((a,b),(b,a)))
    return nodes, sorted(edges)


def permute_edges(nodes, edges, seed, sample_id):
    edges = [tuple(edge) for edge in edges]
    degree = [0] * len(nodes)
    for a,b in edges: degree[a] += 1
    groups = defaultdict(list)
    for node,d in enumerate(degree): groups[d].append(node)
    rng = random.Random(int(hashlib.sha256(f'regvd-null-v1|{seed}|{sample_id}'.encode()).hexdigest()[:16],16))
    permutation = list(range(len(nodes)))
    for d in sorted(groups):
        members = groups[d]; shuffled = members[:]; rng.shuffle(shuffled)
        for a,b in zip(members,shuffled): permutation[a] = b
    new_edges = sorted({(permutation[a],permutation[b]) for a,b in edges})
    new_degree = [0] * len(nodes)
    for a,b in new_edges: new_degree[a] += 1
    assert degree == new_degree
    fraction = len(set(edges)-set(new_edges)) / len(edges) if edges else 0.0
    return new_edges, fraction


class NativeGraphCollator:
    def __init__(self, mode='native', seed=42): self.mode, self.seed = mode, seed

    def __call__(self, rows):
        graphs = []
        for row in rows:
            nodes = row.get('node_ids'); edges = row.get('native_edges')
            if nodes is None: nodes,edges = native_graph(row['input_ids'])
            change = 0.0
            if self.mode == 'permuted': edges,change = permute_edges(nodes,edges,self.seed,row['sample_id'])
            elif self.mode == 'empty': edges = []
            elif self.mode == 'self': edges = [(i,i) for i in range(len(nodes))]
            graphs.append((nodes,edges,change))
        n = max(len(nodes) for nodes,_,_ in graphs)
        ids = torch.zeros(len(rows),n,dtype=torch.long)
        adj = torch.zeros(len(rows),n,n,dtype=torch.float64)
        mask = torch.zeros(len(rows),n,1,dtype=torch.float64)
        for i,(nodes,edges,_) in enumerate(graphs):
            ids[i,:len(nodes)] = torch.tensor(nodes); mask[i,:len(nodes)] = 1
            if edges:
                e = torch.tensor(edges); adj[i,e[:,0],e[:,1]] = 1
            degree = adj[i].sum(1); inverse = degree.clamp_min(1).rsqrt()
            adj[i] *= inverse[:,None]*inverse[None,:]
        return {'node_ids':ids, 'adjacency':adj, 'node_mask':mask, 'labels':torch.tensor([r['label'] for r in rows],dtype=torch.float32),
                'sample_ids':[r['sample_id'] for r in rows], 'edge_change':[g[2] for g in graphs]}


def native_forward(model, batch, device):
    graph = model.gnn(model.embedding(batch['node_ids'].to(device)).double(),
                      batch['adjacency'].to(device),batch['node_mask'].to(device))
    logits = model.out_proj(model.dropout(torch.tanh(model.dense(model.dropout(graph.float())))))
    return logits[:,0]
