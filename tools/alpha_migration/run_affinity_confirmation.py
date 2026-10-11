"""Causal follow-up on a common P-core set; never changes production affinity."""
import csv
from common import *
here=Path(__file__).parent;topology=read(ROOT/'evidence/cpu-set-topology.json');mask=topology['mask'];allowed=set(topology['selected_processors']);assert mask=='0xfff'
job=ROOT/'jobs/affinity-confirmation-pipeline.json';write(job,dict(status='WAITING',pid=os.getpid(),started=now(),mask=mask))
try:
    event('affinity-confirmation-predeclared',mask=mask,processors=sorted(allowed),scenes={'d11':[17,31],'d12':[31,33,44]},repeats=8,frames=2400,reason='Default-affinity regression panels showed many more final/a06 frames on efficiency-class0 processor14; GPU phase totals nearly unchanged. Use identical class1 processor set for every arm to separate CPU scheduling from implementation. Keep original default-policy results and do not modify DLL/application affinity policy.')
    dependency=ROOT/'jobs/quality-confirmation-pipeline.json'
    while read(dependency)['status'] in ['WAITING','RUNNING']:time.sleep(10)
    assert read(dependency)['status']=='PASS','Review preceding failure before more GPU work'
    write(job,dict(status='RUNNING',pid=os.getpid(),started=now(),mask=mask))
    def run(tool,args,name):
        p=ROOT/'jobs'/f'{name}.json'
        if p.exists() and read(p)['status']=='PASS':return
        command([sys.executable,'-B',here/(tool+'.py'),*args],name,cwd=WS,timeout=14400)
    for api,left,suffix,scenes in [('d11','df','','17,31'),('d12','df12','-d3d12','31,33,44')]:
        base='a06-combined-v1'+suffix;right='alpha-migration-final-v1'+suffix;others=['a37-distance-v2'+suffix,'a82-radix-v1'+suffix];suite='affinity-confirm-'+api+'-v1'
        run('run_matrix',['--suite',suite,'--variants',','.join([left,base,*others,right]),'--scenes',scenes,'--frames','2400','--warmup','240','--repeats','8','--env','FLEXPERF_PROCESS_AFFINITY='+mask],suite+'-command')
        run('retest_clock_blocks',['--suite',suite,'--name','affinity-clock-'+api+'-v2'],suite+'-clock-command-v2')
        for a,b in [(left,right),(left,base),(base,right),(base,others[0]),(base,others[1])]:run('analyze_primary',['--suite',suite,'--left',a,'--right',b],suite+'-'+a+'-'+b+'-analysis-v2')
        checked=0
        replacement=read(ROOT/'evidence'/(suite+'-replacements.json'))['mapping']
        for p in (ROOT/'runs').glob(suite+'-*/receipt.json'):
            r=read(p)
            if r.get('suite')!=suite:continue
            if r['name'] in replacement:p=ROOT/'runs'/replacement[r['name']]/'receipt.json';r=read(p)
            assert r['status']=='PASS' and r['process_affinity_mask']==int(mask,0)
            for row in csv.DictReader((p.parent/'cpu-placement.csv').open()):
                if int(row['frame'])>r['warmup']:
                    assert int(row['begin_processor']) in allowed and int(row['end_processor']) in allowed;checked+=1
        write(ROOT/'evidence'/f'{suite}-placement.json',dict(status='PASS',mask=mask,allowed_processors=sorted(allowed),checked_frames=checked))
    write(job,dict(status='PASS',pid=os.getpid(),finished=now(),mask=mask,scope='Supplementary fixed-class experiment only; default-policy panels remain the primary result.'))
except BaseException as e:write(job,dict(status='FAIL',pid=os.getpid(),finished=now(),error=str(e)));raise
