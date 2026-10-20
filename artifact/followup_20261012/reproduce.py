"""Regenerate manuscript tables/figures from anonymous numerical records."""
import argparse
import json
from pathlib import Path
import numpy as np

SEEDS=[42,123,456,789,2026]
CONDITIONS=[('Attention','Sequence','attention_sequence'),('Attention','Authentic','attention_authentic'),
 ('Attention','Shuffled','attention_shuffled'),('Adapter','Sequence','adapter_sequence'),
 ('Adapter','Uncentered','adapter_uncentered'),('Adapter','Centered','adapter_centered'),
 ('ReGVD','Native','native'),('ReGVD','Permuted training','permuted'),('ReGVD','Self-only','self')]
CONTRASTS=[('Attention: authentic $-$ shuffled','attention_authentic-minus-attention_shuffled'),
 ('Attention: authentic $-$ sequence','attention_authentic-minus-attention_sequence'),
 ('Adapter: centered $-$ sequence','adapter_centered-minus-adapter_sequence'),
 ('ReGVD: native $-$ permuted','native-minus-permuted'),('ReGVD: native $-$ self','native-minus-self')]

def f(x,signed=False):return (f'{x:+.5f}' if signed else f'{x:.5f}')
def ci(x):return '$['+f(x[0],True)+', '+f(x[1],True)+']$'
def row(*items):return ' & '.join(map(str,items))+r'\\'+'\n'

def reproduce(root,output):
    d=json.loads((root/'study.json').read_text());output.mkdir(parents=True,exist_ok=True)
    tables=output/'tables';tables.mkdir(exist_ok=True);figures=output/'figures';figures.mkdir(exist_ok=True)
    text=''
    for i,(family,label,key) in enumerate(CONDITIONS):
        r=d['external_conditions'][key]
        text+=row(family,label,'$'+f(r['mean'])+r'\pm'+f(r['sample_sd'])+'$')
        if i in [2,5]:text+=r'\midrule'+'\n'
    text+=r'\bottomrule'+'\n';(tables/'performance.tex').write_text(text)
    text=''
    for label,key in CONTRASTS:
        r=d['contrasts'][key]
        text+=row(label,'$'+f(r['mean_difference'],True)+'$',str(sum(x>0 for x in r['paired_seed_differences']))+'/5',
            ci(r['seed_t_interval_95']),ci(r['component_interval_95']),ci(r['hierarchical_interval_95']))
    text+=r'\bottomrule'+'\n';(tables/'contrasts.tex').write_text(text)
    response=[]
    for condition,modes,prefix in [('attention_authentic',['empty','null'],'Attention'),
            ('adapter_centered',['base','empty','null'],'Centered'),('native',['permuted','empty','self'],'ReGVD')]:
        records=[r for r in d['external'].values() if r['condition']==condition]
        assert len(records)==5
        for mode in modes:
            delta=np.mean([r['metrics']['normal']['ap']-r['metrics'][mode]['ap'] for r in records])
            change=np.mean([r['metrics'][mode]['mean_abs_logit_change'] for r in records])
            response.append(row(prefix+': normal $-$ '+mode,'$'+f(delta,True)+'$','$'+f(change)+'$'))
    (tables/'response.tex').write_text(''.join(response)+r'\bottomrule'+'\n')
    selection=''
    for seed in SEEDS:
        r=d['selection_diagnostic'][str(seed)]
        selection+=row(seed,r['authentic_tune_epoch'],f(r['authentic_tune_audit_ap']),r['donor_tune_epoch'],f(r['donor_tune_audit_ap']))
    (tables/'selection.tex').write_text(selection+r'\bottomrule'+'\n')
    synthetic=''
    for seed in SEEDS:
        a=d['jobs'][f'synthetic_attention_shuffled_s{seed}']['metrics']['normal']['ap']
        b=d['jobs'][f'synthetic_centered_shuffled_s{seed}']['metrics']['normal']['ap']
        ok=d['synthetic_checks']['seeds'][str(seed)]['centered']['all_pass']
        synthetic+=row(seed,f(a),f(b),'Pass' if ok else 'Fail')
    (tables/'synthetic.tex').write_text(synthetic+r'\bottomrule'+'\n')
    macros={'AttnShuffleMean':f(d['contrasts'][CONTRASTS[0][1]]['mean_difference'],True),
        'AttnSequenceMean':f(d['contrasts'][CONTRASTS[1][1]]['mean_difference'],True),
        'CenteredMean':f(d['contrasts'][CONTRASTS[2][1]]['mean_difference'],True),
        'NativePermutedMean':f(d['contrasts'][CONTRASTS[3][1]]['mean_difference'],True),
        'NativeSelfMean':f(d['contrasts'][CONTRASTS[4][1]]['mean_difference'],True)}
    macros['SelectionDropMean']=f(float(np.mean([r['authentic_tune_audit_ap']-r['donor_tune_audit_ap'] for r in d['selection_diagnostic'].values()])))
    centered=[r for r in d['external'].values() if r['condition']=='adapter_centered']
    macros['CenteredBaseAP']=f(float(np.mean([r['metrics']['normal']['ap']-r['metrics']['base']['ap'] for r in centered])))
    macros['CenteredEmptyLogitMean']=f(float(np.mean([r['metrics']['empty']['mean_abs_logit_change'] for r in centered])))
    for name,key in [('CenteredUpper',CONTRASTS[2][1]),('NativeSelfUpper',CONTRASTS[4][1]),('AttnShuffleUpper',CONTRASTS[0][1])]:
        macros[name]=f(d['contrasts'][key]['hierarchical_interval_95'][1])
    macros['AttnShuffleSeedUpper']=f(d['contrasts'][CONTRASTS[0][1]]['seed_t_interval_95'][1])
    for family,prefix in [('Attention','attention_'),('Adapter','adapter_')]:
        records=[r for r in d['jobs'].values() if r['family']=='real' and r['condition'].startswith(prefix)]
        macros[family+'EndpointCount']=str(sum(r['epochs']['budget_endpoint_selected'] for r in records))
    lengths=[r['training_epochs'] for r in d['external'].values() if r['family']=='regvd']
    macros['RegvdEpochRange']=str(min(lengths))+'--'+str(max(lengths))
    slash=chr(92)
    (tables/'numbers.tex').write_text(''.join(slash+'newcommand{'+slash+key+'}{'+value+'}\n' for key,value in macros.items()))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':8.5,'axes.labelsize':8.5,'pdf.fonttype':42,'font.family':'DejaVu Serif'})
    metadata={'Creator':'','Producer':'','CreationDate':None,'ModDate':None}
    fig,ax=plt.subplots(figsize=(7.15,2.4))
    for i,(label,key) in enumerate(CONTRASTS):
        r=d['contrasts'][key];y=4-i
        ax.scatter(r['paired_seed_differences'],[y+.10]*5,s=18,color='.55',label='Individual seed' if i==0 else None,zorder=3)
        low,high=r['hierarchical_interval_95'];m=r['mean_difference']
        ax.errorbar([m],[y-.08],xerr=[[m-low],[high-m]],fmt='D',color='black',capsize=3,
            label='Mean and hierarchical 95% interval' if i==0 else None,zorder=4)
    ax.set_yticks(range(5),[x[0].replace('$-$','minus') for x in CONTRASTS][::-1])
    ax.axvline(0,color='.2',lw=.8);ax.axvline(.02,color='.3',ls='--',lw=.8)
    ax.set_xlabel('External AP difference (absolute AP units)');ax.set_ylabel('Paired training contrast')
    ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),frameon=False,ncol=2,fontsize=7.5)
    ax.spines[['top','right']].set_visible(False);fig.tight_layout()
    fig.savefig(figures/'external_contrasts.pdf',metadata=metadata);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(7.15,2.4))
    groups=[('attention_authentic','Attention'),('adapter_centered','Centered adapter'),('native','ReGVD native')]
    for ax,(condition,title) in zip(axes,groups):
        for index,seed in enumerate(SEEDS):
            record=next(r for r in (d['jobs'].values() if condition!='native' else d['external'].values()) if r['condition']==condition and r['seed']==seed and (condition=='native' or r['family']=='real'))
            history=record['epochs']['history'] if condition!='native' else record['history']
            ax.plot([r['epoch'] for r in history],[r['tune_ap'] for r in history],label=str(seed),lw=.9,
                color=plt.cm.cividis(index/4),marker='.',markersize=2)
        ax.set_title(title);ax.set_xlabel('Completed epoch');ax.set_ylabel('TUNE AP (selection role)');ax.spines[['top','right']].set_visible(False)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,title='Optimizer seed',loc='upper center',bbox_to_anchor=(.5,1.02),ncol=5,fontsize=7.5,title_fontsize=7.5,frameon=False)
    fig.tight_layout(rect=(0,0,1,.85));fig.savefig(figures/'training_histories.pdf',metadata=metadata);plt.close(fig)
    (output/'regeneration.json').write_text(json.dumps({'status':'complete','training_runs':len(d['jobs']),
        'external_evaluations':len(d['external']),'data_source':'study.json','macros':macros},indent=2)+'\n')
    print('Regenerated manuscript tables and two figures from study.json')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--output',type=Path,default=Path('regenerated'));args=p.parse_args();reproduce(args.root,args.output)
