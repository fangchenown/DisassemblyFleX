"""Replace complete experiment blocks flagged by suspend clocks; keep original receipts."""
import argparse
from common import *
from run_matrix import run_one
from locksafe_power import SystemRequired
p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--name',required=True);a=p.parse_args()
receipts=[r for f in (ROOT/'runs').glob(a.suite+'-*/receipt.json') if (r:=read(f)).get('suite')==a.suite];assert receipts and all(x['status']=='PASS' for x in receipts)
keys={(r['scene'],r['emit'],r['repeat']) for r in receipts if r['timing_contaminated_by_suspend']};mapping={}
with SystemRequired():
    for key in sorted(keys):
        rs=[r for r in receipts if (r['scene'],r['emit'],r['repeat'])==key];order=rs[0]['order']
        for variant in order:
            r=next(x for x in rs if x['variant']==variant)
            extra={k:str(v).replace(str(ROOT/'runs'/r['name']),'{run}') for k,v in r.get('environment',{}).items()}
            n=run_one(a.name,variant,r['scene'],r['repeat'],r['frames'],r['warmup'],r['profile'],r['capture'],r['emit'],order,extra)
            if r.get('process_affinity_mask') is not None:assert n.get('process_affinity_mask')==r['process_affinity_mask'],'Replacement affinity mismatch'
            assert n['status']=='PASS' and not n['timing_contaminated_by_suspend'];mapping[r['name']]=n['name']
target=ROOT/'evidence'/(a.suite+'-replacements.json')
if target.exists():assert read(target)['mapping']==mapping
else:write(target,dict(reason='Retest full original experiment block for clock flag; retain every original receipt.',mapping=mapping,time=now()))
event('clock-block-retest',suite=a.suite,mapping=mapping);print(json.dumps(mapping))
