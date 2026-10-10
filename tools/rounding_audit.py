"""Separate float32 coordinate-quantization audit of strict-envelope outliers.

Does not change the strict comparison. Requires the independently verified
identical shader instruction programs. Only position/velocity channels qualify;
all other outliers remain failures. Velocity is a finite difference of two
positions, so its bound is 2 coordinate quanta / substep duration.
"""
import argparse,json
from pathlib import Path
import numpy as np
from ledger import write_json
ROOT=Path(__file__).resolve().parents[2]/'Build/DisassemblyFleX-20261009'
def positions(path):return np.frombuffer(path.read_bytes(),dtype='<u4',offset=4).reshape(-1,9).view(np.float32)[:,1:4]
def main():
    p=argparse.ArgumentParser();p.add_argument('envelope');p.add_argument('--output',required=True);a=p.parse_args();output=ROOT/'evidence'/a.output
    if output.exists():raise ValueError('Immutable report exists')
    proof=json.loads((ROOT/'evidence/text-encoded-program-equality-v2.json').read_text());assert len(proof)==84 and all(x['program_equal'] for x in proof)
    report=json.loads((ROOT/'evidence'/a.envelope).read_text());rows=[]
    for row in report['rows']:
        if row['accepted']:continue
        candidate=Path(row['candidate']);scene=json.loads((candidate/'scene.json').read_text());subdt=np.float32(np.float32(scene['dt'])/np.float32(scene['substeps']));job=json.loads((candidate/'job.json').read_text());dll=Path(job['loaded_core']);manifest=json.loads((dll.parent/'generated/shader_manifest.json').read_text());assert all(x['schedule']=='preserved' and x['instruction_roundtrip_verified'] and x['hlsl_lowering_verified'] for x in manifest)
        entry={'scene':row['scene'],'strict_envelope_accepted':False,'accepted_at_float32_coordinate_precision':True,'fields':[]}
        for name,file in row['files'].items():
            if file['accepted']:continue
            if not name.startswith('state_') or 'fields' not in file:entry['accepted_at_float32_coordinate_precision']=False;continue
            values=[positions(candidate/name)]+[positions(Path(r)/name) for r in row['references']];scale=np.float32(max(float(np.abs(v).max()) for v in values));quantum=float(np.spacing(scale))
            for field,measure in file['fields'].items():
                if measure['accepted']:continue
                bound=quantum if field=='positions' else 2*quantum/float(subdt) if field=='velocities' else None
                nearest=min((d for d in measure['candidate_distances'] if d is not None),key=lambda d:d[1]);accepted=bound is not None and nearest[0]<=bound and nearest[1]<=bound
                entry['fields'].append({'capture':name,'field':field,'coordinate_scale':float(scale),'coordinate_quantum':quantum,'substep_dt':float(subdt),'derived_max_abs_bound':bound,'measured_max_abs':nearest[0],'measured_rms':nearest[1],'accepted':accepted});entry['accepted_at_float32_coordinate_precision']&=accepted
        rows.append(entry)
    write_json(output,{'strict_envelope':a.envelope,'shader_program_proof':'text-encoded-program-equality-v2.json','interpretation':'Supplemental numerical precision equivalence, not byte identity and not a claim that every outlier was observed in a reference repeat. No fixed world-space epsilon.','accepted':all(r['accepted_at_float32_coordinate_precision'] for r in rows),'rows':rows});print(json.dumps({'accepted':all(r['accepted_at_float32_coordinate_precision'] for r in rows),'rows':rows},indent=2))
if __name__=='__main__':main()
