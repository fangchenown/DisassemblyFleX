"""Frozen three-way official FlexDemo regression/performance benchmark."""
import argparse,os,json,random
import fix_task as task
import performance_benchmark as b
import ledger
def configure(build):
    b.ROOT=task.ROOT;b.LEDGER=task.LEDGER
    b.EXE=b.DELIVERY/'DisassemblyFlexDemo.exe'
    receipt=json.loads((task.ROOT/'evidence'/f'{build}-build.json').read_text(encoding='utf-8'))
    b.CORES={'reference':b.WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll','legacy':b.DELIVERY/'NvFlexReleaseD3D_x64.dll','candidate':task.ROOT/'builds'/build/'NvFlexReleaseD3D_x64.dll'}
    b.EXPECTED={'reference':'b79e4680dc16b3e5aa47bd653e23c9383380722d35a97af0bdb49623be53118d','legacy':'8e4a8f1bb479f129147855b9656caa0379ccc2a9c91838604d3cae63a1191090','candidate':receipt['sha256']}
    # Main and regression controllers share the ledger without erasing each
    # other's active jobs. All actual GPU execution still holds one shared lock.
    def checkpoint(**data):
        def change(s):
            if 'active_jobs' in data:
                s['active_jobs']=[j for j in s.get('active_jobs',[]) if j.get('controller_pid')!=os.getpid()]+data['active_jobs']
            s.update({k:v for k,v in data.items() if k!='active_jobs'});s['updated']=b.now()
        ledger.mutate_state(change)
    b.state=checkpoint
    return b
def main():
    p=argparse.ArgumentParser();p.add_argument('--build',default='final-v2');p.add_argument('--suite',required=True);p.add_argument('--scenes',default=','.join(map(str,range(67))));p.add_argument('--modes',default='d3d11,d3d12');p.add_argument('--frames',type=int,default=300);p.add_argument('--warmup',type=int,default=60);p.add_argument('--repeats',type=int,default=4);p.add_argument('--emit',action='store_true');p.add_argument('--profile',type=int,default=0);a=p.parse_args();configure(a.build);b.initialize('inputs-'+a.build+'.json')
    if a.emit:
        original=b.env_for
        def environment(temp,core):
            env=original(temp,core);env['DEMO_EMIT']='1';return env
        b.env_for=environment
    cases=[(m,int(s)) for m in a.modes.split(',') for s in a.scenes.split(',')];plan=[]
    for repeat in range(a.repeats):
        random.Random(20261010+repeat).shuffle(cases)
        for mode,scene in cases:
            order=['reference','legacy','candidate'] if mode=='d3d12' else ['reference','candidate']
            shift=(scene+repeat)%len(order);order=order[shift:]+order[:shift]
            if repeat%2:order.reverse()
            for implementation in order:plan.append(dict(mode=mode,scene=scene,repeat=repeat,implementation=implementation,order=order))
    planfile=b.ROOT/'jobs'/f'{a.suite}-plan.json';data=dict(arguments=vars(a),runs=plan)
    if planfile.exists():assert json.loads(planfile.read_text())==data
    else:b.write(planfile,data)
    control=b.ROOT/'jobs'/f'{a.suite}-controller.json';b.write(control,dict(pid=os.getpid(),status='RUNNING',started=b.now(),plan=str(planfile),extra_environment={'DEMO_EMIT':'1'} if a.emit else {}))
    b.event('fix-suite-start',suite=a.suite,runs=len(plan),build=a.build)
    with b.SystemRequired():
        for entry in plan:b.run_one(a.suite,frames=a.frames,warmup=a.warmup,profile=a.profile,capture=0,**entry)
    b.initialize('inputs-'+a.build+'.json');b.write(control,dict(pid=os.getpid(),status='PASS',finished=b.now(),runs=len(plan),plan=str(planfile),extra_environment={'DEMO_EMIT':'1'} if a.emit else {}));b.event('fix-suite-complete',suite=a.suite,runs=len(plan))
if __name__=='__main__':main()
