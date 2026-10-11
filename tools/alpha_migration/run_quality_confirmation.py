"""Independent controls/ablation for new deterministic drift or unusually large spread."""
from common import *
here=Path(__file__).parent;job=ROOT/'jobs/quality-confirmation-pipeline.json';write(job,dict(status='WAITING',pid=os.getpid(),started=now()))
try:
    event('quality-confirmation-predeclared',repeats=8,frames=1200,arms=['released DF','no-change control','a06 combined','restricted neighbors','radix','final'],selection='Always D11 scenes3/56; in either backend additionally any nonzero position/velocity drift when both original repeat maxima are zero, or position/velocity cross or candidate-repeat maxima >4x original maxima and >1e-4. This selects investigation only, never an acceptance tolerance.',reason='D11 scene56 differs consistently after120frames while early snapshots match; distinguish original stochastic spread from candidate-induced differences. No automatic acceptance.')
    dependency=ROOT/'jobs/regression-confirmation-pipeline.json'
    while read(dependency)['status'] in ['WAITING','RUNNING']:time.sleep(10)
    assert read(dependency)['status']=='PASS','Review preceding failure before more GPU work'
    write(job,dict(status='RUNNING',pid=os.getpid(),started=now()))
    def run(tool,args,name):
        p=ROOT/'jobs'/f'{name}.json'
        if p.exists() and read(p)['status']=='PASS':return
        command([sys.executable,'-B',here/(tool+'.py'),*args],name,cwd=WS,timeout=14400)
    selections={}
    for api,left,control,suffix in [('d11','df','control-v0',''),('d12','df12','control-v0-d3d12','-d3d12')]:
        final='alpha-migration-final-v1'+suffix;rows=read(ROOT/'analysis'/f'final-quality-{api}-v1__{left}-vs-{final}-quality-assessment.json');selected={3,56} if api=='d11' else set()
        for r in rows:
            pos,vel=r['position_rms'],r['velocity_rms'];deterministic=pos[left+'_self_max']==0 and vel[left+'_self_max']==0
            if deterministic and (pos['cross_max']>0 or vel['cross_max']>0):selected.add(r['scene'])
            for values in [pos,vel]:
                base=values[left+'_self_max'];worst=max(values['cross_max'],values[final+'_self_max'])
                if worst>1e-4 and worst>4*base:selected.add(r['scene'])
        selections[api]=sorted(selected)
        if not selected:continue
        variants=[left,control,'a06-combined-v1'+suffix,'a37-distance-v2'+suffix,'a82-radix-v1'+suffix,final];suite='quality-confirm-'+api+'-v1'
        run('run_matrix',['--suite',suite,'--variants',','.join(variants),'--scenes',','.join(map(str,sorted(selected))),'--frames','1200','--warmup','120','--repeats','8','--capture','1'],suite+'-command')
        comparisons=[(left,control),(left,final),('a06-combined-v1'+suffix,final),('a06-combined-v1'+suffix,'a37-distance-v2'+suffix),('a06-combined-v1'+suffix,'a82-radix-v1'+suffix)]
        for a,b in comparisons:
            for tool in ['quality_analysis','assess_quality','compare_aux_outputs','quality_flags']:run(tool,['--suite',suite,'--left',a,'--right',b],suite+'-'+a+'-'+b+'-'+tool)
        for variant in [left,control]:run('characterize_baseline',['--suite',suite,'--variant',variant],suite+'-'+variant+'-baseline')
    write(ROOT/'evidence/quality-confirmation-selection.json',selections);write(job,dict(status='PASS',pid=os.getpid(),finished=now(),selection=selections,scope='Execution only; unresolved quality flags still require diagnosis or removal of responsible optimization.'))
except BaseException as e:write(job,dict(status='FAIL',pid=os.getpid(),finished=now(),error=str(e)));raise
