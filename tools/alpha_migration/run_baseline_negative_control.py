"""Additional original/no-change variability evidence, declared before running."""
from common import *
here=Path(__file__).parent;job=ROOT/'jobs/baseline-variability-pipeline.json';write(job,dict(status='RUNNING',pid=os.getpid(),started=now()))
try:
    def run(tool,args,name):
        p=ROOT/'jobs'/f'{name}.json'
        if p.exists() and read(p)['status']=='PASS':return
        command([sys.executable,'-B',here/(tool+'.py'),*args],name,cwd=WS,timeout=7200)
    event('baseline-variability-predeclared',protocol=str(LEDGER/'02_BASELINE_VARIABILITY_ADDENDUM.txt'),sha256=sha(LEDGER/'02_BASELINE_VARIABILITY_ADDENDUM.txt'),scenes=[0,23,25,27,28,64],repeats=8,frames=1200,candidates_included=False)
    for api,left,right in [('d11','df','control-v0'),('d12','df12','control-v0-d3d12')]:
        suite='baseline-variability-'+api+'-v1'
        run('run_matrix',['--suite',suite,'--variants',left+','+right,'--scenes','0,23,25,27,28,64','--frames','1200','--warmup','120','--repeats','8','--capture','1'],suite+'-command')
        for tool in ['quality_analysis','assess_quality','compare_aux_outputs','quality_flags']:run(tool,['--suite',suite,'--left',left,'--right',right],suite+'-'+tool)
        for variant in [left,right]:run('characterize_baseline',['--suite',suite,'--variant',variant],suite+'-'+variant+'-envelope')
    write(job,dict(status='PASS',pid=os.getpid(),finished=now()))
except BaseException as e:write(job,dict(status='FAIL',pid=os.getpid(),finished=now(),error=str(e)));raise
