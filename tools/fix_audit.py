"""Final acceptance audit for the repaired, frozen DLL and final test suites."""
import json,csv,collections
import fix_benchmark as fix
from fix_analyze import load
EXPECTED={'main-v2':1340,'emit-v2':60,'long-v2':25,'context-v2':54,'gpu-v2':54}
def main():
    b=fix.configure('final-v2');issues=[];summary={};all_runs=[];outputs={};deterministic_legacy_corrections=[]
    for suite,expected in EXPECTED.items():
        controller=json.loads((b.ROOT/'jobs'/f'{suite}-controller.json').read_text(encoding='utf-8'));assert controller['status']=='PASS',(suite,controller)
        runs,replacements=load(suite);assert len(runs)==expected,(suite,len(runs),expected);all_runs+=runs
        for j in runs:
            assert j['core_sha256']==b.EXPECTED[j['implementation']],j['name']
            assert j['no_window_verified'] and not j['timing_contaminated_by_suspend'],j['name']
            assert j['complete']['frames']==j['frames'] and j['complete']['owned_top_level_windows']==0
            final=list(csv.DictReader((b.ROOT/'runs'/j['name']/'frames.csv').open()))[-1];assert int(final['nonfinite'])==0,j['name']
        summary[suite]=dict(effective_runs=len(runs),frames=sum(j['frames'] for j in runs),replaced_groups=len(replacements))
        if suite in ['context-v2','gpu-v2']:continue
        analysis=json.loads((b.ROOT/'analysis'/f'{suite}.json').read_text(encoding='utf-8'))
        outputs[suite]={}
        for comparison in sorted({a['comparison'] for a in analysis['audits']}):
            rows=[a for a in analysis['audits'] if a['comparison']==comparison]
            for a in rows:
                if not a['metadata_equal'] or a['initial_hash_mismatches'] or a['activity_differing_frames'] or a['clock_flag'] or any(a['nonfinite_final']):issues.append(a)
                s=a['state']
                assert all(not value.get('missing_candidate') for value in a['final_outputs'].values()),(suite,a['scene'],'Missing output snapshot')
                if not s['bytes_equal']:
                    assert s.get('ids_phases_equal',False),(suite,a['mode'],a['scene'],'Discrete mismatch')
                    assert s.get('inverse_mass',{}).get('max_abs',0)==0,(suite,a['scene'],'Inverse mass changed')
                    assert s.get('positions',{}).get('nonfinite_differences',0)==0 and s.get('velocities',{}).get('nonfinite_differences',0)==0
                    peers=a['baseline_repeat_drift']
                    if peers and all(p['bytes_equal'] for p in peers):
                        # A stable old output difference is not excused as
                        # nondeterminism. It must instead match the real oracle.
                        oracle=next((x for x in analysis['audits'] if x['mode']==a['mode'] and x['scene']==a['scene'] and x['repeat']==a['repeat'] and x['comparison']=='candidate/reference'),None)
                        assert comparison=='candidate/legacy' and oracle and oracle['state']['bytes_equal'],(suite,a['scene'],'Mismatch against repeatably exact oracle')
                        deterministic_legacy_corrections.append(dict(suite=suite,mode=a['mode'],scene=a['scene'],repeat=a['repeat'],candidate_equals_original=True,legacy_equals_original=False))
            outputs[suite][comparison]=dict(pairs=len(rows),exact=sum(a['state']['bytes_equal'] for a in rows),all_final_snapshots_exact=sum(all(v['bytes_equal'] for v in a['final_outputs'].values()) for a in rows),nonexact_scenes=sorted({a['scene'] for a in rows if not a['state']['bytes_equal']}),max_position_difference=max((a['state'].get('positions',{}).get('max_abs',0) for a in rows),default=0))
    assert not issues,issues
    regression=json.loads((b.ROOT/'evidence/regression-final-v2/results.json').read_text(encoding='utf-8'));assert len(regression)==13 and all(r['passed'] for r in regression)
    particles=json.loads((b.ROOT/'evidence/regression-final-v2/particles/results.json').read_text(encoding='utf-8'));assert len(particles)==33 and all(r['equal'] for r in particles)
    lifetime=json.loads((b.ROOT/'evidence/final-v2-lifetime.json').read_text(encoding='utf-8'));assert lifetime['status']=='PASS' and not lifetime['pool_growth_after_warmup']
    shader=json.loads((b.ROOT/'evidence/shader-audit-final-v2.json').read_text(encoding='utf-8'));assert shader['all_programs_equal'] and all(x==84 for x in shader['containers'].values())
    # Formal runtime and shader inputs must still match the exact built snapshot.
    snapshot=b.ROOT/'source-snapshots/final-v2';source_changes=[]
    for top in ['src','include','shaders','cmake']:
        for p in (snapshot/top).rglob('*'):
            if p.is_file() and b.sha(p)!=b.sha(b.PROJECT/p.relative_to(snapshot)):source_changes.append(str(p.relative_to(snapshot)))
    assert not source_changes,source_changes
    b.initialize('inputs-final-v2.json')
    qpath=b.ROOT/'evidence/quality-replacements.json';quality=json.loads(qpath.read_text(encoding='utf-8')) if qpath.exists() else []
    telemetry=[]
    for j in all_runs:
        raw=j['after_gpu']['value'].split(', ')
        if len(raw)==8:telemetry.append(dict(temperature=float(raw[2]),sm_mhz=float(raw[4]),watts=float(raw[6])))
    result=dict(status='PASS',created=b.now(),candidate=str(b.CORES['candidate']),candidate_sha256=b.EXPECTED['candidate'],suites=summary,effective_flexdemo_runs=len(all_runs),effective_flexdemo_frames=sum(j['frames'] for j in all_runs),quality_replacements=quality,regression_gates=13,exact_particle_cases=33,lifetime=lifetime,shader_programs_equal=84,formal_runtime_matches_snapshot=True,output_summary=outputs,deterministic_legacy_corrections=deterministic_legacy_corrections,issues=[],telemetry_ranges={k:[min(x[k] for x in telemetry),max(x[k] for x in telemetry)] for k in ['temperature','sm_mhz','watts']})
    b.write(b.ROOT/'evidence/FINAL_VALIDATION.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
