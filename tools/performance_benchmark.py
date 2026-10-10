"""Independent, resumable, lock-screen-safe official FlexDemo performance study.

Never changes a tested DLL or the archived reconstruction evidence. One GPU run
at a time, coordinated with the independent alpha8.2c task's byte-range lock.
"""
import argparse, csv, hashlib, json, msvcrt, os, random, shutil, statistics
import subprocess, sys, time, traceback
from datetime import datetime, timezone
from pathlib import Path
from locksafe_power import SystemRequired, suspend_clock, suspended_ms

WS = Path(__file__).resolve().parents[2]
PROJECT = WS / 'DisassemblyFleX'
ROOT = WS / 'Build/DisassemblyFleXPerformance-20261010'
LEDGER = PROJECT / 'PerformanceExecutionLedger'
DELIVERY = WS / 'Build/DisassemblyFleX-20261009/delivery'
EXE = DELIVERY / 'DisassemblyFlexDemo.exe'
EXT = WS / 'FleX/bin/win64/NvFlexExtReleaseD3D_x64.dll'
CORES = {'reference': WS / 'FleX/bin/win64/NvFlexReleaseD3D_x64.dll',
         'candidate': DELIVERY / 'NvFlexReleaseD3D_x64.dll'}
EXPECTED = {'reference': 'b79e4680dc16b3e5aa47bd653e23c9383380722d35a97af0bdb49623be53118d',
            'candidate': '8e4a8f1bb479f129147855b9656caa0379ccc2a9c91838604d3cae63a1191090'}
def now(): return datetime.now(timezone.utc).isoformat()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, path)
def event(kind, **data):
    LEDGER.mkdir(parents=True, exist_ok=True)
    with (LEDGER/'events.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps(dict(time=now(),kind=kind,**data),ensure_ascii=False)+'\n')
        f.flush(); os.fsync(f.fileno())
def state(**data):
    path=LEDGER/'state.json'
    s=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    s.update(data,updated=now());write(path,s)
def telemetry():
    p=subprocess.run(['nvidia-smi','--query-gpu=name,driver_version,temperature.gpu,utilization.gpu,clocks.sm,clocks.mem,power.draw,pstate','--format=csv,noheader,nounits'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    return dict(time=now(),exit_code=p.returncode,value=p.stdout.decode(errors='replace').strip())
def env_for(temp,core):
    env={k:v for k,v in os.environ.items() if not k.startswith(('OPENFLEX_','OF_','DEMO_'))}
    env.update(TEMP=str(temp),TMP=str(temp),TMPDIR=str(temp),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',DEMO_BATCH='1')
    env['PATH']=str(core.parent)+os.pathsep+str(EXT.parent)+os.pathsep+env['PATH']
    return env
def initialize(manifest_name='inputs.json'):
    for name in ['runs','jobs','evidence','analysis','logs','temp','demo-stage/bin/win64']: (ROOT/name).mkdir(parents=True,exist_ok=True)
    if not (ROOT/'demo-stage/data').exists():shutil.copytree(WS/'FleX/data',ROOT/'demo-stage/data')
    identities={k:dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for k,p in dict(CORES,exe=EXE,ext=EXT).items()}
    for name in CORES:assert identities[name]['sha256']==EXPECTED[name],identities[name]
    assert identities['exe']['sha256']=='d6a2c0f3314996b6112708cfe6e2e10b443480f824dc1ebec248eb64c1f86bee'
    assets={p.relative_to(ROOT/'demo-stage/data').as_posix():sha(p) for p in sorted((ROOT/'demo-stage/data').rglob('*')) if p.is_file()}
    manifest=dict(created=now(),identities=identities,assets=assets,runner_sha256=sha(Path(__file__)))
    old=ROOT/'evidence'/manifest_name
    if old.exists():
        before=json.loads(old.read_text(encoding='utf-8'));assert before['identities']==identities;assert before['assets']==assets
    else:write(old,manifest)
    return manifest
def run_one(suite,mode,scene,repeat,implementation,frames,warmup,profile,capture,order):
    name=f'{suite}-{mode}-s{scene:02d}-r{repeat}-{implementation}'
    run=ROOT/'runs'/name;receipt=run/'job.json'
    if receipt.exists():
        old=json.loads(receipt.read_text(encoding='utf-8'))
        if old['status']=='PASS':return old
        raise RuntimeError('Existing incomplete/failed run requires explicit audit: '+str(receipt))
    run.mkdir();temp=ROOT/'temp'/name;temp.mkdir()
    core=CORES[implementation]
    command=[str(EXE),str(core),str(EXT),mode,str(scene),str(frames),str(run),'0',str(profile),str(capture)]
    job=dict(name=name,suite=suite,mode=mode,scene=scene,repeat=repeat,implementation=implementation,frames=frames,warmup=warmup,profile=profile,capture=capture,order=order,command=command,controller_pid=os.getpid(),status='WAITING_GPU_LOCK',created=now(),core_sha256=sha(core))
    write(receipt,job);state(status='ACTIVE',phase=suite,active_jobs=[dict(controller_pid=os.getpid(),name=name,receipt=str(receipt))])
    lock_path=WS/'Build/OpenFlexAlpha82c-20260928/gpu.lock'
    try:
        with lock_path.open('a+b') as lock:
            while True:
                try:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1);break
                except OSError:time.sleep(.5)
            job['before_gpu']=telemetry();first=suspend_clock();start=time.perf_counter()
            job.update(status='RUNNING',started=now());write(receipt,job)
            with (run/'console.log').open('wb') as log:
                p=subprocess.Popen(command,cwd=ROOT/'demo-stage/bin/win64',env=env_for(temp,core),stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                job['pid']=p.pid;write(receipt,job)
                try:code=p.wait(timeout=900)
                except subprocess.TimeoutExpired:p.kill();p.wait();raise RuntimeError('900 second owned child timeout')
            job.update(exit_code=code,process_wall_ms=(time.perf_counter()-start)*1000,suspended_ms=suspended_ms(first,suspend_clock()),after_gpu=telemetry())
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
        assert code==0,(name,code)
        complete=json.loads((run/'complete.json').read_text());assert complete['frames']==frames and complete['owned_top_level_windows']==0,complete
        modules=(run/'modules.txt').read_text().splitlines();loaded=[x for x in modules if Path(x).name.lower()=='nvflexreleased3d_x64.dll']
        assert len(loaded)==1 and Path(loaded[0]).resolve()==core.resolve(),loaded
        rows=list(csv.DictReader((run/'frames.csv').open()));assert len(rows)==frames
        measured=[r for r in rows if int(r['frame'])>warmup];assert len(measured)==frames-warmup
        metrics={}
        for metric in ['complete_ms','scene_ms','api_ms','wait_ms','gpu_latency_ms','gpu_total_ms']:
            values=[float(r[metric]) for r in measured];sort=sorted(values)
            metrics[metric]=dict(mean=statistics.mean(values),median=statistics.median(values),p95=sort[int(.95*(len(sort)-1))],minimum=min(values),maximum=max(values))
        job.update(status='PASS',finished=now(),no_window_verified=True,loaded_core=loaded[0],complete=complete,metrics=metrics,initial=json.loads((run/'scene.json').read_text()),particles=[min(int(r['particles']) for r in measured),max(int(r['particles']) for r in measured)],capture_files={p.name:sha(p) for p in run.glob('*.bin')},timing_contaminated_by_suspend=abs(job['suspended_ms'])>1)
        write(receipt,job);event('run-complete',name=name,receipt=str(receipt),mean_ms=metrics['complete_ms']['mean'])
        print(json.dumps(dict(name=name,mean_ms=metrics['complete_ms']['mean'],process_ms=job['process_wall_ms']),ensure_ascii=False),flush=True)
        return job
    except BaseException as exc:
        job.update(status='FAIL',finished=now(),error=repr(exc));write(receipt,job);event('run-failed',name=name,error=repr(exc));raise
    finally:state(active_jobs=[])
def main():
    p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--scenes',default=','.join(map(str,range(67))));p.add_argument('--modes',default='d3d11,d3d12');p.add_argument('--repeats',type=int,default=4);p.add_argument('--frames',type=int,default=300);p.add_argument('--warmup',type=int,default=60);p.add_argument('--profile',type=int,default=0);p.add_argument('--capture',type=int,default=0);p.add_argument('--seed',type=int,default=20261010)
    a=p.parse_args();assert a.frames>a.warmup>=30
    initialize();plan=[]
    # Randomize scene/backend order, keep same-scene A/B adjacent, reverse order
    # for each successive independent process pair to balance drift.
    cases=[(m,int(s)) for m in a.modes.split(',') for s in a.scenes.split(',')]
    for repeat in range(a.repeats):
        random.Random(a.seed+repeat).shuffle(cases)
        for index,(mode,scene) in enumerate(cases):
            order=['reference','candidate'] if (scene+repeat)%2==0 else ['candidate','reference']
            for implementation in order:plan.append(dict(mode=mode,scene=scene,repeat=repeat,implementation=implementation,order=order))
    plan_path=ROOT/'jobs'/f'{a.suite}-plan.json';plan_info=dict(arguments=vars(a),runs=plan)
    if plan_path.exists():assert json.loads(plan_path.read_text())==plan_info
    else:write(plan_path,plan_info)
    event('suite-start',suite=a.suite,pid=os.getpid(),runs=len(plan));write(ROOT/'jobs'/f'{a.suite}-controller.json',dict(pid=os.getpid(),status='RUNNING',plan=str(plan_path),started=now()))
    with SystemRequired():
        for entry in plan:run_one(a.suite,frames=a.frames,warmup=a.warmup,profile=a.profile,capture=a.capture,**entry)
    initialize() # Asset and binary immutability check after completion.
    write(ROOT/'jobs'/f'{a.suite}-controller.json',dict(pid=os.getpid(),status='PASS',finished=now(),runs=len(plan)))
    event('suite-complete',suite=a.suite,runs=len(plan));state(phase='ANALYZE_'+a.suite,active_jobs=[])
if __name__=='__main__':main()
