"""Atomic task checkpoints; append-only events and small resumable state."""
import argparse
from datetime import datetime,timezone,timedelta
import json
import os
import msvcrt,time
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]
LEDGER=Path(os.environ.get('DISASSEMBLYFLEX_LEDGER',str(PROJECT/'OpenFlexExecutionLedger')))
OUTPUT=Path(os.environ.get('DISASSEMBLYFLEX_OUTPUT',str(PROJECT.parent/'Build/DisassemblyFleX-20261009')))
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
def write_json(path,value):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temp,path)
def event(kind,detail,**evidence):
    row={'time':now(),'event':kind,'detail':detail,**evidence}
    with (LEDGER/'events.jsonl').open('a',encoding='utf-8') as output:
        output.write(json.dumps(row,ensure_ascii=False)+'\n');output.flush();os.fsync(output.fileno())
    return row
def mutate_state(change):
    lockpath=OUTPUT/'jobs/ledger.lock'
    with lockpath.open('a+b') as lock:
        while True:
            try:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1);break
            except OSError:time.sleep(.05)
        try:
            state=json.loads((LEDGER/'state.json').read_text(encoding='utf-8'));change(state);write_json(LEDGER/'state.json',state);return state
        finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
def add_job(job):
    def change(state):
        state['active_jobs']=[j for j in state['active_jobs'] if j.get('name')!=job['name']]+[job]
    return mutate_state(change)
def remove_job(name):
    def change(state):state['active_jobs']=[j for j in state['active_jobs'] if j.get('name')!=name]
    return mutate_state(change)
def checkpoint(phase,summary,next_steps,active_jobs=None):
    def change(state):
        state.update(phase=phase,summary=summary,next=next_steps,updated=now())
        if active_jobs is not None:state['active_jobs']=active_jobs
    state=mutate_state(change)
    (LEDGER/'00_CURRENT.md').write_text('# DisassemblyFleX — '+state['status']+' / '+phase+'\n\n'+summary+'\n\n## 下一步\n\n'+'\n'.join(f'{i+1}. {n}' for i,n in enumerate(next_steps))+'\n\n先检查 state.active_jobs 和实际进程；锁屏兼容、GPU 串行、所有生成物在 Build。所有验收完成前不归档、不宣告完成。\n',encoding='utf-8')
    event('checkpoint',summary,phase=phase,next=next_steps)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--status',action='store_true');args=parser.parse_args()
    state=json.loads((LEDGER/'state.json').read_text(encoding='utf-8'))
    print(json.dumps(state,ensure_ascii=False,indent=2))
