"""Independent predeclared follow-up for apparent per-scene slowdowns."""
from common import *
here=Path(__file__).parent;job=ROOT/'jobs/regression-confirmation-pipeline.json';write(job,dict(status='WAITING',pid=os.getpid(),started=now()))
try:
    event('regression-confirmation-predeclared',scenes={'d11':[17,31],'d12':[31,33,44]},repeats=8,frames=2400,arms=['released DF','a06 cumulative CPU/spring base','restricted neighbors only','radix only','final combination'],reason='Fresh confirmation of negative point estimates, even though none separated after67-scene Holm; retain initial whole-suite measurements.')
    dependency=ROOT/'jobs/final-validation-pipeline.json'
    while read(dependency)['status'] in ['WAITING','RUNNING']:time.sleep(10)
    assert read(dependency)['status']=='PASS','Review final pipeline failure before additional experiments'
    write(job,dict(status='RUNNING',pid=os.getpid(),started=now()))
    def run(tool,args,name):
        p=ROOT/'jobs'/f'{name}.json'
        if p.exists() and read(p)['status']=='PASS':return
        command([sys.executable,'-B',here/(tool+'.py'),*args],name,cwd=WS,timeout=7200)
    for api,left,suffix,scenes in [('d11','df','','17,31'),('d12','df12','-d3d12','31,33,44')]:
        base='a06-combined-v1'+suffix;right='alpha-migration-final-v1'+suffix;others=['a37-distance-v2'+suffix,'a82-radix-v1'+suffix];suite='regression-confirm-'+api+'-v1'
        run('run_matrix',['--suite',suite,'--variants',','.join([left,base,*others,right]),'--scenes',scenes,'--frames','2400','--warmup','240','--repeats','8'],suite+'-command')
        run('retest_clock_blocks',['--suite',suite,'--name',suite+'-clock'],suite+'-clock-command')
        for a,b in [(left,right),(base,right),(base,others[0]),(base,others[1])]:run('analyze_primary',['--suite',suite,'--left',a,'--right',b],suite+'-'+a+'-'+b+'-analysis')
        profile='regression-attribution-'+api+'-v1'
        run('run_matrix',['--suite',profile,'--variants',','.join([left,base,*others,right]),'--scenes',scenes,'--frames','360','--warmup','60','--repeats','2','--profile','1'],profile+'-command')
        for a,b in [(left,right),(base,right),(base,others[0]),(base,others[1])]:run('analyze_gpu_details',['--suite',profile,'--left',a,'--right',b],profile+'-'+a+'-'+b+'-analysis')
    write(job,dict(status='PASS',pid=os.getpid(),finished=now(),scope='Requires explicit interpretation; original whole-suite results preserved.'))
except BaseException as e:write(job,dict(status='FAIL',pid=os.getpid(),finished=now(),error=str(e)));raise
