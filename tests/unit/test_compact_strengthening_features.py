import torch
from astguard.data.collate import StructuralCollator


def test_omitting_extraction_groups_preserves_zero_dropout_model_inputs():
    full={'sample_id':'s','label':1,'input_ids':[0,100,200,100,2],
          'attention_mask':[True]*5,'special_tokens_mask':[True,False,False,False,True],
          'ast_token_edges':[[1,2],[2,1]],'dfg_token_edges':[[3,1]],
          'edge_projection_groups':[{'relation':'ast','projected_pairs':[[1,2],[2,1]]},
                                    {'relation':'dfg','projected_pairs':[[3,1]]}]}
    compact={k:v for k,v in full.items() if k!='edge_projection_groups'}
    a,b=StructuralCollator()([full]),StructuralCollator()([compact])
    for key in ['input_ids','attention_mask','special_tokens_mask','relation_masks','labels']:
        torch.testing.assert_close(a[key],b[key])
