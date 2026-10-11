"""Summarize actual quality observations against repeat variability, without auto-acceptance."""
import argparse,csv,collections,itertools
import numpy as np
from common import *
p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--left',required=True);p.add_argument('--right',required=True);a=p.parse_args()
label=a.suite+'__'+a.left+'-vs-'+a.right
q=read(ROOT/'analysis'/f'{label}-quality.json');s=read(ROOT/'analysis'/f'{label}-self-repeat.json');out=[]
keys=['min_y','max_y','speed_rms','spring_rel_rms','spring_rel_max','plane_penetration_max']
for scene in sorted(set(r['scene'] for r in q)):
    rows=[r for r in q if r['scene']==scene];snap=[x for r in rows for x in r['snapshots'] if x['frame']>0];within=[x['metrics'] for x in s if x['scene']==scene and x['frame']>0]
    result=dict(scene=scene,contracts_equal=all(r['contract_equal'] for r in rows),snapshot_pairs=len(snap),exact_snapshots=sum(x['cross']['byte_identical'] for x in snap),self_exact=sum(x['byte_identical'] for x in within),self_comparisons=len(within),id_phase_mass_equal=all(x['cross']['same_id_order'] and x['cross']['same_phases'] and x['cross']['same_inverse_mass'] for x in snap))
    for k in ['position_rms','position_max','velocity_rms']:
        result[k]=dict(cross_max=max(x['cross'].get(k,0) for x in snap),self_max=max([x.get(k,0) for x in within] or [0]))
        for variant in [a.left,a.right]:
            result[k][variant+'_self_max']=max([x['metrics'].get(k,0) for x in s if x['scene']==scene and x['frame']>0 and x['variant']==variant] or [0])
    frame_sets={v:[] for v in [a.left,a.right]}
    for f in (ROOT/'runs').glob(a.suite+f'-s{scene:02d}-*/receipt.json'):
        r=read(f)
        if r.get('suite')!=a.suite:continue
        if r['status']=='PASS' and r['variant'] in frame_sets and r['capture']:
            data=list(csv.DictReader((f.parent/'frames.csv').open()));frame_sets[r['variant']].append((r['repeat'],np.array([[float(x[k]) for k in keys] for x in data])))
    if all(frame_sets.values()):
        arrays={v:[x[1] for x in sorted(xs,key=lambda x:x[0])] for v,xs in frame_sets.items()}
        cross=np.max([np.max(abs(x-y),axis=0) for x,y in zip(arrays[a.left],arrays[a.right])],axis=0)
        repeat=np.max([np.max(abs(x-y),axis=0) for v in arrays for x,y in itertools.combinations(arrays[v],2)] or [np.zeros(len(keys))],axis=0)
        result['all_frame_metrics']={k:dict(cross_max_abs=float(cross[i]),self_max_abs=float(repeat[i])) for i,k in enumerate(keys)}
        for variant,xs in arrays.items():
            maximum=np.max([np.max(abs(x-y),axis=0) for x,y in itertools.combinations(xs,2)] or [np.zeros(len(keys))],axis=0)
            for i,k in enumerate(keys):result['all_frame_metrics'][k][variant+'_self_max_abs']=float(maximum[i])
    out.append(result)
write(ROOT/'analysis'/f'{label}-quality-assessment.json',out)
print(json.dumps(out,ensure_ascii=False,indent=2))
