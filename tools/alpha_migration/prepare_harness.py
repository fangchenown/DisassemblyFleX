"""Freeze the proven lock-safe FlexDemo harness and exact assets for this task."""
from common import *
def main():
    prior=WS/'Build/DisassemblyFleX-OpenFleX82c-Performance-20261010';inputs=read(prior/'evidence/inputs.json');exe=Path(inputs['executable']['path']);assert sha(exe)==inputs['executable']['sha256']
    target=ROOT/'harness';target.mkdir(exist_ok=True)
    if not (target/'source').exists():shutil.copytree(prior/'harness',target/'source')
    (target/'bin').mkdir(exist_ok=True);shutil.copy2(exe,target/'bin/FlexComparisonDemo.exe');shutil.copy2(WS/'FleX/bin/win64/SDL2.dll',target/'bin/SDL2.dll')
    stage=ROOT/'demo-stage';(stage/'bin/win64').mkdir(parents=True,exist_ok=True)
    if not (stage/'data').exists():shutil.copytree(prior/'demo-stage/data',stage/'data')
    for name,digest in inputs['assets'].items():assert sha(stage/'data'/name)==digest,name
    baselines=read(ROOT/'evidence/baselines.json')
    for b in baselines.values():
        folder=Path(b['core']['path']).parent
        for lib in ['amd_ags_x64.dll','GFSDK_Aftermath_Lib.x64.dll','nvToolsExt64_1.dll']:shutil.copy2(WS/'FleX/bin/win64'/lib,folder/lib)
    saved=dict(executable=dict(path=str(target/'bin/FlexComparisonDemo.exe'),sha256=sha(exe)),harness_source={p.relative_to(target/'source').as_posix():sha(p) for p in (target/'source').rglob('*') if p.is_file()},assets=inputs['assets'],baseline=baselines,mode_names=['df-d3d11','df-d3d12'],flags=0,scope='Same previously validated official 67-scene headless FlexDemo harness; no rendering/interop. All new run evidence stays in this task.')
    write(ROOT/'evidence/inputs.json',saved);shutil.copy2(PROJECT/'tools/locksafe_power.py',PROJECT/'tools/alpha_migration/locksafe_power.py')
    command([target/'bin/FlexComparisonDemo.exe','--list'],'scene-list',cwd=stage/'bin/win64')
    event('harness-frozen',sha256=sha(exe),assets=len(inputs['assets']));print('Frozen harness and',len(inputs['assets']),'assets')
if __name__=='__main__':main()
