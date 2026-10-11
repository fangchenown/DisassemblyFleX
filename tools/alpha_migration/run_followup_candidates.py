"""Finish predeclared clock replacements and independent neighbor quality gates."""
from common import *
here=Path(__file__).parent;job=ROOT/'jobs/followup-candidates-pipeline.json';write(job,dict(status='WAITING',pid=os.getpid(),started=now()))
try:
    path=ROOT/'jobs/last-candidates-pipeline.json'
    while read(path)['status'] in ['WAITING','RUNNING']:time.sleep(10)
    assert read(path)['status']=='PASS','Inspect preserved prior pipeline failure before resuming'
    write(job,dict(status='RUNNING',pid=os.getpid(),started=now()))
    def run(tool,args,name):
        path=ROOT/'jobs'/f'{name}.json'
        if path.exists() and read(path)['status']=='PASS':return
        command([sys.executable,'-B',here/(tool+'.py'),*args],name,cwd=WS,timeout=7200)
    for api,suffix in [('d11',''),('d12','-d3d12')]:
        for family,candidates in [('a37',['a37-distance-v1','a37-fullrow-v1']),('last',['a39-dead-stream-v1','a42-packed-springs-v1','a82-radix-v1'])]:
            suite=f'{family}-screen-{api}-v1'
            run('retest_clock_blocks',['--suite',suite,'--name',f'{family}-screen-{api}-clock-v1'],f'{family}-{api}-clock-command')
            for candidate in candidates:run('analyze_primary',['--suite',suite,'--left','a06-combined-v1'+suffix,'--right',candidate+suffix],candidate+'-'+api+'-replaced-analysis')
        suite='a37-distance-quality-'+api+'-v1';left='a06-combined-v1'+suffix;right='a37-distance-v1'+suffix
        run('run_matrix',['--suite',suite,'--variants',left+','+right,'--scenes','0,9,23,25,27,28,47,64,65','--frames','1200','--warmup','120','--repeats','3','--capture','1'],suite+'-command')
        for tool in ['quality_analysis','assess_quality','compare_aux_outputs']:run(tool,['--suite',suite,'--left',left,'--right',right],suite+'-'+tool)
    suite='a37-attribution-d12-v1';left='a06-combined-v1-d3d12'
    run('run_matrix',['--suite',suite,'--variants',left+',a37-distance-v1-d3d12,a37-fullrow-v1-d3d12','--scenes','9,33,52','--frames','360','--warmup','60','--repeats','2','--profile','1'],suite+'-command')
    for candidate in ['a37-distance-v1-d3d12','a37-fullrow-v1-d3d12']:run('analyze_gpu_details',['--suite',suite,'--left',left,'--right',candidate],suite+'-'+candidate+'-analysis')
    write(job,dict(status='PASS',pid=os.getpid(),finished=now()))
except BaseException as e:write(job,dict(status='FAIL',pid=os.getpid(),finished=now(),error=str(e)));raise
