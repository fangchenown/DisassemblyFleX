"""Predeclared conservative replacement of a whole timing-quality group."""
import json,os
import fix_benchmark as fix
def main():
    b=fix.configure('final-v2');path=b.ROOT/'evidence/quality-replacements.json'
    replacements=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    covered={(q['suite'],q['mode'],q['scene'],q['repeat']) for q in replacements}
    groups={}
    for suite in ['main-v2','emit-v2','long-v2','context-v2','gpu-v2']:
        for p in (b.ROOT/'runs').glob(suite+'-*/job.json'):
            j=json.loads(p.read_text(encoding='utf-8'))
            if j['status']=='PASS':groups.setdefault((suite,j['mode'],j['scene'],j['repeat']),[]).append(j)
    pending=[]
    for key,jobs in groups.items():
        flagged=[j for j in jobs if j['timing_contaminated_by_suspend']]
        if flagged and key not in covered:
            expected=3 if key[1]=='d3d12' else 2
            assert len(jobs)==expected,'Wait for whole group before replacing'
            q=dict(suite=key[0],mode=key[1],scene=key[2],repeat=key[3],replacement_suite=f'quality-{len(replacements)+1}-v2',reason='Absolute auxiliary suspend-clock difference exceeds predeclared 1 ms threshold; replace complete paired/triple group without selecting by performance.',flagged={j['name']:j['suspended_ms'] for j in flagged},decided=b.now())
            replacements.append(q);pending.append((q,jobs));b.write(path,replacements);b.event('fix-quality-decision',**q)
    for q,jobs in pending:
        sample=jobs[0];b.EXE=__import__('pathlib').Path(sample['command'][0]);order=sample['order'];base=b.env_for
        if q['suite']=='emit-v2':
            def env(temp,core,base=base):e=base(temp,core);e['DEMO_EMIT']='1';return e
            b.env_for=env
        receipt=b.ROOT/'jobs'/(q['replacement_suite']+'-controller.json');b.write(receipt,dict(q,pid=os.getpid(),status='RUNNING'))
        with b.SystemRequired():
            for impl in order:
                result=b.run_one(q['replacement_suite'],q['mode'],q['scene'],0,impl,sample['frames'],sample['warmup'],sample['profile'],0,order)
                assert not result['timing_contaminated_by_suspend'],'Replacement itself needs another explicit quality decision'
        b.env_for=base;b.write(receipt,dict(q,pid=os.getpid(),status='PASS',runs=len(order),finished=b.now()))
    print(json.dumps(dict(new_replacements=len(pending),total_replacements=len(replacements)),indent=2))
if __name__=='__main__':main()
