"""Instrumented GPU phase attribution; never replaces production-frame results."""
import argparse,csv,collections,statistics,math
from common import *
from analyze_primary import interval
p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--left',required=True);p.add_argument('--right',required=True);a=p.parse_args()
groups=collections.defaultdict(dict)
for path in (ROOT/'runs').glob(a.suite+'-*/receipt.json'):
    r=read(path)
    if r.get('suite')!=a.suite:continue
    if r['variant'] not in [a.left,a.right]:continue
    assert r['status']=='PASS' and r['profile']&1 and not r['capture']
    phases=collections.defaultdict(list)
    for row in csv.DictReader((path.parent/'detail.csv').open()):
        if int(row['frame'])>r['warmup']:phases[row['name']].append(float(row['ms']))
    r['gpu_details']={name:statistics.mean(values) for name,values in phases.items()};groups[(r['scene'],r['repeat'])][r['variant']]=r
paired=collections.defaultdict(list)
for (scene,repeat),arms in sorted(groups.items()):
    assert a.left in arms and a.right in arms
    l,r=arms[a.left],arms[a.right]
    for phase in sorted(set(l['gpu_details'])&set(r['gpu_details'])):
        x,y=l['gpu_details'][phase],r['gpu_details'][phase]
        if x>0 and y>0:paired[(scene,phase)].append(dict(repeat=repeat,left_ms=x,right_ms=y,ratio=x/y))
rows=[]
for (scene,phase),pairs in sorted(paired.items()):
    logs=[math.log(x['ratio']) for x in pairs];ci=interval(logs)
    rows.append(dict(scene=scene,phase=phase,n=len(pairs),left_mean_ms=statistics.mean(x['left_ms'] for x in pairs),right_mean_ms=statistics.mean(x['right_ms'] for x in pairs),speedup_geomean=math.exp(statistics.mean(logs)),speedup_ci95=[math.exp(x) if x is not None else None for x in ci],pairs=pairs))
out=dict(scope='Profile1 GPU timestamp phase sums per frame, instrumented attribution only; not production completed-frame timing or game FPS.',suite=a.suite,left=a.left,right=a.right,rows=rows)
write(ROOT/'analysis'/f'{a.suite}__{a.left}-vs-{a.right}-gpu-details.json',out)
print(json.dumps([r for r in rows if r['phase'] in ['CollideParticles','SolveSprings','RadixSort1CS','RadixSort2CS','RadixSort3CS']],ensure_ascii=False,indent=2))
