"""Package reviewed results and archive only after the final acceptance audit."""
import json,shutil,zipfile
from pathlib import Path
import performance_benchmark as b
def main():
    audit=json.loads((b.ROOT/'evidence/FINAL_AUDIT.json').read_text(encoding='utf-8'));assert audit['status']=='PASS' and not audit['issues']
    assert sum(audit['runs'].values())==1402
    for name in audit['expected_runs']:
        if name=='pilot-v1':continue
        controller=json.loads((b.ROOT/'jobs'/f'{name}-controller.json').read_text(encoding='utf-8'));assert controller['status']=='PASS',(name,controller)
    delivery=b.ROOT/'delivery';assert (delivery/'REPORT_CN.txt').exists() and (delivery/'performance-ratios.png').exists()
    raw={}
    for p in sorted((b.ROOT/'runs').glob('*/job.json')):
        j=json.loads(p.read_text(encoding='utf-8'));assert j['status']=='PASS'
        raw[p.parent.name]=dict(job_sha256=b.sha(p),frames_sha256=b.sha(p.parent/'frames.csv'),module_list_sha256=b.sha(p.parent/'modules.txt'),core_sha256=j['core_sha256'],capture_files=j['capture_files'])
    b.write(b.ROOT/'evidence/RUN_MANIFEST.json',raw)
    b.write(b.LEDGER/'tasks.json',[dict(id='P'+str(i+1),task=task,status='complete') for i,task in enumerate(['输入冻结、计时审计、pilot','67场景×2后端×4配对主测试及质量配对复测','统计、工作量核对及3个发射场景补测','CPU/GPU热点诊断和资源复用因果消融','中文详细报告、最终审计、图表检查与归档'])])
    b.state(status='COMPLETE',phase='COMPLETE',active_jobs=[],finished=b.now(),run_count=1402,main_effective_runs=1072,report=str(delivery/'REPORT_CN.txt'),audit=str(b.ROOT/'evidence/FINAL_AUDIT.json'))
    b.event('acceptance-complete',runs=1402,main_effective_runs=1072,report=str(delivery/'REPORT_CN.txt'),original_candidate_unchanged=True,quality_replacement=str(b.ROOT/'evidence/quality-replacement.json'))
    archive=b.PROJECT/'PerformanceExecutionLedgerArchive/20261010-complete';assert not archive.exists()
    (b.LEDGER/'00_CURRENT.md').write_text('''# DisassemblyFleX 性能对比 — COMPLETE

1402 次 FlexDemo 成功运行。主协议执行1074次（含时钟质量标志整对替换），最终使用1072次，67场景×2后端×4对。其余为pilot、CPU/GPU诊断、3个发射场景和资源复用消融。

D3D11等权几何平均候选/原版耗时比0.9979609；D3D12为4.4412701。原始正式候选DLL哈希保持8e4a8f1bb479f129147855b9656caa0379ccc2a9c91838604d3cae63a1191090。

中文报告：Build/DisassemblyFleXPerformance-20261010/delivery/REPORT_CN.txt
最终审计：Build/DisassemblyFleXPerformance-20261010/evidence/FINAL_AUDIT.json
所有原始运行：Build/DisassemblyFleXPerformance-20261010/runs/
复现入口：DisassemblyFleX/PERFORMANCE_TESTING_CN.txt

本任务完成性能比较和归因，不将诊断优化DLL作为新的正式交付。D3D12常量缓冲区和描述符堆复用是主要性能机会；诊断变体未做完整API/外部Context生命周期回归。

保留异常证据：辅助时钟−1.0003ms的整对被保守替换；两个早期代理编译失败；两个诊断控制器在全部子测试成功后的事件写入TypeError已补记。详细事件和记录均保留。

此前源码重建归档与独立alpha8.2c任务保持原状。没有活动作业，无需恢复已完成测试。
''',encoding='utf-8')
    b.event('ledger-archive',archive=str(archive));shutil.copytree(b.LEDGER,archive)
    b.write(b.LEDGER/'state.json',dict(status='ARCHIVED',active_jobs=[],archive=str(archive),report=str(delivery/'REPORT_CN.txt'),updated=b.now()))
    (b.LEDGER/'00_CURRENT.md').write_text('# DisassemblyFleX 性能对比 — ARCHIVED / COMPLETE\n\n完整账本：../PerformanceExecutionLedgerArchive/20261010-complete/\n中文报告：../../Build/DisassemblyFleXPerformance-20261010/delivery/REPORT_CN.txt\n共1402次运行，任务已完成；先前源码重建与alpha8.2c账本均保留。\n',encoding='utf-8')
    entry=b.PROJECT/'OPENFLEX_EXECUTION_LEDGER.md';text=entry.read_text(encoding='utf-8');split=text.index('## 之前的源码重建任务')
    entry.write_text('''# DisassemblyFleX 性能对比 — ARCHIVED / COMPLETE

完整性能账本：`PerformanceExecutionLedgerArchive/20261010-complete/`。
详细中文报告：`../Build/DisassemblyFleXPerformance-20261010/delivery/REPORT_CN.txt`。
证据包：`../Build/DisassemblyFleXPerformance-20261010/DisassemblyFleX-Performance-Report.zip`。
1402次成功FlexDemo运行；候选/原版耗时几何平均D3D11为0.998，D3D12为4.441。
主指标为无窗口物理更新与完整主机读回，非可视化屏幕FPS。无活动作业。

'''+text[split:],encoding='utf-8')
    entry=b.WS/'OPENFLEX_EXECUTION_LEDGER.md';text=entry.read_text(encoding='utf-8');marker='## Independent task: DisassemblyFleX performance — ACTIVE / GO (2026-10-10)';assert marker in text
    prefix=text.split(marker)[0]
    entry.write_text(prefix+'''## Independent task: DisassemblyFleX performance — ARCHIVED / COMPLETE (2026-10-10)

1402 successful FlexDemo runs; final performance report: `Build/DisassemblyFleXPerformance-20261010/delivery/REPORT_CN.txt`. Archive: `DisassemblyFleX/PerformanceExecutionLedgerArchive/20261010-complete/`. Original source-reconstruction archive and independent alpha8.2c task above are preserved. No active jobs remain for this performance study.
''',encoding='utf-8')
    for directory in ['analysis','evidence']:
        destination=delivery/directory;destination.mkdir(exist_ok=True)
        for path in (b.ROOT/directory).glob('*'):
            if path.is_file() and ('progress' not in path.name):shutil.copy2(path,destination/path.name)
    tools=delivery/'reproduce';tools.mkdir(exist_ok=True)
    for path in (b.PROJECT/'tools').glob('performance_*.py'):shutil.copy2(path,tools/path.name)
    for name in ['locksafe_power.py','build.py','analyze_demo_suite.py','ledger.py']:shutil.copy2(b.PROJECT/'tools'/name,tools/name)
    shutil.copy2(b.PROJECT/'PERFORMANCE_TESTING_CN.txt',tools/'PERFORMANCE_TESTING_CN.txt')
    shutil.copytree(archive,delivery/'ledger')
    (delivery/'README_CN.txt').write_text('报告与证据包\n\nREPORT_CN.txt 是完整中文报告；performance-ratios.png 是全部场景图表。\nanalysis/含统计表和诊断汇总；evidence/含输入、shader、质量处理与最终验收；ledger/为已完成账本。\nreproduce/为脚本审计副本，运行时应使用工作区 DisassemblyFleX/tools 的原位置，因脚本通过所在目录解析工作区。\n原始1402次运行的帧CSV、状态快照、精确命令与日志保存在同级../runs/，未重复装入此紧凑报告包。\n正式DLL仍位于之前源码重建delivery目录，本报告包不包含新的替换DLL。\n',encoding='utf-8')
    manifest={p.relative_to(delivery).as_posix():dict(sha256=b.sha(p),bytes=p.stat().st_size) for p in sorted(delivery.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'}
    b.write(delivery/'MANIFEST.json',manifest)
    package=b.ROOT/'DisassemblyFleX-Performance-Report.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(delivery.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(delivery).as_posix())
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    b.write(b.ROOT/'PACKAGE.json',dict(path=str(package),sha256=b.sha(package),bytes=package.stat().st_size,files=len(manifest)+1,ledger_archive=str(archive),status='COMPLETE'))
    print(json.dumps(dict(package=str(package),sha256=b.sha(package),archive=str(archive),runs=1402),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
