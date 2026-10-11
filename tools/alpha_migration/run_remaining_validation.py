"""Independent confirmation and final candidate quality before composition."""
from common import *
here=Path(__file__).parent;job=ROOT/'jobs/remaining-validation-pipeline.json';write(job,dict(status='RUNNING',pid=os.getpid(),started=now()))
try:
    def run(tool,args,name):
        path=ROOT/'jobs'/f'{name}.json'
        if path.exists() and read(path)['status']=='PASS':return
        command([sys.executable,'-B',here/(tool+'.py'),*args],name,cwd=WS,timeout=7200)
    for api,suffix in [('d11',''),('d12','-d3d12')]:
        left='a06-combined-v1'+suffix;right='a37-distance-v2'+suffix;suite='a37-v2-confirm-'+api+'-v1'
        run('run_matrix',['--suite',suite,'--variants',left+','+right,'--scenes','9,47','--frames','2400','--warmup','240','--repeats','6'],suite+'-command')
        run('retest_clock_blocks',['--suite',suite,'--name',suite+'-clock'],suite+'-clock-command')
        run('analyze_primary',['--suite',suite,'--left',left,'--right',right],suite+'-analysis')
        suite='remaining-quality-'+api+'-v1'
        run('run_matrix',['--suite',suite,'--variants',left+','+right+',a82-radix-v1'+suffix,'--scenes','0,9,23,25,27,28,33,47,64,65','--frames','1200','--warmup','120','--repeats','3','--capture','1'],suite+'-command')
        for candidate in ['a37-distance-v2','a82-radix-v1']:
            for tool in ['quality_analysis','assess_quality','compare_aux_outputs','quality_flags']:
                run(tool,['--suite',suite,'--left',left,'--right',candidate+suffix],suite+'-'+candidate+'-'+tool)
        suite='a82-attribution-'+api+'-v1';right='a82-radix-v1'+suffix
        run('run_matrix',['--suite',suite,'--variants',left+','+right,'--scenes','25,33,64','--frames','360','--warmup','60','--repeats','2','--profile','1'],suite+'-command')
        run('analyze_gpu_details',['--suite',suite,'--left',left,'--right',right],suite+'-analysis')
    write(job,dict(status='PASS',pid=os.getpid(),finished=now()))
except BaseException as e:write(job,dict(status='FAIL',pid=os.getpid(),finished=now(),error=str(e)));raise
