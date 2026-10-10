"""Final evidence/workload audit, also supports partial progress snapshots."""
import argparse,csv,json,statistics,collections
import performance_benchmark as b
from analyze_demo_suite import compare
EXPECTED_RUNS={'pilot-v1':16,'main-v1':1072,'clock-replacement-v1':2,'context-v1':48,'gpu-v1':48,'context-heavy-v1':18,'gpu-heavy-v1':18,'cbpool-v1':40,'heapreuse-v1':40,'pooled-v1':40,'pooled-context-v1':12,'emit-v1':32,'debris-emit-v1':16}
def main():
    p=argparse.ArgumentParser();p.add_argument('--final',action='store_true');a=p.parse_args()
    jobs=[];status=collections.Counter();byname={}
    for path in sorted((b.ROOT/'runs').glob('*/job.json')):
        j=json.loads(path.read_text(encoding='utf-8'));status[j['status']]+=1
        if j['status']=='PASS':jobs.append(j);byname[j['name']]=j
    quality_path=b.ROOT/'evidence/quality-replacement.json';quality=json.loads(quality_path.read_text()) if quality_path.exists() else None
    excluded=quality['excluded_names'] if quality else []
    count=collections.Counter(j['suite'] for j in jobs);issues=[];details=[];groups=collections.defaultdict(dict)
    for j in jobs:
        if j['timing_contaminated_by_suspend'] and j['name'] not in excluded:issues.append([j['name'],'suspend'])
        if not j['no_window_verified']:issues.append([j['name'],'window'])
        groups[j['suite'],j['mode'],j['scene']][j['repeat'],j['implementation']]=j
        last=list(csv.DictReader((b.ROOT/'runs'/j['name']/'frames.csv').open()))[-1]
        if int(last['nonfinite']):issues.append([j['name'],'nonfinite',last['nonfinite']])
    for (suite,mode,scene),g in groups.items():
        if suite not in ['main-v1','cbpool-v1','heapreuse-v1','pooled-v1','emit-v1','debris-emit-v1']:continue
        for repeat,impl in list(g):
            if impl!='reference' or (repeat,'candidate') not in g:continue
            r,c=g[repeat,'reference'],g[repeat,'candidate'];rp=b.ROOT/'runs'/r['name'];cp=b.ROOT/'runs'/c['name']
            frame=str(r['frames']).zfill(4);rstate=rp/f'state_{frame}.bin';cstate=cp/f'state_{frame}.bin'
            comparison=compare(rstate,cstate)
            # Compare with ordinary reference-repeat drift for the same scene.
            other=next((x for (n,i),x in g.items() if i=='reference' and n!=repeat),None)
            reference_drift=compare(rstate,b.ROOT/'runs'/other['name']/f'state_{frame}.bin') if other else None
            details.append(dict(suite=suite,mode=mode,scene=scene,repeat=repeat,pair=comparison,reference_repeat=reference_drift))
    telemetry=[]
    for j in jobs:
        if j['suite']!='main-v1':continue
        raw=j['after_gpu']['value'].split(', ')
        if len(raw)==8:telemetry.append(dict(name=j['name'],temperature_c=float(raw[2]),gpu_utilization_percent=float(raw[3]),sm_mhz=float(raw[4]),memory_mhz=float(raw[5]),watts=float(raw[6]),pstate=raw[7]))
    b.write(b.ROOT/'analysis/output-differences.json',details)
    outputs={}
    for suite in ['main-v1','cbpool-v1','heapreuse-v1','pooled-v1','emit-v1','debris-emit-v1']:
        rows=[r for r in details if r['suite']==suite]
        outputs[suite]=dict(pairs=len(rows),state_exact_pairs=sum(r['pair']['bytes_equal'] for r in rows),reference_repeat_exact_pairs=sum(bool(r['reference_repeat'] and r['reference_repeat']['bytes_equal']) for r in rows),max_position_difference=max((r['pair'].get('positions',{}).get('max_abs',0) for r in rows),default=0))
    result=dict(created=b.now(),status='PASS' if a.final else 'PARTIAL',runs=dict(count),run_statuses=dict(status),expected_runs=EXPECTED_RUNS,issues=issues,quality_replacement=quality,output_summary=outputs,telemetry_range={k:[min(r[k] for r in telemetry),max(r[k] for r in telemetry)] for k in ['temperature_c','sm_mhz','watts']} if telemetry else {},input_manifest=str(b.ROOT/'evidence/inputs.json'))
    if a.final:
        for suite,n in EXPECTED_RUNS.items():assert count[suite]==n,(suite,count[suite],n)
        assert status=={'PASS':sum(EXPECTED_RUNS.values())},status
        assert not issues,issues
        for suite in ['main-v1','cbpool-v1','heapreuse-v1','pooled-v1','emit-v1','debris-emit-v1']:
            audit=json.loads((b.ROOT/'analysis'/f'{suite}.json').read_text(encoding='utf-8'))['audit']
            assert all(not r['initial_metadata_differences'] and not r['initial_hash_differences'] and not r['activity_differing_frames'] and not r['suspend_contaminated'] for r in audit),suite
        b.initialize()
    b.write(b.ROOT/'evidence'/('FINAL_AUDIT.json' if a.final else 'audit-progress.json'),result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
