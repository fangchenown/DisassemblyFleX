"""Resumable, one-GPU-at-a-time, paired FlexDemo experiments."""
import argparse,csv,statistics,random,sys,traceback,math,ctypes
from common import *
from locksafe_power import SystemRequired,suspend_clock,suspended_ms

def telemetry():
    p=subprocess.run(['nvidia-smi','--query-gpu=name,driver_version,temperature.gpu,utilization.gpu,clocks.sm,clocks.mem,power.draw,pstate','--format=csv,noheader,nounits'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    return dict(time=now(),exit_code=p.returncode,value=p.stdout.decode(errors='replace').strip())
def get_variants():
    base=read(ROOT/'evidence/baselines.json');variants={}
    for key,source,mode in [('df','df','df-d3d11'),('df12','df','df-d3d12'),('nv','nv','df-d3d11'),('nv12','nv','df-d3d12')]:
        v=base[source];variants[key]=dict(core=v['core']['path'],ext=v['ext']['path'],core_sha256=v['core']['sha256'],ext_sha256=v['ext']['sha256'],mode=mode,environment={})
    path=ROOT/'evidence/variants.json'
    if path.exists():variants.update(read(path))
    return variants

def run_one(suite,variant,scene,repeat,frames,warmup,profile,capture,emit,order,extra=None):
    variants=get_variants();v=variants[variant];exe=Path(v.get('harness',read(ROOT/'evidence/inputs.json')['executable']['path']));core=Path(v['core']);ext=Path(v['ext']);name=f'{suite}-s{scene:02d}-e{int(emit)}-r{repeat}-{variant}';run=ROOT/'runs'/name;receipt=run/'receipt.json'
    assert not v.get('diagnostic_only') or capture or profile,'Diagnostic DLL cannot be used as a production timing arm'
    if receipt.exists():
        old=read(receipt)
        if old['status']=='PASS':return old
        raise RuntimeError('Audit existing incomplete/failed run before resuming: '+str(receipt))
    run.mkdir();envextra=dict(DEMO_BATCH='1');envextra.update(v.get('environment',{}));envextra.update(extra or {})
    if emit:envextra['DEMO_EMIT']='1'
    envextra={k:str(value).replace('{run}',str(run)) for k,value in envextra.items()}
    env=clean_env(ROOT/'temp'/name,envextra);env['PATH']=str(core.parent)+os.pathsep+str(ext.parent)+os.pathsep+str(WS/'FleX/bin/win64')+os.pathsep+env['PATH']
    assert sha(core)==v['core_sha256'] and sha(ext)==v['ext_sha256']
    cmd=[str(exe),str(core),str(ext),v['mode'],str(scene),str(frames),str(run),'0',str(profile),str(capture)]
    job=dict(name=name,suite=suite,variant=variant,scene=scene,repeat=repeat,frames=frames,warmup=warmup,profile=profile,capture=capture,emit=emit,order=order,command=cmd,status='WAITING',created=now(),controller_pid=os.getpid(),core_sha256=sha(core),ext_sha256=sha(ext),harness_sha256=sha(exe),environment=envextra)
    job['diagnostic_only']=bool(v.get('diagnostic_only'));write(receipt,job);state(phase=suite,active_jobs=[dict(name=name,controller_pid=os.getpid(),receipt=str(receipt))])
    try:
        with gpu_lock():
            job['before_gpu']=telemetry();first=suspend_clock();begin=time.perf_counter();job.update(status='RUNNING',started=now())
            with (run/'console.log').open('wb') as log:
                p=subprocess.Popen(cmd,cwd=ROOT/'demo-stage/bin/win64',env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job['pid']=p.pid
                if envextra.get('FLEXPERF_PROCESS_AFFINITY'):
                    mask=int(envextra['FLEXPERF_PROCESS_AFFINITY'],0);kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];kernel.SetProcessAffinityMask.restype=ctypes.c_int
                    if not kernel.SetProcessAffinityMask(int(p._handle),mask):p.kill();p.wait();raise ctypes.WinError(ctypes.get_last_error())
                    job['process_affinity_mask']=mask
                write(receipt,job)
                try:code=p.wait(timeout=900)
                except subprocess.TimeoutExpired:p.kill();p.wait();code=-999
            job.update(exit_code=code,process_ms=(time.perf_counter()-begin)*1000,suspended_ms=suspended_ms(first,suspend_clock()),after_gpu=telemetry())
        assert code==0,(name,code)
        complete=read(run/'complete.json');assert complete['frames']==frames and complete['owned_top_level_windows']==0,complete
        modules=(run/'modules.txt').read_text(encoding='utf-8',errors='replace').splitlines();loaded=[x for x in modules if Path(x).name.lower()==core.name.lower()];assert len(loaded)==1 and Path(loaded[0]).resolve()==core.resolve(),loaded
        loaded_ext=[x for x in modules if Path(x).name.lower()==ext.name.lower()];assert len(loaded_ext)==1 and Path(loaded_ext[0]).resolve()==ext.resolve(),loaded_ext
        rows=list(csv.DictReader((run/'frames.csv').open()));assert len(rows)==frames;observed=[r for r in rows if int(r['frame'])>warmup]
        metrics={}
        for k in ['complete_ms','scene_ms','api_ms','wait_ms','gpu_latency_ms','gpu_total_ms']:
            values=[float(r[k]) for r in observed];assert all(math.isfinite(x) for x in values);ordered=sorted(values);metrics[k]=dict(mean=statistics.mean(values),median=statistics.median(values),stdev=statistics.stdev(values),p95=ordered[int(.95*(len(values)-1))],min=min(values),max=max(values))
        contracts=list(csv.DictReader((run/'contract.csv').open()));assert len(contracts)==frames
        environment=dict(line.split('=',1) for line in (run/'effective-environment.txt').read_text(encoding='utf-8',errors='replace').splitlines() if '=' in line)
        job.update(status='PASS',finished=now(),complete=complete,metrics=metrics,scene_configuration=read(run/'scene.json'),loaded_core=loaded[0],loaded_ext=loaded_ext[0],effective_environment=environment,particles=[min(int(r['particles']) for r in rows),max(int(r['particles']) for r in rows)],quality_observed=bool(capture),quality_mode='all-frames' if capture else 'last-frame-only',endpoint_nonfinite=int(rows[-1]['nonfinite']),nonfinite_observed=sum(int(r['nonfinite']) for r in rows) if capture else None,timing_contaminated_by_suspend=abs(job['suspended_ms'])>1,files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in run.iterdir() if p.is_file() and p.name!='receipt.json'})
        assert job['endpoint_nonfinite']==0 and (job['nonfinite_observed'] is None or job['nonfinite_observed']==0),'Nonfinite simulation state'
        write(receipt,job);event('run-pass',name=name,mean_ms=metrics['complete_ms']['mean'],nonfinite=job['nonfinite_observed']);print(json.dumps(dict(name=name,mean_ms=metrics['complete_ms']['mean'],process_s=job['process_ms']/1000,particles=job['particles']),ensure_ascii=False),flush=True);return job
    except BaseException as e:
        job.update(status='FAIL',finished=now(),error=repr(e));write(receipt,job);event('run-fail',name=name,error=repr(e));raise
    finally:state(active_jobs=[])

def main():
    p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--scenes',default=','.join(map(str,range(67))));p.add_argument('--variants',default='df,of');p.add_argument('--frames',type=int,default=1200);p.add_argument('--warmup',type=int,default=120);p.add_argument('--repeats',type=int,default=5);p.add_argument('--profile',type=int,default=0);p.add_argument('--capture',type=int,default=0);p.add_argument('--emit',action='store_true');p.add_argument('--env',action='append',default=[]);a=p.parse_args();assert a.frames>a.warmup>=30
    continue_failures=os.environ.get('FLEXPERF_CONTINUE_FAILED_CASES')=='1'
    plan=[];names=a.variants.split(',');extra=dict(x.split('=',1) for x in a.env)
    for repeat in range(a.repeats):
        scenes=list(map(int,a.scenes.split(',')));random.Random(20261010+repeat).shuffle(scenes)
        for scene in scenes:
            if len(names)==2:order=names if (scene+repeat)%2==0 else names[::-1]
            else:
                shift=(scene+repeat)%len(names);order=names[shift:]+names[:shift]
                if repeat%2:order=order[::-1]
            for name in order:plan.append(dict(variant=name,scene=scene,repeat=repeat,order=order))
    pp=ROOT/'jobs'/f'{a.suite}-plan.json';payload=dict(arguments=vars(a),runs=plan)
    if pp.exists():assert read(pp)==payload
    else:write(pp,payload)
    driver=ROOT/'jobs'/f'{a.suite}-driver.py'
    if not driver.exists():shutil.copy2(Path(__file__),driver)
    if continue_failures:shutil.copy2(Path(__file__),ROOT/'jobs'/f'{a.suite}-driver-continue.py')
    controller=ROOT/'jobs'/f'{a.suite}-controller.json';write(controller,dict(status='RUNNING',pid=os.getpid(),started=now(),plan=str(pp),runs=len(plan)));event('suite-start',suite=a.suite,runs=len(plan))
    try:
        failed=[]
        with SystemRequired():
            for r in plan:
                receipt=ROOT/'runs'/f'{a.suite}-s{r["scene"]:02d}-e{int(a.emit)}-r{r["repeat"]}-{r["variant"]}'/'receipt.json'
                if continue_failures and receipt.exists() and read(receipt)['status']=='FAIL':failed.append(read(receipt)['name']);continue
                try:run_one(a.suite,frames=a.frames,warmup=a.warmup,profile=a.profile,capture=a.capture,emit=a.emit,extra=extra,**r)
                except Exception:
                    if not continue_failures:raise
                    failed.append(read(receipt)['name']);continue
        status='COMPLETE_WITH_FAILURES' if failed else 'PASS'
        write(controller,dict(status=status,pid=os.getpid(),finished=now(),runs=len(plan),failed_cases=failed));event('suite-complete',suite=a.suite,status=status,runs=len(plan),failed_cases=failed)
    except BaseException as e:write(controller,dict(status='FAIL',pid=os.getpid(),finished=now(),error=repr(e)));raise
if __name__=='__main__':main()
