"""Deliver the reviewed DLL/source/evidence and archive this completed task."""
import json,shutil,zipfile
from pathlib import Path
import fix_benchmark as fix
import ledger
def zip_tree(root,target):
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(root).as_posix())
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
def main():
    b=fix.configure('final-v2');audit=json.loads((b.ROOT/'evidence/FINAL_VALIDATION.json').read_text(encoding='utf-8'));assert audit['status']=='PASS' and not audit['issues'];assert audit['candidate_sha256']==b.sha(b.CORES['candidate'])
    assert json.loads((b.ROOT/'jobs/analysis-controller.json').read_text(encoding='utf-8'))['status']=='PASS'
    delivery=b.ROOT/'delivery';assert (delivery/'REPORT_CN.txt').exists() and (delivery/'performance-fix.png').exists()
    build=b.ROOT/'builds/final-v2'
    for name in ['NvFlexReleaseD3D_x64.dll','amd_ags_x64.dll','GFSDK_Aftermath_Lib.x64.dll','DisassemblyD3D12PoolOracle.exe']:
        shutil.copy2(build/name,delivery/name)
    # Ship the exact common harness used for all performance measurements.
    for name in ['DisassemblyFlexDemo.exe','SDL2.dll']:shutil.copy2(b.DELIVERY/name,delivery/name)
    assert b.sha(delivery/'NvFlexReleaseD3D_x64.dll')==audit['candidate_sha256']
    b.write(b.PROJECT/'CURRENT_DELIVERY.json',dict(task='D3D12 performance repair',build='final-v2',dll=str(delivery/'NvFlexReleaseD3D_x64.dll'),sha256=audit['candidate_sha256'],report=str(delivery/'REPORT_CN.txt'),validation=str(b.ROOT/'evidence/FINAL_VALIDATION.json')))
    ledger.mutate_state(lambda s:s.update(status='COMPLETE',phase='COMPLETE',active_jobs=[],next='None; task complete',finished=b.now(),candidate_sha256=audit['candidate_sha256'],report=str(delivery/'REPORT_CN.txt'),effective_flexdemo_runs=audit['effective_flexdemo_runs']))
    tasks=json.loads((b.LEDGER/'tasks.json').read_text(encoding='utf-8'))
    for item in tasks:item['status']='complete'
    b.write(b.LEDGER/'tasks.json',tasks)
    summary=json.loads((delivery/'SUMMARY.json').read_text(encoding='utf-8'))['summary']
    ratio_old=summary['d3d12 candidate/legacy']['ratio_geomean'];ratio_nv=summary['d3d12 candidate/reference']['ratio_geomean']
    archive=b.PROJECT/'PerformanceFixExecutionLedgerArchive/20261010-complete';assert not archive.exists()
    (b.LEDGER/'00_CURRENT.md').write_text(f'''# DisassemblyFleX 正式性能修复 — COMPLETE

正式源码已修复，最终构建 final-v2。
DLL SHA256：{audit['candidate_sha256']}
交付：Build/DisassemblyFleXPerformanceFix-20261010/delivery/
中文报告：该目录 REPORT_CN.txt。

有效 FlexDemo {audit['effective_flexdemo_runs']} 次、{audit['effective_flexdemo_frames']} 帧；全部67场景/两后端、三项发射负载、五项1800帧长时间测试、CPU/GPU诊断。13项既有回归、33确定性粒子案例、84 shader程序一致、专用资源池/多solver/外部Direct+Compute队列生命周期门禁均通过。

D3D12 新/旧重建版耗时比 {ratio_old:.6f}；新/原版 {ratio_nv:.6f}。仍有残余派发与状态管理差距，详见报告；不宣称所有输入逐字节或性能等价。

正式运行不含早期final-v1预验main-v1（SUPERSEDED）。旧构建、旧交付、两次先前归档与alpha8.2c任务保留。无活动作业；不需要恢复已完成的测试。
''',encoding='utf-8')
    ledger.event('acceptance-complete','D3D12正式性能修复与所有约定验收完成',dll_sha256=audit['candidate_sha256'],effective_flexdemo_runs=audit['effective_flexdemo_runs'],report=str(delivery/'REPORT_CN.txt'))
    ledger.event('archive','性能修复账本归档',archive=str(archive));shutil.copytree(b.LEDGER,archive)
    b.write(b.LEDGER/'state.json',dict(status='ARCHIVED',active_jobs=[],archive=str(archive),report=str(delivery/'REPORT_CN.txt'),candidate_sha256=audit['candidate_sha256'],updated=b.now()))
    (b.LEDGER/'00_CURRENT.md').write_text('# DisassemblyFleX 正式性能修复 — ARCHIVED / COMPLETE\n\n完整账本：../PerformanceFixExecutionLedgerArchive/20261010-complete/\n报告：../../Build/DisassemblyFleXPerformanceFix-20261010/delivery/REPORT_CN.txt\n最新DLL与哈希：../CURRENT_DELIVERY.json\n',encoding='utf-8')
    p=b.PROJECT/'OPENFLEX_EXECUTION_LEDGER.md';text=p.read_text(encoding='utf-8');start=text.index('## 之前的性能对比')
    p.write_text(f'''# DisassemblyFleX 正式性能修复 — ARCHIVED / COMPLETE

新 DLL：`../Build/DisassemblyFleXPerformanceFix-20261010/delivery/NvFlexReleaseD3D_x64.dll`
SHA256：`{audit['candidate_sha256']}`
中文报告：`../Build/DisassemblyFleXPerformanceFix-20261010/delivery/REPORT_CN.txt`
交付包：`../Build/DisassemblyFleXPerformanceFix-20261010/DisassemblyFleX-PerformanceFix-Delivery.zip`
源码包：`../Build/DisassemblyFleXPerformanceFix-20261010/DisassemblyFleX-PerformanceFix-Source.zip`
完整账本：`PerformanceFixExecutionLedgerArchive/20261010-complete/`
全部约定验证完成，无活动作业；此前归档保留。

'''+text[start:],encoding='utf-8')
    p=b.WS/'OPENFLEX_EXECUTION_LEDGER.md';text=p.read_text(encoding='utf-8');marker='## Independent task: DisassemblyFleX performance fix — ACTIVE / GO (2026-10-10)';assert marker in text
    p.write_text(text.split(marker)[0]+'''## Independent task: DisassemblyFleX performance fix — ARCHIVED / COMPLETE (2026-10-10)

Formal source repaired and DLL rebuilt. Delivery/report: `Build/DisassemblyFleXPerformanceFix-20261010/delivery/`. Full ledger: `DisassemblyFleX/PerformanceFixExecutionLedgerArchive/20261010-complete/`. Latest DLL identity: `DisassemblyFleX/CURRENT_DELIVERY.json`. All earlier tasks/archives above are preserved; this repair has no active jobs.
''',encoding='utf-8')
    # Preserve compact, complete analysis/API evidence in the binary delivery.
    for folder in ['analysis','evidence']:
        dst=delivery/folder;dst.mkdir(exist_ok=True)
        for p in (b.ROOT/folder).iterdir():
            if p.is_file() and 'progress' not in p.name:shutil.copy2(p,dst/p.name)
        if folder=='evidence':shutil.copytree(b.ROOT/'evidence/regression-final-v2',dst/'regression-final-v2')
    shutil.copytree(archive,delivery/'ledger')
    run_manifest={}
    for p in sorted((b.ROOT/'runs').glob('*/job.json')):
        j=json.loads(p.read_text(encoding='utf-8'))
        if j['suite'] not in ['main-v2','emit-v2','long-v2','context-v2','gpu-v2'] and not j['suite'].startswith('quality-'):continue
        run_manifest[p.parent.name]=dict(status=j['status'],job_sha256=b.sha(p),frames_sha256=b.sha(p.parent/'frames.csv') if (p.parent/'frames.csv').exists() else None,capture_files=j.get('capture_files',{}),core_sha256=j['core_sha256'])
    b.write(delivery/'RUN_MANIFEST.json',run_manifest)
    (delivery/'README_CN.txt').write_text('正式D3D12性能修复交付\n\nNvFlexReleaseD3D_x64.dll 为 final-v2 正式新DLL。\n同目录包含所需AMD AGS/Aftermath依赖与验收使用的固定FlexDemo无窗口EXE。SDK Ext/资产仍使用工作区 FleX。\n报告见 REPORT_CN.txt；机器可读验收见 evidence/FINAL_VALIDATION.json；逐场景表见 analysis/；账本见 ledger/。\n原始逐帧CSV/状态快照/命令记录在 Build/DisassemblyFleXPerformanceFix-20261010/runs/；未重复打入紧凑DLL交付包。\n原版SDK与此前交付DLL保持不变。本次目录中的根DLL即应使用的修复版本。\n',encoding='utf-8')
    # Source package contains the formal project, current test tools, and docs.
    source=b.ROOT/'delivery-source/DisassemblyFleX';source.mkdir(parents=True,exist_ok=False)
    for folder in ['include','src','shaders','cmake','reference','tools','tests']:shutil.copytree(b.PROJECT/folder,source/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for filename in ['CMakeLists.txt','README_CN.txt','PERFORMANCE_TESTING_CN.txt','PERFORMANCE_FIX_CN.txt','CURRENT_DELIVERY.json','OPENFLEX_EXECUTION_LEDGER.md']:shutil.copy2(b.PROJECT/filename,source/filename)
    shutil.copytree(archive,source/'PerformanceFixExecutionLedgerArchive/20261010-complete')
    shutil.copytree(b.LEDGER,source/'PerformanceFixExecutionLedger')
    b.write(source/'SOURCE_MANIFEST.json',{p.relative_to(source).as_posix():b.sha(p) for p in sorted(source.rglob('*')) if p.is_file()})
    b.write(delivery/'MANIFEST.json',{p.relative_to(delivery).as_posix():dict(sha256=b.sha(p),bytes=p.stat().st_size) for p in sorted(delivery.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'})
    binary_zip=b.ROOT/'DisassemblyFleX-PerformanceFix-Delivery.zip';source_zip=b.ROOT/'DisassemblyFleX-PerformanceFix-Source.zip'
    zip_tree(delivery,binary_zip);zip_tree(source.parent,source_zip)
    b.write(b.ROOT/'PACKAGE.json',dict(status='COMPLETE',candidate_sha256=audit['candidate_sha256'],packages=[dict(path=str(p),sha256=b.sha(p),bytes=p.stat().st_size) for p in [binary_zip,source_zip]],ledger_archive=str(archive)))
    print(json.dumps(json.loads((b.ROOT/'PACKAGE.json').read_text(encoding='utf-8')),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
