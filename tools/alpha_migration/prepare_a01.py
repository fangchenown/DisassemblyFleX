"""Prepare the alpha0.1 eligibility idea as an isolated DF candidate."""
import difflib
from common import *
def main():
    name='a01-empty-triangle-v1';src=ROOT/'proposals'/name
    if not src.exists():shutil.copytree(ROOT/'baseline/source',src)
    file=src/'src/solver/ParticleStep.cpp';original=(ROOT/'baseline/source/src/solver/ParticleStep.cpp').read_bytes().decode().replace('\r','')
    begin=original.index('    uploadSubstep();\n    Pass(solver,"g_Flex_CollideTriangles"')
    end=original.index('    uploadSubstep();',begin+len('    uploadSubstep();'))
    body=original[begin:end]
    replacement='''    // Alpha0.1 eligibility idea: no triangle mesh collision can be produced
    // without shape instances or library triangle vertex storage. Keep the
    // contact-count clear above and the analytic shape/plane pass below.
    if(shape.count && geometry.vertices.buffer){
'''+body+'''    }
'''
    updated=original[:begin]+replacement+original[end:];file.write_text(updated,encoding='utf8')
    diff=''.join(difflib.unified_diff(original.splitlines(True),updated.splitlines(True),fromfile='baseline/src/solver/ParticleStep.cpp',tofile=name+'/src/solver/ParticleStep.cpp'))
    (ROOT/'evidence'/f'{name}.patch').write_text(diff,encoding='utf8')
    item=dict(id='A001-01',version='alpha0.1',title='Skip provably empty triangle-mesh collision dispatch',status='candidate-prepared',candidate=name,source=str(src),donor='history/alpha0.1/source/OpenFleX/src/d3d11/D3D11Backend.cpp:2148',donor_fact='TriangleMeshCollision ShapeCount()==0 returns before collision dispatch.',adaptation='DF uses a conservative shape.count && geometry.vertices.buffer prerequisite; contact counts clear, analytic shapes/planes, dynamic cloth triangle outputs, callbacks and all solver iterations remain.',numerical_change=False,shader_change=False,evidence=str(ROOT/'evidence'/f'{name}.patch'),required_validation=['exact 84 shader containers','paired D3D11/D3D12 FlexDemo','empty/mesh/shape transitions and multiple solvers','API/physics regression'])
    items=read(LEDGER/'optimizations.json');items=[x for x in items if x['id']!=item['id']]+[item];write(LEDGER/'optimizations.json',items)
    vs=read(LEDGER/'versions.json')
    for v in vs:
        if v['version']=='alpha0.1':v.update(status='candidate-validation',optimization_ids=['A001-01'],baseline_functionality='DF already implements the baseline NvFlex-compatible solver; preserve formulas and source ABI instead of replacing with black-box reconstructed equations.')
    write(LEDGER/'versions.json',vs);state(current_version='alpha0.1',current_candidate=name,phase='first-candidate-build');event('candidate-prepared',**item);print(src)
if __name__=='__main__':main()
