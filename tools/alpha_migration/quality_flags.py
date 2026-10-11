"""Triage strict outputs and repeat envelopes without accepting numeric drift."""
import argparse
from common import *
p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--left',required=True);p.add_argument('--right',required=True);a=p.parse_args();label=a.suite+'__'+a.left+'-vs-'+a.right
rows=read(ROOT/'analysis'/f'{label}-quality-assessment.json');flags=[]
for row in rows:
    item=dict(scene=row['scene'],exact_snapshots=row['exact_snapshots'],snapshot_pairs=row['snapshot_pairs'],strict_contracts=row['contracts_equal'] and row['id_phase_mass_equal'],metrics=[])
    for name in ['position_rms','position_max','velocity_rms']:
        values=row[name];cross=values['cross_max'];left=values[a.left+'_self_max'];right=values[a.right+'_self_max']
        if cross>left or right>left:item['metrics'].append(dict(name=name,cross_max=cross,baseline_self_max=left,candidate_self_max=right,baseline_deterministic=left==0))
    for name,values in row.get('all_frame_metrics',{}).items():
        cross=values['cross_max_abs'];left=values[a.left+'_self_max_abs'];right=values[a.right+'_self_max_abs']
        if cross>left or right>left:item['metrics'].append(dict(name=name,cross_max=cross,baseline_self_max=left,candidate_self_max=right,baseline_deterministic=left==0))
    if item['metrics'] or not item['strict_contracts']:flags.append(item)
result=dict(scope='Review flags only. Candidate repeat noise never enlarges the baseline envelope. A flag is not an automatic acceptance or proof of physical change; inspect trajectories and original arithmetic.',suite=a.suite,left=a.left,right=a.right,scenes=len(rows),flags=flags)
write(ROOT/'analysis'/f'{label}-quality-flags.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
