"""Function head reproduced from the pinned MIT LineVul replication package.

The two-logit softmax is preserved. Its logit difference allows the shared binary
metric and weighted BCE implementation without changing probabilities.
"""
import torch
from torch import nn

STATUS = {'model_id':'linevul_function','status':'implemented',
          'upstream_revision':'9401ec6e60b762a9308645961268203244bee048',
          'license':'MIT','supervised_history':'CodeBERT pretraining only'}


class LineVulFunction(nn.Module):
    def __init__(self,backbone):
        super().__init__()
        self.backbone=backbone
        d=backbone.config.hidden_size
        self.classifier=nn.ModuleDict({'dense':nn.Linear(d,d),'out_proj':nn.Linear(d,2)})
        self.dropout=nn.Dropout(backbone.config.hidden_dropout_prob)

    @classmethod
    def from_pretrained(cls,checkpoint,revision=None):
        from transformers import RobertaModel
        return cls(RobertaModel.from_pretrained(checkpoint,revision=revision,add_pooling_layer=False,attn_implementation='eager'))

    def forward(self,input_ids,attention_mask,relation_masks=None,special_tokens_mask=None):
        hidden=self.backbone(input_ids,attention_mask=attention_mask).last_hidden_state
        value=self.dropout(hidden[:,0])
        value=self.dropout(torch.tanh(self.classifier['dense'](value)))
        logits=self.classifier['out_proj'](value)
        return {'logits':logits[:,1]-logits[:,0],'two_class_logits':logits}
