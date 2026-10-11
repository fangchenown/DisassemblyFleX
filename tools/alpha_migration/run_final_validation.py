"""Predeclared whole-project acceptance against frozen released/no-change controls."""
from common import *
here=Path(__file__).parent;candidate='alpha-migration-final-v1';job=ROOT/'jobs/final-validation-pipeline.json';write(job,dict(status='WAITING',pid=os.getpid(),candidate=candidate,started=now()))
try:
    dependency=ROOT/'jobs/baseline-variability-pipeline.json'
    while read(dependency)['status'] in ['WAITING','RUNNING']:time.sleep(10)
    assert read(dependency)['status']=='PASS','Inspect independent baseline characterization first'
    assert read(ROOT/'evidence'/f'{candidate}-shader-audit.json')['status']=='PASS'
    assert all(r['status']=='PASS' for r in read(ROOT/'runs/final-v1-regressions/results.json'))
    for name in ['spring','neighbor','radix']:assert read(ROOT/'runs'/f'final-v1-{name}-oracle/result.json')['status']=='PASS'
    write(job,dict(status='RUNNING',pid=os.getpid(),candidate=candidate,started=now()))
    def run(tool,args,name):
        p=ROOT/'jobs'/f'{name}.json'
        if p.exists() and read(p)['status']=='PASS':return
        command([sys.executable,'-B',here/(tool+'.py'),*args],name,cwd=WS,timeout=14400)
    def performance(suite,variants,frames=1200,warmup=120,repeats=4,scenes=None,emit=False):
        args=['--suite',suite,'--variants',','.join(variants),'--frames',str(frames),'--warmup',str(warmup),'--repeats',str(repeats)]
        if scenes:args+=['--scenes',scenes]
        if emit:args+=['--emit']
        run('run_matrix',args,suite+'-command')
        run('retest_clock_blocks',['--suite',suite,'--name',suite+'-clock'],suite+'-clock-command')
        for left in variants[:-1]:run('analyze_primary',['--suite',suite,'--left',left,'--right',variants[-1]],suite+'-'+left+'-analysis')
    def quality(suite,left,right,frames=1200,scenes=None,emit=False):
        args=['--suite',suite,'--variants',left+','+right,'--frames',str(frames),'--warmup','120','--repeats','3','--capture','1']
        if scenes:args+=['--scenes',scenes]
        if emit:args+=['--emit']
        run('run_matrix',args,suite+'-command')
        for tool in ['quality_analysis','assess_quality','compare_aux_outputs','quality_flags']:run(tool,['--suite',suite,'--left',left,'--right',right],suite+'-'+tool)
    for api,left,control,suffix in [('d11','df','control-v0',''),('d12','df12','control-v0-d3d12','-d3d12')]:
        right=candidate+suffix;suite='final-primary-'+api+'-v1'
        performance(suite,[left,control,right])
        run('analyze_primary',['--suite',suite,'--left',left,'--right',control],suite+'-no-change-control-analysis')
    for api,left,suffix in [('d11','df',''),('d12','df12','-d3d12')]:
        right=candidate+suffix;quality('final-quality-'+api+'-v1',left,right)
        performance('final-emission-'+api+'-v1',[left,right],frames=1800,warmup=180,repeats=4,scenes='36,39,40,64,65,66',emit=True)
        quality('final-emission-quality-'+api+'-v1',left,right,frames=1800,scenes='36,39,40,64,65,66',emit=True)
        quality('final-long-'+api+'-v1',left,right,frames=6000,scenes='0,9,25,27,47,65')
        suite='final-cpu-'+api+'-v1'
        run('run_matrix',['--suite',suite,'--variants',left+','+right,'--scenes','0,9,25,27,33,47,64,65','--frames','1200','--warmup','120','--repeats','4','--profile','4'],suite+'-command')
        run('retest_clock_blocks',['--suite',suite,'--name',suite+'-clock'],suite+'-clock-command')
        run('analyze_cpu_counters',['--suite',suite,'--left',left,'--right',right],suite+'-analysis')
    write(job,dict(status='PASS',pid=os.getpid(),candidate=candidate,finished=now(),scope='Execution completed. Numerical flags, nondeterminism, regressions and publication still require explicit review.'))
except BaseException as e:write(job,dict(status='FAIL',pid=os.getpid(),candidate=candidate,finished=now(),error=str(e)));raise
