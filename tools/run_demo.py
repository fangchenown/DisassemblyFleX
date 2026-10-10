"""Run official FlexDemo physics without an interactive desktop or render window."""
import argparse,hashlib,json,msvcrt,os,shutil,subprocess,time,uuid
from pathlib import Path
from ledger import add_job,remove_job,PROJECT,LEDGER,write_json,event,now
from locksafe_power import SystemRequired,suspend_clock,suspended_ms
WS=PROJECT.parent;OUTPUT=WS/'Build/DisassemblyFleX-20261009'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--build',default='headless-baseline-v1');parser.add_argument('--implementation',choices=['reference','candidate'],required=True)
    parser.add_argument('--scene',type=int,required=True);parser.add_argument('--frames',type=int,default=30)
    parser.add_argument('--name',required=True);parser.add_argument('--mode',choices=['d3d11','d3d11-generic','d3d12'],default='d3d11')
    args=parser.parse_args()
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.name):raise ValueError(args.name)
    build=OUTPUT/'builds'/args.build;exe=build/'DisassemblyFlexDemo.exe'
    core=WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll' if args.implementation=='reference' else build/'NvFlexReleaseD3D_x64.dll'
    ext=WS/'FleX/bin/win64/NvFlexExtReleaseD3D_x64.dll'
    run=OUTPUT/'demo-runs'/args.name
    run.resolve().relative_to((WS/'Build').resolve());run.mkdir(parents=True,exist_ok=False)
    stage=OUTPUT/'demo-stage';cwd=stage/'bin/win64';cwd.mkdir(parents=True,exist_ok=True)
    if not (stage/'data').exists():shutil.copytree(WS/'FleX/data',stage/'data')
    before_assets={p.relative_to(stage/'data').as_posix():sha(p) for p in sorted((stage/'data').rglob('*')) if p.is_file()}
    temp=OUTPUT/'temp'/('demo-'+args.name+'-'+uuid.uuid4().hex);temp.mkdir()
    env=os.environ.copy()
    for k in list(env):
        if k.startswith(('OPENFLEX_','OF_','DEMO_')):del env[k]
    for k in ('TEMP','TMP','TMPDIR'):env[k]=str(temp)
    env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONUTF8']='1'
    env['PATH']=str(core.parent)+os.pathsep+str(ext.parent)+os.pathsep+env['PATH']
    command=[str(exe),str(core),str(ext),args.mode,str(args.scene),str(args.frames),str(run),'0','0','1']
    job={'name':args.name,'kind':'FlexDemo','controller_pid':os.getpid(),'status':'WAITING_GPU_LOCK','command':command,'run':str(run),'started':now(),
         'implementation':args.implementation,'core_sha256':sha(core),'ext_sha256':sha(ext),'exe_sha256':sha(exe),'mode':args.mode,'scene':args.scene,'frames':args.frames}
    write_json(run/'job.json',job)
    add_job({'kind':'demo','name':args.name,'controller_pid':os.getpid(),'receipt':str(run/'job.json')})
    lock_path=WS/'Build/OpenFlexAlpha82c-20260928/gpu.lock'
    try:
        with SystemRequired(),lock_path.open('a+b') as lock:
            print('Waiting for shared GPU lock',flush=True)
            while True:
                try:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1);break
                except OSError:time.sleep(0.5)
            first=suspend_clock();job['status']='RUNNING';write_json(run/'job.json',job)
            with (run/'console.log').open('wb') as log:
                process=subprocess.Popen(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                job['pid']=process.pid;write_json(run/'job.json',job)
                print('FlexDemo PID',process.pid,flush=True)
                code=process.wait()
            last=suspend_clock();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
        job.update(status='PASS' if code==0 else 'FAIL',exit_code=code,finished=now(),suspended_ms=suspended_ms(first,last))
        after_assets={p.relative_to(stage/'data').as_posix():sha(p) for p in sorted((stage/'data').rglob('*')) if p.is_file()}
        job['asset_changes']=[name for name in sorted(set(before_assets)|set(after_assets)) if before_assets.get(name)!=after_assets.get(name)]
        if code==0:
            complete=json.loads((run/'complete.json').read_text(encoding='utf-8'))
            assert complete['frames']==args.frames and complete['owned_top_level_windows']==0,complete
            module_lines=(run/'modules.txt').read_text(encoding='utf-8').splitlines()
            loaded=[p for p in module_lines if Path(p).name.lower()=='nvflexreleased3d_x64.dll']
            assert len(loaded)==1 and Path(loaded[0]).resolve()==core.resolve(),loaded
            job['no_window_verified']=True;job['loaded_core']=loaded[0]
            job['capture_files']={p.name:sha(p) for p in sorted(run.glob('*.bin'))}
        write_json(run/'job.json',job)
        event('flexdemo-run-finished','无窗口FlexDemo '+args.name,status=job['status'],evidence=str(run/'job.json'))
        print(json.dumps({k:job[k] for k in ['name','status','exit_code','scene','frames','suspended_ms','asset_changes']},ensure_ascii=False,indent=2))
        if code:raise SystemExit(code)
    finally:
        remove_job(args.name)
if __name__=='__main__':main()
