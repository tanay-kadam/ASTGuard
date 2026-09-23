"""Claims are generated only from explicitly supplied verified evidence."""


def supported_claims(evidence):
    claims={}
    claims['adaptivity']=bool(evidence.get('adaptive_vs_fixed',{}).get('strong_positive'))
    claims['structure']=bool(evidence.get('adaptive_vs_sequence',{}).get('strong_positive'))
    claims['mechanism']=claims['adaptivity'] and all(evidence.get(key,False) for key in ['A1_supported','A2_supported','A3_supported'])
    low=evidence.get('low_fpr',{})
    claims['low_fpr']=bool(low and low.get('recall_difference_lower',0)>0 and low.get('adaptive_fpr',1)<=.005 and low.get('baseline_fpr',1)<=.005)
    robust=evidence.get('dropout',{})
    claims['dropout_tradeoff']=bool(robust and robust.get('clean_ap_loss',1)<=.01 and robust.get('area_difference_lower',0)>0)
    efficiency=evidence.get('efficiency',{})
    claims['modest_overhead']=bool(efficiency.get('same_host') and efficiency.get('batch1_end_to_end_median_ratio',float('inf'))<=1.25 and efficiency.get('peak_vram_ratio',float('inf'))<=1.25)
    claims['transfer']=bool(evidence.get('transfer',{}).get('frozen_decontaminated_cohort') and evidence.get('transfer',{}).get('positive_evidence'))
    return claims
