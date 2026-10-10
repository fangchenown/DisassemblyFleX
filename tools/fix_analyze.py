"""Independent-process paired performance and numerical regression statistics."""
import argparse,json,csv,math,statistics,collections
from pathlib import Path
import fix_task as task
from performance_benchmark import write,now,sha
from performance_analyze import ci
from analyze_demo_suite import compare
ROOT=task.ROOT
def load(suite):
    path=ROOT/'evidence/quality-replacements.json';replacements=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    relevant=[x for x in replacements if x['suite']==suite];exclude={(x['mode'],x['scene'],x['repeat']) for x in relevant}
    records=[]
    for p in sorted((ROOT/'runs').glob(suite+'-*/job.json')):
        j=json.loads(p.read_text(encoding='utf-8'))
        if j['status']=='PASS' and (j['mode'],j['scene'],j['repeat']) not in exclude:records.append(j)
    for q in relevant:
        for p in sorted((ROOT/'runs').glob(q['replacement_suite']+'-*/job.json')):
            j=json.loads(p.read_text(encoding='utf-8'))
            if j['status']=='PASS':records.append(dict(j,repeat=q['repeat']))
    return records,relevant
def analyze(suite):
    runs,replacements=load(suite);groups=collections.defaultdict(dict)
    for j in runs:groups[j['mode'],j['scene']][j['repeat'],j['implementation']]=j
    rows=[];audits=[]
    for (mode,scene),g in sorted(groups.items()):
        comparisons=[('reference','candidate')]+([('legacy','candidate')] if mode=='d3d12' else [])
        for base,new in comparisons:
            repeats=sorted(r for r,impl in g if impl==base and (r,new) in g)
            if not repeats:continue
            aa=[g[r,base] for r in repeats];zz=[g[r,new] for r in repeats]
            ratios=[z['metrics']['complete_ms']['mean']/a['metrics']['complete_ms']['mean'] for a,z in zip(aa,zz)];logs=list(map(math.log,ratios));interval=ci(logs);interval=[math.exp(x) if x is not None else None for x in interval]
            ratio=math.exp(statistics.mean(logs));cls='insufficient_repeats'
            if len(repeats)>=4:cls='slower_over_5pct' if interval[0]>1.05 else ('faster_over_5pct' if interval[1]<.95 else ('within_5pct_interval' if interval[0]>=.95 and interval[1]<=1.05 else 'uncertain_or_small'))
            row=dict(mode=mode,scene=scene,name=aa[0]['initial']['name'],comparison=f'{new}/{base}',pairs=len(repeats),baseline_ms=statistics.mean(x['metrics']['complete_ms']['mean'] for x in aa),candidate_ms=statistics.mean(x['metrics']['complete_ms']['mean'] for x in zz),ratio=ratio,change_percent=(ratio-1)*100,ci_low=interval[0],ci_high=interval[1],classification=cls,ratio_min=min(ratios),ratio_max=max(ratios))
            for label,rr in [('baseline',aa),('candidate',zz)]:
                for key in ['scene_ms','api_ms','wait_ms','gpu_total_ms','gpu_latency_ms']:row[label+'_'+key]=statistics.mean(x['metrics'][key]['mean'] for x in rr)
                row[label+'_p95_ms']=statistics.mean(x['metrics']['complete_ms']['p95'] for x in rr)
                row[label+'_run_cv']=statistics.stdev(x['metrics']['complete_ms']['mean'] for x in rr)/statistics.mean(x['metrics']['complete_ms']['mean'] for x in rr) if len(rr)>1 else 0
            for key in ['particles','capacity','substeps','iterations','springs','triangles','rigids']:row[key]=aa[0]['initial'][key]
            rows.append(row)
            for repeat,a,z in zip(repeats,aa,zz):
                ap,zp=ROOT/'runs'/a['name'],ROOT/'runs'/z['name'];ar=list(csv.DictReader((ap/'frames.csv').open()));zr=list(csv.DictReader((zp/'frames.csv').open()))
                initial=[k for k in a['capture_files'] if k=='params.bin' or k.endswith('_0000.bin') or k.endswith('_-001.bin')]
                frame=str(a['frames']).zfill(4);state=compare(ap/f'state_{frame}.bin',zp/f'state_{frame}.bin')
                final_names=[name for name in a['capture_files'] if name.endswith('_'+frame+'.bin')]
                final_outputs={name:compare(ap/name,zp/name) if (zp/name).exists() else {'missing_candidate':True,'bytes_equal':False} for name in final_names}
                peers=[v for (r,i),v in g.items() if i==base and r!=repeat]
                drift=[compare(ap/f'state_{frame}.bin',ROOT/'runs'/v['name']/f'state_{frame}.bin') for v in peers]
                audits.append(dict(mode=mode,scene=scene,repeat=repeat,comparison=f'{new}/{base}',baseline_run=a['name'],candidate_run=z['name'],metadata_equal=a['initial']==z['initial'],initial_hash_mismatches=[k for k in initial if a['capture_files'][k]!=z['capture_files'].get(k)],activity_differing_frames=sum(x['particles']!=y['particles'] for x,y in zip(ar,zr)),nonfinite_final=[int(ar[-1]['nonfinite']),int(zr[-1]['nonfinite'])],clock_flag=a['timing_contaminated_by_suspend'] or z['timing_contaminated_by_suspend'],state=state,final_outputs=final_outputs,baseline_repeat_drift=drift))
    summaries={}
    for key in sorted({(r['mode'],r['comparison']) for r in rows}):
        selected=[r for r in rows if (r['mode'],r['comparison'])==key]
        summaries[' '.join(key)]=dict(scenes=len(selected),ratio_geomean=math.exp(statistics.mean(math.log(r['ratio']) for r in selected)),sum_baseline_ms=sum(r['baseline_ms'] for r in selected),sum_candidate_ms=sum(r['candidate_ms'] for r in selected),classification=dict(collections.Counter(r['classification'] for r in selected)),ratio_range=[min(r['ratio'] for r in selected),max(r['ratio'] for r in selected)])
    result=dict(suite=suite,created=now(),effective_runs=len(runs),quality_replacements=replacements,summary=summaries,rows=rows,audits=audits)
    write(ROOT/'analysis'/f'{suite}.json',result)
    if rows:
        with (ROOT/'analysis'/f'{suite}.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    issues=[r for r in audits if not r['metadata_equal'] or r['initial_hash_mismatches'] or r['activity_differing_frames'] or any(r['nonfinite_final']) or r['clock_flag']]
    print(json.dumps(dict(suite=suite,effective_runs=len(runs),summary=summaries,issues=[{k:r[k] for k in ['mode','scene','repeat','comparison','metadata_equal','initial_hash_mismatches','activity_differing_frames','nonfinite_final','clock_flag']} for r in issues]),ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--suite',default='main-v2');a=p.parse_args();analyze(a.suite)
