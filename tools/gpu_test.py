"""Serialize a hidden GPU diagnostic, recording restart-safe job receipts."""
import argparse,hashlib,json,msvcrt,os,subprocess,time,uuid
from pathlib import Path
from ledger import add_job,remove_job,PROJECT,LEDGER,OUTPUT,event,write_json,now
from locksafe_power import SystemRequired,suspend_clock,suspended_ms
WS=PROJECT.parent;OUT=OUTPUT
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--name',required=True);parser.add_argument('--timeout',type=float,default=180);parser.add_argument('command',nargs=argparse.REMAINDER);args=parser.parse_args()
    command=args.command
    if command and command[0]=='--':command=command[1:]
    if not command:raise ValueError('No diagnostic command')
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.name):raise ValueError(args.name)
    record=OUT/'jobs'/(args.name+'.json')
    if record.exists():raise RuntimeError('Immutable diagnostic name already exists')
    temp=OUT/'temp'/('gpu-'+args.name+'-'+uuid.uuid4().hex);temp.mkdir()
    env=os.environ.copy()
    for key in ('TEMP','TMP','TMPDIR'):env[key]=str(temp)
    env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONUTF8']='1'
    env['PATH']=str(WS/'FleX/bin/win64')+os.pathsep+env['PATH']
    job={'name':args.name,'controller_pid':os.getpid(),'status':'WAITING_GPU_LOCK','command':command,'started':now(),'log':str(OUT/'logs'/(args.name+'.log'))}
    job['input_files']={str(Path(value).resolve()):hashlib.sha256(Path(value).read_bytes()).hexdigest() for value in command if Path(value).is_file() and Path(value).suffix.lower() in ('.exe','.dll','.py','.bin')}
    write_json(record,job);add_job({'name':args.name,'controller_pid':os.getpid(),'receipt':str(record)})
    try:
        with SystemRequired(),(WS/'Build/OpenFlexAlpha82c-20260928/gpu.lock').open('a+b') as lock:
            while True:
                try:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1);break
                except OSError:time.sleep(.5)
            first=suspend_clock()
            try:
                with Path(job['log']).open('wb') as log:
                    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=WS,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
                    job.update(status='RUNNING',pid=process.pid);write_json(record,job)
                    try:code=process.wait(timeout=args.timeout)
                    except subprocess.TimeoutExpired:
                        job['timed_out_after_seconds']=args.timeout
                        debugger=Path('C:/Program Files (x86)/Windows Kits/10/Debuggers/x64/cdb.exe')
                        if debugger.exists():
                            trace=OUT/'evidence'/(args.name+'-timeout-stacks.txt');debug_env=env.copy();debug_env['_NT_SYMBOL_PATH']=str(WS/'FleX/bin/win64')
                            try:
                                with trace.open('wb') as diagnostic:subprocess.run([str(debugger),'-pv','-p',str(process.pid),'-c','~* k;qd'],stdout=diagnostic,stderr=subprocess.STDOUT,env=debug_env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
                                job['timeout_stacks']=str(trace)
                            except subprocess.TimeoutExpired:pass
                        process.kill();process.wait();code=124
            finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
            job.update(status='PASS' if code==0 else 'FAIL',exit_code=code,finished=now(),suspended_ms=suspended_ms(first,suspend_clock()))
        write_json(record,job);event('gpu-test-finished',args.name,status=job['status'],receipt=str(record));print(json.dumps(job,ensure_ascii=False,indent=2))
        print(Path(job['log']).read_text(encoding='utf-8',errors='replace')[-2500:])
        if code:raise SystemExit(code)
    finally:
        remove_job(args.name)
if __name__=='__main__':main()
