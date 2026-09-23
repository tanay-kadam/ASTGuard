"""C/C++ adaptation of Microsoft's pinned graph-guided embedding/mask logic.

Copyright (c) Microsoft Corporation. Upstream MIT notice is retained in
third_party/sources/CodeBERT. Added classification head and C/C++ graph source are
explicit adaptations from the original code-search encoder.
"""
import torch
from torch import nn
from astguard.models.heads import FunctionClassificationHead

STATUS={'model_id':'graphcodebert_c_adapted','status':'implemented',
        'upstream_revision':'c0de43d3aaf38e89290f1efb771f8de845e7a489','license':'MIT',
        'code_budget':384,'node_budget':128,'extractor':'local C/C++ structured CFG'}


def graph_features(feature,unk_id=3):
    if len(feature['input_ids'])>384:
        raise ValueError('GraphCodeBERT features require preprocessing at max_length=384')
    mapping={int(k):v for k,v in feature['leaf_to_bpe'].items()}
    edges=[tuple(edge) for edge in feature['lexical_dfg_edges']]
    occurrences=sorted({i for edge in edges for i in edge})[:128]
    index={node:i for i,node in enumerate(occurrences)}
    code_count=len(feature['input_ids']);length=code_count+len(occurrences)
    mask=torch.zeros(length,length,dtype=torch.bool)
    mask[:code_count,:code_count]=True
    mask[0,:]=True;mask[code_count-1,:]=True
    for node,offset in index.items():
        pieces=mapping.get(node,[])
        for piece in pieces:
            mask[code_count+offset,piece]=True
            mask[piece,code_count+offset]=True
    for consumer,source in edges:
        if consumer in index and source in index:
            mask[code_count+index[consumer],code_count+index[source]]=True
    return {'input_ids':feature['input_ids']+[unk_id]*len(occurrences),
            'position_ids':list(range(2,code_count+2))+[0]*len(occurrences),
            'graph_attention_mask':mask,'sample_id':feature['sample_id'],'label':feature['label']}


class GraphCollator:
    def __call__(self,rows):
        rows=[graph_features(row) for row in rows]
        length=max(len(row['input_ids']) for row in rows)
        batch={'input_ids':torch.ones(len(rows),length,dtype=torch.long),
               'position_ids':torch.ones(len(rows),length,dtype=torch.long),
               'graph_attention_mask':torch.zeros(len(rows),length,length,dtype=torch.bool),
               'labels':torch.tensor([row['label'] for row in rows],dtype=torch.float32),
               'sample_ids':[row['sample_id'] for row in rows]}
        for i,row in enumerate(rows):
            size=len(row['input_ids'])
            batch['input_ids'][i,:size]=torch.tensor(row['input_ids'])
            batch['position_ids'][i,:size]=torch.tensor(row['position_ids'])
            batch['graph_attention_mask'][i,:size,:size]=row['graph_attention_mask']
        return batch


class GraphCodeBERTClassifier(nn.Module):
    def __init__(self,backbone):
        super().__init__()
        self.backbone=backbone
        self.classifier=FunctionClassificationHead(backbone.config.hidden_size)

    @classmethod
    def from_pretrained(cls,checkpoint,revision=None):
        from transformers import RobertaModel
        return cls(RobertaModel.from_pretrained(checkpoint,revision=revision,add_pooling_layer=False,attn_implementation='eager'))

    def forward(self,input_ids,position_ids,graph_attention_mask):
        nodes=position_ids.eq(0);tokens=position_ids.ge(2)
        embeddings=self.backbone.embeddings.word_embeddings(input_ids)
        weights=(nodes[:,:,None]&tokens[:,None,:]&graph_attention_mask).to(embeddings.dtype)
        weights=weights/(weights.sum(-1,keepdim=True)+1e-10)
        averages=torch.einsum('bij,bjd->bid',weights,embeddings)
        embeddings=embeddings*(~nodes)[:,:,None]+averages*nodes[:,:,None]
        hidden=self.backbone(inputs_embeds=embeddings,attention_mask=graph_attention_mask,position_ids=position_ids).last_hidden_state
        return {'logits':self.classifier(hidden)}
