"""Run-level paired statistics; individual frames are not independent repeats."""
import argparse,csv,json,math,statistics,collections
import performance_benchmark as b
T95={1:12.7062,2:4.3027,3:3.1824,4:2.7764,5:2.5706,6:2.4469,7:2.3646,8:2.3060,9:2.2622,10:2.2281,11:2.2010,15:2.1314,19:2.0930,29:2.0452}
def ci(values):
    n=len(values);m=statistics.mean(values)
    if n<2:return [None,None]
    t=next((T95[k] for k in sorted(T95) if k>=n-1),1.96)
    d=t*statistics.stdev(values)/math.sqrt(n);return [m-d,m+d]
def analyze(suite):
    groups=collections.defaultdict(dict);runs=[]
    quality_path=b.ROOT/'evidence/quality-replacement.json';quality=json.loads(quality_path.read_text()) if suite=='main-v1' and quality_path.exists() else None
    paths=list((b.ROOT/'runs').glob(suite+'-*/job.json'))
    if quality:paths+=list((b.ROOT/'runs').glob(quality['replacement_suite']+'-*/job.json'))
    for path in sorted(paths):
        j=json.loads(path.read_text(encoding='utf-8'))
        if j['status']!='PASS':continue
        if quality and j['name'] in quality['excluded_names']:continue
        if quality and j['suite']==quality['replacement_suite']:
            assert j['scene']==quality['scene'] and j['mode']==quality['mode'] and j['repeat']==quality['replacement_repeat']
            j=dict(j,repeat=quality['replace_repeat'])
        runs.append(j);groups[j['mode'],j['scene']][j['repeat'],j['implementation']]=j
    rows=[];audit=[]
    for (mode,scene),g in sorted(groups.items()):
        repeats=sorted(r for r,i in g if i=='reference' and (r,'candidate') in g)
        if not repeats:continue
        refs=[g[r,'reference'] for r in repeats];cands=[g[r,'candidate'] for r in repeats]
        rv=[j['metrics']['complete_ms']['mean'] for j in refs];cv=[j['metrics']['complete_ms']['mean'] for j in cands]
        ratios=[c/r for c,r in zip(cv,rv)];logs=list(map(math.log,ratios));bounds=ci(logs);bounds=[math.exp(x) if x is not None else None for x in bounds]
        row=dict(mode=mode,scene=scene,name=refs[0]['initial']['name'],pairs=len(repeats),reference_ms=statistics.mean(rv),candidate_ms=statistics.mean(cv),delta_ms=statistics.mean(c-r for c,r in zip(cv,rv)),ratio_geomean=math.exp(statistics.mean(logs)),ratio_low95=bounds[0],ratio_high95=bounds[1],ratio_min=min(ratios),ratio_max=max(ratios),reference_run_cv=statistics.stdev(rv)/statistics.mean(rv) if len(rv)>1 else 0,candidate_run_cv=statistics.stdev(cv)/statistics.mean(cv) if len(cv)>1 else 0)
        row['difference_percent']=(row['ratio_geomean']-1)*100
        row['classification']='insufficient_repeats' if len(repeats)<4 else ('slower_over_5pct' if bounds[0]>1.05 else ('faster_over_5pct' if bounds[1]<.95 else ('within_5pct_interval' if bounds[0]>=.95 and bounds[1]<=1.05 else 'uncertain_or_small')))
        for metric in ['scene_ms','api_ms','wait_ms','gpu_latency_ms','gpu_total_ms']:
            for impl,items in [('reference',refs),('candidate',cands)]:row[impl+'_'+metric]=statistics.mean(j['metrics'][metric]['mean'] for j in items)
        for impl,items in [('reference',refs),('candidate',cands)]:
            row[impl+'_init_ms']=statistics.mean(j['complete']['init_ms'] for j in items)
            row[impl+'_process_ms']=statistics.mean(j['process_wall_ms'] for j in items)
            row[impl+'_p95_ms']=statistics.mean(j['metrics']['complete_ms']['p95'] for j in items)
            row[impl+'_median_ms']=statistics.mean(j['metrics']['complete_ms']['median'] for j in items)
        row.update({key:refs[0]['initial'][key] for key in ['particles','capacity','substeps','iterations','springs','triangles','rigids']})
        rows.append(row)
        for repeat,r,c in zip(repeats,refs,cands):
            init_diff={k:[r['initial'].get(k),c['initial'].get(k)] for k in set(r['initial'])|set(c['initial']) if r['initial'].get(k)!=c['initial'].get(k)}
            # Exact initial input artifacts and complete activity sequence, not just extrema.
            rr=b.ROOT/'runs'/r['name'];cr=b.ROOT/'runs'/c['name']
            rframes=list(csv.DictReader((rr/'frames.csv').open()));cframes=list(csv.DictReader((cr/'frames.csv').open()))
            initial_keys=[k for k in r['capture_files'] if k=='params.bin' or k.endswith('_0000.bin') or k.endswith('_-001.bin')]
            audit.append(dict(mode=mode,scene=scene,repeat=repeat,initial_metadata_differences=init_diff,initial_hash_differences=[k for k in initial_keys if r['capture_files'].get(k)!=c['capture_files'].get(k)],activity_differing_frames=sum(a['particles']!=z['particles'] for a,z in zip(rframes,cframes)),final_state_equal=r['capture_files'].get('state_'+str(r['frames']).zfill(4)+'.bin')==c['capture_files'].get('state_'+str(c['frames']).zfill(4)+'.bin'),suspend_contaminated=r['timing_contaminated_by_suspend'] or c['timing_contaminated_by_suspend']))
    backend={}
    for mode in sorted({r['mode'] for r in rows}):
        items=[r for r in rows if r['mode']==mode]
        backend[mode]=dict(scenes=len(items),geomean_ratio=math.exp(statistics.mean(math.log(r['ratio_geomean']) for r in items)),sum_reference_ms=sum(r['reference_ms'] for r in items),sum_candidate_ms=sum(r['candidate_ms'] for r in items),classifications=dict(collections.Counter(r['classification'] for r in items)),min_ratio=min(r['ratio_geomean'] for r in items),max_ratio=max(r['ratio_geomean'] for r in items))
    result=dict(suite=suite,created=b.now(),passed_runs=len(runs),pair_count=len(audit),quality_replacement=quality,statistics='Geometric mean of independent-process paired mean-frame ratios; Student t interval on log ratios (not frame-level pseudo-replication). 5% practical threshold predeclared before all runs completed. No familywise correction.',backend=backend,rows=rows,audit=audit)
    b.write(b.ROOT/'analysis'/f'{suite}.json',result)
    if rows:
        with (b.ROOT/'analysis'/f'{suite}.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(dict(runs=len(runs),pairs=len(audit),backend=backend,audit_issues=[x for x in audit if x['initial_metadata_differences'] or x['initial_hash_differences'] or x['activity_differing_frames'] or x['suspend_contaminated']]),ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--suite',default='main-v1');a=p.parse_args();analyze(a.suite)
