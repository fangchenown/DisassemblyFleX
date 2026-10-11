"""Classify actual particle growth; DEMO_EMIT is the original space-key toggle."""
import argparse,statistics,math
from common import *
from analyze_primary import interval
p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--left',required=True);p.add_argument('--right',required=True);a=p.parse_args();stem=a.suite+'__'+a.left+'-vs-'+a.right
rows=read(ROOT/'analysis'/(stem+'-scenes.json'));summary=read(ROOT/'analysis'/(stem+'-summary.json'));assert summary['balanced_repeat_panels']
classified=[];growth=[]
for row in rows:
    ranges=[]
    for pair in row['pairs']:
        l,r=read(pair['left_receipt']),read(pair['right_receipt']);assert l['particles']==r['particles'];ranges.append(l['particles'])
    grows=all(high>low for low,high in ranges);kind='actual-particle-growth' if grows else 'zero-particle-control' if all(high==0 for low,high in ranges) else 'fixed-particle-count'
    classified.append(dict(scene=row['scene'],name=row['name'],kind=kind,particle_ranges=ranges))
    if grows:growth.append(row)
assert growth;repeats=sorted(p['repeat'] for p in growth[0]['pairs']);logs=[]
for repeat in repeats:logs.append(statistics.mean(next(p['logratio'] for p in row['pairs'] if p['repeat']==repeat) for row in growth))
ci=interval(logs);result=dict(suite=a.suite,left=a.left,right=a.right,scope='Read-only postclassification by actual counts, not performance outcome. Original six-scene space-toggle panel and its statistics remain unchanged. Scene Initialize keeps its own default emitter state; DEMO_EMIT sends space and toggles it.',scenes=classified,growth_only=dict(scenes=[r['scene'] for r in growth],repeat_blocks=len(logs),equal_scene_geomean=math.exp(statistics.mean(logs)),equal_scene_geomean_ci95=[math.exp(v) for v in ci]))
write(ROOT/'analysis'/(stem+'-emission-semantics.json'),result);print(json.dumps(result,ensure_ascii=False,indent=2))
