"""Instrumented CPU attribution, explicitly separate from production wall-clock ranking."""
import argparse,csv,collections,statistics,math
from common import *
from analyze_primary import interval
p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--left',required=True);p.add_argument('--right',required=True);a=p.parse_args()
controller=read(ROOT/'jobs'/f'{a.suite}-controller.json');assert controller['status']=='PASS'
replacement=ROOT/'evidence'/(a.suite+'-replacements.json');mapping=read(replacement)['mapping'] if replacement.exists() else {}
groups=collections.defaultdict(dict)
for path in (ROOT/'runs').glob(a.suite+'-*/receipt.json'):
    r=read(path)
    if r.get('suite')!=a.suite:continue
    if r['variant'] not in [a.left,a.right]:continue
    if r['name'] in mapping:r=read(ROOT/'runs'/mapping[r['name']]/'receipt.json')
    assert r['status']=='PASS' and r['profile']&4 and not r['capture'] and not r.get('diagnostic_only')
    phases=collections.defaultdict(lambda:collections.defaultdict(list))
    for row in csv.DictReader((ROOT/'runs'/r['name']/'cpu-phases.csv').open()):
        if int(row['frame'])<=r['warmup']:continue
        for field in ['wall_ms','thread_ms','process_ms','cycles']:phases[row['phase']][field].append(float(row[field]))
    assert 'WholeFrame' in phases
    r['cpu_metrics']={phase:{field:statistics.mean(values) for field,values in metrics.items()} for phase,metrics in phases.items()};groups[(r['scene'],r['repeat'])][r['variant']]=r
observations=collections.defaultdict(list);excluded=[]
for (scene,repeat),arms in groups.items():
    l,r=arms[a.left],arms[a.right]
    if l['timing_contaminated_by_suspend'] or r['timing_contaminated_by_suspend']:excluded.append(dict(scene=scene,repeat=repeat));continue
    assert (ROOT/'runs'/l['name']/'contract.csv').read_bytes()==(ROOT/'runs'/r['name']/'contract.csv').read_bytes()
    for phase in set(l['cpu_metrics'])&set(r['cpu_metrics']):
        for metric in ['wall_ms','thread_ms','process_ms','cycles']:
            x,y=l['cpu_metrics'][phase][metric],r['cpu_metrics'][phase][metric]
            if x>0 and y>0:observations[(scene,phase,metric)].append(dict(repeat=repeat,left=x,right=y,logratio=math.log(x/y),left_run=l['name'],right_run=r['name']))
rows=[];summary=[]
for (scene,phase,metric),pairs in sorted(observations.items()):
    if len(pairs)<2:continue
    ci=interval([r['logratio'] for r in pairs]);rows.append(dict(scene=scene,phase=phase,metric=metric,n=len(pairs),left_mean=statistics.mean(r['left'] for r in pairs),right_mean=statistics.mean(r['right'] for r in pairs),speedup=math.exp(statistics.mean(r['logratio'] for r in pairs)),ci95=[math.exp(x) for x in ci],pairs=pairs))
for phase,metric in sorted(set((r['phase'],r['metric']) for r in rows)):
    selected=[r for r in rows if r['phase']==phase and r['metric']==metric];repeat_sets=[set(x['repeat'] for x in r['pairs']) for r in selected];balanced=all(x==repeat_sets[0] for x in repeat_sets);by_repeat=collections.defaultdict(list)
    for r in selected:
        for pair in r['pairs']:by_repeat[pair['repeat']].append(pair['logratio'])
    ci=interval([statistics.mean(v) for v in by_repeat.values()]) if balanced else [None,None]
    summary.append(dict(phase=phase,metric=metric,scenes=len(selected),speedup=math.exp(statistics.mean(math.log(r['speedup']) for r in selected)),ci95=[math.exp(x) if x is not None else None for x in ci],sum_scene_left=sum(r['left_mean'] for r in selected),sum_scene_right=sum(r['right_mean'] for r in selected),balanced=balanced))
label=a.suite+'__'+a.left+'-vs-'+a.right;result=dict(suite=a.suite,left=a.left,right=a.right,summary=summary,scenes=rows,excluded_clock_pairs=excluded,scope='Same frozen FlexDemo executable, CPU probe mode4; observer overhead is present. WholeFrame thread/process time and cycles distinguish CPU work from GPU waiting. These are not uninstrumented frame-time rankings; cycles are not converted to seconds.')
write(ROOT/'analysis'/f'{label}-cpu-attribution.json',result)
print(json.dumps([x for x in summary if x['phase'] in ['WholeFrame','Solve','UpdateSolver','FinalMap']],ensure_ascii=False,indent=2))
