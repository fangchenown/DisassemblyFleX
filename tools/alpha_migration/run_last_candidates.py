"""Serialized final independent experiments; safe to resume completed steps."""
from common import *
here=Path(__file__).parent
job=ROOT/'jobs/last-candidates-pipeline.json'
write(job,dict(status='WAITING',pid=os.getpid(),started=now()))
try:
    for suite in ['a37-screen-d11-v1','a37-screen-d12-v1']:
        path=ROOT/'jobs'/f'{suite}-controller.json'
        while not path.exists() or read(path)['status']=='RUNNING':time.sleep(10)
        assert read(path)['status']=='PASS',suite
    write(job,dict(status='RUNNING',pid=os.getpid(),started=now()))
    def run(tool,args,name):
        receipt=ROOT/'jobs'/f'{name}.json'
        if receipt.exists() and read(receipt)['status']=='PASS':return
        command([sys.executable,'-B',here/(tool+'.py'),*args],name,cwd=WS,timeout=7200)
    for api,suffix in [('d11',''),('d12','-d3d12')]:
        for candidate in ['a37-distance-v1','a37-fullrow-v1']:
            run('analyze_primary',['--suite',f'a37-screen-{api}-v1','--left','a06-combined-v1'+suffix,'--right',candidate+suffix],f'{candidate}-{api}-screen-analysis')
    for name,base,factory in [('a39-dead-stream-v1','a06-combined-v1','prepare_a39_dead_stream'),('a42-packed-springs-v1','a39-dead-stream-v1','prepare_a42_packed_springs'),('a82-radix-v1','a06-combined-v1','prepare_a82_radix')]:
        run(factory,['--base',base,'--name',name],name+'-prepare')
        run('build_candidate',['--name',name,'--source',str(ROOT/'proposals'/name)],name+'-build-command')
        if name=='a82-radix-v1':
            run('run_regressions',['--build',name,'--name',name+'-regressions-df-radix','--radix-reference-build','a06-combined-v1'],name+'-regression-command-v2')
        else:run('run_regressions',['--build',name,'--name',name+'-regressions'],name+'-regression-command')
        if name!='a82-radix-v1':run('run_spring_extent_oracle',['--base','a06-combined-v1','--candidate',name,'--name',name+'-spring-oracle'],name+'-spring-command')
        run('audit_shaders',[name],name+'-audit-command')
    for api,suffix in [('d11',''),('d12','-d3d12')]:
        variants=','.join(n+suffix for n in ['a06-combined-v1','a39-dead-stream-v1','a42-packed-springs-v1','a82-radix-v1'])
        run('run_matrix',['--suite','last-screen-'+api+'-v1','--variants',variants,'--scenes','0,4,9,18,23,25,27,28,29,31,33,47,48,52,54,57,60,61,64,65','--frames','1200','--warmup','120','--repeats','4'],'last-screen-'+api+'-command')
        for candidate in ['a39-dead-stream-v1','a42-packed-springs-v1','a82-radix-v1']:
            run('analyze_primary',['--suite','last-screen-'+api+'-v1','--left','a06-combined-v1'+suffix,'--right',candidate+suffix],candidate+'-'+api+'-last-screen-analysis')
    write(job,dict(status='PASS',pid=os.getpid(),finished=now()))
except BaseException as e:
    write(job,dict(status='FAIL',pid=os.getpid(),finished=now(),error=str(e)));raise
