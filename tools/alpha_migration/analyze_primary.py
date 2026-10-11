"""Process-paired scene statistics; never treat correlated frames as repeats."""
import csv,math,statistics,collections,argparse
from common import *
T95={1:12.7062047364,2:4.3026527297,3:3.1824463053,4:2.7764451052,5:2.5705818356,6:2.4469118511,7:2.3646242516,8:2.3060041352,9:2.2621571629,10:2.228138852}
def interval(values):
    mean=statistics.mean(values);n=len(values)
    if n<2:return [None,None]
    half=T95.get(n-1,1.96)*statistics.stdev(values)/math.sqrt(n);return [mean-half,mean+half]
def main():
    p=argparse.ArgumentParser();p.add_argument('--suite',default='primary-v1');p.add_argument('--left',default='df');p.add_argument('--right',default='of');p.add_argument('--metric',choices=['complete','solver'],default='complete');a=p.parse_args()
    controller=read(ROOT/'jobs'/f'{a.suite}-controller.json');assert controller['status'] in ['PASS','COMPLETE_WITH_FAILURES'],controller
    receipts=[r for f in (ROOT/'runs').glob(a.suite+'-*/receipt.json') if (r:=read(f)).get('suite')==a.suite];assert len(receipts)==controller['runs'] and all(r['status'] in ['PASS','FAIL'] for r in receipts)
    assert not any(r.get('diagnostic_only') for r in receipts if r['variant'] in [a.left,a.right]),'Diagnostic DLL timings are not production performance evidence'
    replacement_file=ROOT/'evidence'/('primary-replacements.json' if a.suite=='primary-v1' else 'emission-replacements.json' if a.suite=='emission-v1' else a.suite+'-replacements.json')
    replacements=read(replacement_file)['mapping'] if replacement_file.exists() else {}
    originals=receipts
    receipts=[read(ROOT/'runs'/replacements[r['name']]/'receipt.json') if r['name'] in replacements else r for r in receipts]
    groups=collections.defaultdict(dict);audit=[]
    for r in receipts:
        if r['variant'] not in [a.left,a.right]:continue
        groups[(r['scene'],r['emit'])].setdefault(r['repeat'],{})[r['variant']]=r
    rows=[];all_logs_by_repeat=collections.defaultdict(list);failed_pairs=[];excluded_scenes=[];clock_excluded_pairs=[]
    for (scene,emit),repeats in sorted(groups.items()):
        pairs=[];workload_equal=True;params_equal=True;ids_equal=True;initial_equal=True;windowless=True;finite=True;contaminated=[]
        for repeat,arms in sorted(repeats.items()):
            l,r=arms[a.left],arms[a.right];ld=ROOT/'runs'/l['name'];rd=ROOT/'runs'/r['name']
            if l['status']!='PASS' or r['status']!='PASS':
                failed_pairs.append(dict(scene=scene,repeat=repeat,left_run=l['name'],right_run=r['name'],left_status=l['status'],right_status=r['status'],scope='No valid performance pair; failure retained as compatibility evidence.'));continue
            lcontracts=list(csv.DictReader((ld/'contract.csv').open()));rcontracts=list(csv.DictReader((rd/'contract.csv').open()));ce=lcontracts==rcontracts;workload_equal&=ce
            pe=(ld/'params.bin').read_bytes()==(rd/'params.bin').read_bytes();params_equal&=pe
            se=(ld/'state_0000.bin').read_bytes()==(rd/'state_0000.bin').read_bytes();initial_equal&=se
            windowless&=l['complete']['owned_top_level_windows']==r['complete']['owned_top_level_windows']==0
            finite&=(l.get('endpoint_nonfinite',0)==0 and r.get('endpoint_nonfinite',0)==0)
            if l['timing_contaminated_by_suspend'] or r['timing_contaminated_by_suspend']:
                contaminated.append(repeat);clock_excluded_pairs.append(dict(scene=scene,emit=emit,repeat=repeat,left=l['name'],right=r['name']));continue
            if a.metric=='solver':
                assert (ld/'replay-inputs.csv').read_bytes()==(rd/'replay-inputs.csv').read_bytes(),'Common-input replay mismatch'
                lm=l['metrics']['api_ms']['mean']+l['metrics']['wait_ms']['mean'];rm=r['metrics']['api_ms']['mean']+r['metrics']['wait_ms']['mean']
            else:lm=l['metrics']['complete_ms']['mean'];rm=r['metrics']['complete_ms']['mean']
            logratio=math.log(lm/rm)
            pairs.append(dict(repeat=repeat,left_ms=lm,right_ms=rm,speedup_left_over_right=lm/rm,logratio=logratio,contract_equal=ce,params_equal=pe,initial_state_byte_equal=se,left_receipt=str(ld/'receipt.json'),right_receipt=str(rd/'receipt.json'),left_init_ms=l['complete']['init_ms'],right_init_ms=r['complete']['init_ms']))
        if len(pairs)<2:
            excluded_scenes.append(dict(scene=scene,emit=emit,valid_pairs=len(pairs),reason='Fewer than two successfully completed, clock-valid paired processes'));continue
        for pair in pairs:all_logs_by_repeat[pair['repeat']].append(pair['logratio'])
        logs=[r['logratio'] for r in pairs];ci=interval(logs);ratios=[r['speedup_left_over_right'] for r in pairs]
        lo,hi=[math.exp(v) if v is not None else None for v in ci];geo=math.exp(statistics.mean(logs));decision='right-faster' if lo and lo>1 else 'left-faster' if hi and hi<1 else 'inconclusive-at-95pct'
        first=next(arms[a.left] for arms in repeats.values() if arms[a.left]['status']=='PASS')
        z=dict(scene=scene,emit=emit,name=first['scene_configuration']['name'],n=len(pairs),left=a.left,right=a.right,left_ms_median=statistics.median(r['left_ms'] for r in pairs),right_ms_median=statistics.median(r['right_ms'] for r in pairs),paired_speedup_geomean=geo,paired_speedup_ci95=[lo,hi],decision=decision,all_pair_directions_same=all(x>1 for x in ratios) or all(x<1 for x in ratios),contract_equal=workload_equal,params_initial_equal=params_equal,initial_state_byte_equal=initial_equal,windowless=windowless,endpoint_finite=finite,suspend_excluded_repeats=contaminated,pairs=pairs,scope='same FlexDemo contract; trajectories and actual neighbor/contact work may differ')
        for key in ['scene_ms','api_ms','wait_ms']:
            z[key]={v:statistics.median(arms[v]['metrics'][key]['mean'] for arms in repeats.values() if arms[v]['status']=='PASS' and not arms[v]['timing_contaminated_by_suspend']) for v in [a.left,a.right]}
        rows.append(z)
    per_repeat=[statistics.mean(x) for _,x in sorted(all_logs_by_repeat.items())];ci=interval(per_repeat)
    summary=dict(suite=a.suite,left=a.left,right=a.right,scenes=len(rows),runs=len(receipts),frames=sum(r['frames'] for r in receipts if r['status']=='PASS'),measured_frames=sum(r['frames']-r['warmup'] for r in receipts if r['status']=='PASS'),equal_scene_geomean=math.exp(statistics.mean(per_repeat)),equal_scene_geomean_ci95=[math.exp(x) if x is not None else None for x in ci],equal_frame_total_left_ms=sum(r['left_ms_median'] for r in rows),equal_frame_total_right_ms=sum(r['right_ms_median'] for r in rows),decisions=dict(collections.Counter(r['decision'] for r in rows)),all_contracts_equal=all(r['contract_equal'] for r in rows),all_initial_params_equal=all(r['params_initial_equal'] for r in rows),all_endpoint_finite=all(r['endpoint_finite'] for r in rows),suspend_exclusions=sum(len(r['suspend_excluded_repeats']) for r in rows),ci_method='two-sided t interval on paired process-level log ratios; n independent process pairs per scene; scene-wise intervals are unadjusted for multiple comparisons',performance_only=True)
    summary.update(replaced_runs=len(replacements),replacement_mapping=replacements,original_clock_flags=[r['name'] for r in originals if r.get('timing_contaminated_by_suspend')],failed_pairs=failed_pairs,excluded_scenes=excluded_scenes,failed_runs=[r['name'] for r in receipts if r['status']=='FAIL'])
    summary['suspend_exclusions']=len(clock_excluded_pairs);summary['clock_excluded_pairs']=clock_excluded_pairs
    repeat_sets=[set(p['repeat'] for p in r['pairs']) for r in rows]
    summary['balanced_repeat_panels']=all(x==repeat_sets[0] for x in repeat_sets)
    summary['equal_scene_geomean']=math.exp(statistics.mean(math.log(r['paired_speedup_geomean']) for r in rows))
    if not summary['balanced_repeat_panels']:
        summary['equal_scene_geomean_ci95']=[None,None]
        summary['aggregate_ci_note']='Unequal repeat panels after exclusions: descriptive equal-scene mean retained, aggregate CI withheld pending complete-block retests.'
    summary['metric']='complete frame' if a.metric=='complete' else 'API request + final Map completion; excludes scene/replay copy'
    try:
        from scipy.stats import t as student
        tests=[]
        for row in rows:
            xs=[p['logratio'] for p in row['pairs']];sd=statistics.stdev(xs);mean=statistics.mean(xs);stat=mean/(sd/math.sqrt(len(xs))) if sd else (0.0 if mean==0 else float('inf'));pv=float(2*student.sf(abs(stat),len(xs)-1));row['p_unadjusted']=pv;tests.append((pv,row))
        previous=0.0
        for index,(pv,row) in enumerate(sorted(tests,key=lambda x:x[0])):
            adjusted=max(previous,min(1.0,pv*(len(tests)-index)));previous=adjusted;row['p_holm']=adjusted;row['holm_decision']=('right-faster' if row['paired_speedup_geomean']>1 else 'left-faster') if adjusted<.05 else 'not-separated-after-Holm'
        summary['holm_decisions']=dict(collections.Counter(r['holm_decision'] for r in rows))
    except ImportError:summary['holm_decisions']='scipy unavailable; unadjusted intervals explicitly labeled'
    summary['selected_arm_runs']=sum(r['variant'] in [a.left,a.right] for r in receipts)
    label=a.suite+('' if (a.left,a.right)==('df','of') else '__'+a.left+'-vs-'+a.right)+('-solver' if a.metric=='solver' else '')
    write(ROOT/'analysis'/f'{label}-scenes.json',rows);write(ROOT/'analysis'/f'{label}-summary.json',summary)
    with (ROOT/'analysis'/f'{label}-scenes.csv').open('w',encoding='utf-8-sig',newline='') as fd:
        fields=['scene','emit','name','n','left_ms_median','right_ms_median','paired_speedup_geomean','paired_speedup_ci95','decision','contract_equal','initial_state_byte_equal'];w=csv.DictWriter(fd,fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    event('paired-analysis',suite=a.suite,summary=summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
