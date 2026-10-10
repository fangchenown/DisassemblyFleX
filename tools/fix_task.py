"""Independent task paths for the formal D3D12 performance repair."""
import os,sys,subprocess,msvcrt,time,json
from pathlib import Path
WS=Path(__file__).resolve().parents[2];PROJECT=WS/'DisassemblyFleX'
ROOT=WS/'Build/DisassemblyFleXPerformanceFix-20261010';LEDGER=PROJECT/'PerformanceFixExecutionLedger'
os.environ['DISASSEMBLYFLEX_OUTPUT']=str(ROOT);os.environ['DISASSEMBLYFLEX_LEDGER']=str(LEDGER)
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['PYTHONUTF8']='1'
for name in ['builds','source-snapshots','evidence','jobs','logs','temp','analysis','delivery']: (ROOT/name).mkdir(parents=True,exist_ok=True)
for key in ['TEMP','TMP','TMPDIR']:os.environ[key]=str(ROOT/'temp')
from locksafe_power import SystemRequired
def main():
    # Reuse the proven build/oracle wrappers with task-specific ledger/output.
    command=sys.argv[1:]
    if not command:raise ValueError('fix_task.py <command> [args]')
    with SystemRequired(),(WS/'Build/OpenFlexAlpha82c-20260928/gpu.lock').open('a+b') as lock:
        while True:
            try:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1);break
            except OSError:time.sleep(.2)
        p=subprocess.run(command,cwd=WS,env=os.environ.copy(),creationflags=subprocess.CREATE_NO_WINDOW)
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    raise SystemExit(p.returncode)
if __name__=='__main__':main()
