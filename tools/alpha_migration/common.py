"""Shared task utilities: hidden execution, isolated state, byte-stable sources and safe Git."""
import os,json,hashlib,subprocess,shutil,time,msvcrt,contextlib,re,sys
from pathlib import Path
from datetime import datetime,timezone,timedelta
sys.stdout.reconfigure(encoding='utf8',errors='replace')
WS=Path(__file__).resolve().parents[3];PROJECT=WS/'DisassemblyFleX';ROOT=WS/'Build/DisassemblyFleX-AlphaMigration-20261010';LEDGER=PROJECT/'AlphaMigrationExecutionLedger'
VC=Path(r'F:\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC\14.44.35207');SDK=Path(r'C:\Program Files (x86)\Windows Kits\10');SDKVER='10.0.26100.0'
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
def longpath(p):
    p=str(Path(p).absolute());return p if p.startswith('\\\\?\\') else '\\\\?\\'+p
def sha(p):
    h=hashlib.sha256()
    with open(longpath(p),'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def decode_text(data):
    if data.startswith((b'\xff\xfe',b'\xfe\xff')):return data.decode('utf-16')
    for encoding in ('utf-8-sig','gb18030'):
        try:return data.decode(encoding)
        except UnicodeDecodeError:pass
    return data.decode('utf8',errors='replace')
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8');os.replace(tmp,p)
def event(event_type,**data):
    if 'kind' in data:data=dict(data,subject_kind=data.pop('kind'))
    with (LEDGER/'events.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(dict(data,time=now(),kind=event_type),ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
def state(**data):
    s=read(LEDGER/'state.json');s.update(data,updated=now());write(LEDGER/'state.json',s)
def clean_env(temp,extra=None):
    e={k:v for k,v in os.environ.items() if not k.startswith(('OPENFLEX_','OF_','DEMO_','FLEXPERF_','GIT_TRACE','GCM_TRACE')) and k not in ['GIT_CURL_VERBOSE','CURL_VERBOSE','DISASSEMBLYFLEX_LEDGER','DISASSEMBLYFLEX_OUTPUT']}
    Path(temp).mkdir(parents=True,exist_ok=True)
    e.update(TEMP=str(temp),TMP=str(temp),TMPDIR=str(temp),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never')
    if extra:e.update({k:str(v) for k,v in extra.items()})
    return e
def safe_text(s):
    s=re.sub(r'(?im)^.*(?:Authorization:|Proxy-Authorization:).*$', '[redacted authentication header]',s)
    s=re.sub(r'(?:gh[pousr]_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+)','[redacted token]',s)
    return re.sub(r'(https?://)[^/\s:@]+:[^@\s]+@',r'\1[redacted]@',s)
def git(args,repo=PROJECT):
    p=subprocess.run(['git',*map(str,args)],cwd=repo,env=clean_env(ROOT/'temp/git'),capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if p.returncode:raise RuntimeError(safe_text(p.stderr.decode('utf8',errors='replace')))
    return p.stdout
def build_env(temp):
    e=clean_env(temp);e['PATH']=str(VC/'bin/Hostx64/x64')+os.pathsep+str(SDK/f'bin/{SDKVER}/x64')+os.pathsep+e['PATH']
    e['INCLUDE']=';'.join(str(x) for x in [VC/'include',*[SDK/f'Include/{SDKVER}'/x for x in ['ucrt','shared','um','winrt']]])
    e['LIB']=';'.join(str(x) for x in [VC/'lib/x64',SDK/f'Lib/{SDKVER}/ucrt/x64',SDK/f'Lib/{SDKVER}/um/x64'])
    return e
def command(args,name,env=None,cwd=None,timeout=None):
    log=ROOT/'logs'/f'{name}.log';receipt=ROOT/'jobs'/f'{name}.json'
    with log.open('wb') as fd:
        p=subprocess.Popen(list(map(str,args)),cwd=cwd or ROOT,env=env or clean_env(ROOT/'temp'/name),stdout=fd,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        row=dict(name=name,status='RUNNING',pid=p.pid,controller_pid=os.getpid(),command=list(map(str,args)),log=str(log),started=now());write(receipt,row);state(active_jobs=[row]);event('command-start',name=name,pid=p.pid)
        try:code=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:p.kill();p.wait();code=-999
    row.update(status='PASS' if code==0 else 'FAIL',exit_code=code,finished=now());write(receipt,row);state(active_jobs=[]);event('command-finish',name=name,exit_code=code)
    if code:raise RuntimeError(f'{name} exit {code}: {log}')
    return row
@contextlib.contextmanager
def gpu_lock():
    p=WS/'Build/OpenFlexAlpha82c-20260928/gpu.lock'
    with p.open('a+b') as f:
        while True:
            try:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1);break
            except OSError:time.sleep(.5)
        try:yield
        finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
