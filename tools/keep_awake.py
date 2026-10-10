"""Task-scoped system-idle prevention; never requests the display to stay on."""
import json,os,time
from pathlib import Path
from ledger import LEDGER,PROJECT,now,write_json
from locksafe_power import SystemRequired
out=PROJECT.parent/'Build/DisassemblyFleX-20261009/jobs/power_keeper.json'
with SystemRequired():
    write_json(out,{'pid':os.getpid(),'status':'RUNNING','started':now(),'request':'ES_SYSTEM_REQUIRED','display_required':False})
    while (LEDGER/'state.json').exists():
        try:
            state=json.loads((LEDGER/'state.json').read_text(encoding='utf-8'))
            if state.get('status')!='ACTIVE':break
            # Release after a long abandoned session; every build/test/checkpoint
            # refreshes state.json. Manual sleep is never overridden.
            if time.time()-(LEDGER/'state.json').stat().st_mtime>3*3600:break
        except (OSError,ValueError):pass
        time.sleep(5)
write_json(out,{'pid':os.getpid(),'status':'STOPPED','finished':now(),'display_required':False})
