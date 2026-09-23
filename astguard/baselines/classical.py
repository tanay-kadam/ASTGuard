from __future__ import annotations

import math

from .base import BaselineAdapter
from .simple import PriorBaseline,TfidfLogisticBaseline


class PriorAdapter(BaselineAdapter):
    def __init__(self):self.model=PriorBaseline()
    def prepare_features(self,rows):return list(rows)
    def fit(self,train_rows,tune_rows):self.model.fit(train_rows);return {'prevalence':self.model.prevalence}
    def predict_to_common_schema(self,rows):
        result=[]
        for row in rows:
            logit=self.model.predict_logit(row)
            result.append({'sample_id':row['sample_id'],'label':int(row['label']),'logit':logit,'probability':1/(1+math.exp(-logit))})
        return result
    def provenance(self):return {'model':'training_prevalence_prior','fit_roles':['train']}
    def status(self):return {'model_id':'prior','status':'implemented'}


class TfidfAdapter(BaselineAdapter):
    def __init__(self,tokenizer):self.model=TfidfLogisticBaseline(tokenizer)
    def prepare_features(self,rows):return list(rows)
    def fit(self,train_rows,tune_rows):return self.model.fit(train_rows,tune_rows)
    def predict_to_common_schema(self,rows):
        scores=self.model.predict(rows);result=[]
        for row,probability in zip(rows,scores):
            value=min(max(float(probability),1e-12),1-1e-12)
            result.append({'sample_id':row['sample_id'],'label':int(row['label']),
                           'logit':math.log(value/(1-value)),'probability':value})
        return result
    def provenance(self):return {'model':'case_sensitive_lexical_tfidf_logistic','ngram_range':[1,2],
                                  'max_features':100000,'min_df':2,'selected_C':self.model.selected_c,
                                  'fit_roles':['train','tune_selection']}
    def status(self):return {'model_id':'tfidf_lr','status':'implemented'}
