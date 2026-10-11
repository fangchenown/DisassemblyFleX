"""Bootstrap the alpha-history migration task without modifying prior ledgers."""
from pathlib import Path
import json,datetime,subprocess,hashlib,zipfile,shutil,os
WS=Path(__file__).resolve().parents[3];PROJECT=WS/'DisassemblyFleX';ROOT=WS/'Build/DisassemblyFleX-AlphaMigration-20261010';LEDGER=PROJECT/'AlphaMigrationExecutionLedger'
def now():return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if (LEDGER/'state.json').exists():print('Existing ledger; resume it.');return
    for name in ['baseline','history','sources','builds','runs','jobs','logs','evidence','analysis','temp','delivery','tools']: (ROOT/name).mkdir(parents=True,exist_ok=True)
    LEDGER.mkdir();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=PROJECT).decode().strip()
    assert head=='51cac80f7bb0f466869da573ae9422f0885a9672'
    archive=ROOT/'baseline/df-source.zip';subprocess.run(['git','archive','--format=zip','--output',str(archive),'HEAD'],cwd=PROJECT,check=True)
    with zipfile.ZipFile(archive) as z:z.extractall(ROOT/'baseline/source')
    dll=WS/'Build/DisassemblyFleXPerformanceFix-20261010/delivery/NvFlexReleaseD3D_x64.dll';ext=WS/'FleX/bin/win64/NvFlexExtReleaseD3D_x64.dll';nv=WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll'
    refs={}
    for name,src in [('df',dll),('nv',nv)]:
        d=ROOT/'baseline'/name;d.mkdir();shutil.copy2(src,d/src.name);shutil.copy2(ext,d/ext.name)
        refs[name]={'core':{'path':str(d/src.name),'sha256':sha(src)},'ext':{'path':str(d/ext.name),'sha256':sha(ext)}}
    write(ROOT/'evidence/baselines.json',refs)
    write(ROOT/'evidence/source-baseline.json',dict(head=head,archive=str(archive),archive_sha256=sha(archive),files={p.relative_to(ROOT/'baseline/source').as_posix():sha(p) for p in (ROOT/'baseline/source').rglob('*') if p.is_file()}))
    write(LEDGER/'state.json',dict(task='DisassemblyFleX alpha-history optimization migration',status='active',phase='history-inventory',started=now(),updated=now(),baseline_head=head,output=str(ROOT),current_version=None,current_candidate=None,active_jobs=[],remote='https://github.com/fangchenown/DisassemblyFleX.git',push_authorized=True,tag=None))
    tasks=[('M0','冻结基线、环境、协议与全部alpha版本清单'),('M1','按真实版本顺序读取优化证据、源码差异并建立逐项迁移账'),('M2','按版本顺序实现/检验候选并维护累计可回退底座'),('M3','全量FlexDemo/正确性/资源/ABI/长期与性能终验'),('M4','正式源码与DLL交付、详细中文报告、证据完整性核验'),('M5','账本归档、git commit/tag/push与远程身份核验')]
    write(LEDGER/'tasks.json',[dict(id=i,task=t,status='in_progress' if i=='M0' else 'pending') for i,t in tasks])
    write(LEDGER/'versions.json',[]);write(LEDGER/'optimizations.json',[])
    (LEDGER/'events.jsonl').write_text(json.dumps(dict(time=now(),kind='task-start',baseline=head,output=str(ROOT)),ensure_ascii=False)+'\n',encoding='utf8')
    current=f"""# DF alpha历史优化迁移 — ACTIVE / GO

恢复顺序：本文件 → state.json → tasks.json → versions.json / optimizations.json → events.jsonl → {ROOT}/jobs 与不可变运行回执。
当前Git基线：{head}，main与origin/main原先一致。
冻结源码：{ROOT}/baseline/source；冻结DF DLL及原版NV DLL/Ext在baseline/df与baseline/nv。
当前仅完成初始冻结，尚未修改计算代码、开始新编译或新GPU测试。

用户目标：逐alpha版本顺序审计并迁移有效优化；默认不影响计算与表现；只有极大收益且影响极轻微的候选才考虑例外。以实际测量和验收判断，不机械移植所有旧代码。全程允许锁屏。完成后commit、更新HEAD/tag并推送，归档本任务。
全部旧账本/Release/Build报告原样保留。OpenFleX、KG3D_OpenFleX作为只读历史来源；不向它们提交迁移改动。
当前无适用AGENTS.md；禁止未经用户授权的子agent，本任务不派发。
已发现OF与KG3D的alpha2.2至8.2c标签；早期0.1至2.1在Release/ARCHIVED_VERSIONS.csv标为MOVED_TO_DELETED，需继续查Deleted/History而非认定缺失。Release当前可见6.5c起，不能当作全部历史。
所有Git网络操作必须从环境彻底移除GIT_CURL_VERBOSE、GIT_TRACE*、GCM_TRACE*（不能设字符串0，旧Git仍会输出认证头）；捕获输出并脱敏后才显示。禁止打印凭据，禁止强推。用户已授权最终commit/tag/push。
复用前任务纯测量方法可以，但不得直接调用会写旧LEDGER的common.py/build.py/fix_task.py。新工具所有状态只能写本账本和新Build目录。
单GPU共享锁沿用Build/OpenFlexAlpha82c-20260928/gpu.lock；禁止在性能运行时并行编译/重分析；CREATE_NO_WINDOW和SystemRequired，不要求亮屏，不改变系统电源计划。
下一步：补齐0.1起全部版本/标签/归档证据，确定版本和优化顺序，冻结准入协议，再从最早版本开始候选实现/验收。最终报告需列每项采纳/已有/不适用/拒绝/依赖/证据不足。
"""
    (LEDGER/'00_CURRENT.md').write_text(current,encoding='utf8')
    (LEDGER/'01_ACCEPTANCE.md').write_text("""# 验收协议（首次运行前冻结，变更须留事件）

- 基线：Git 51cac80，正式DF final-v2 SHA256 0407fe58026c9d8dc93c36d5adf42d554bb3e660fe1f79eafd666d9a3e81e357；原版NV仅作为行为参照；当前DF为性能控制。另构建同编译配置的无改动控制，避免把编译器/布局变化算作优化。
- 优先保持原84个shader程序及公式、迭代/子步/回调/公开输入输出契约。每项最小可验证改动；改变数据流也验证生命周期、别名、外部Context与多solver。
- 严格输出契约：帧数、dt、子步、迭代、粒子/约束数量、ID/phase、参数、已定义的公开结果必须一致。不能少算子步、降频、少输出或缩小物理工作来冒充同任务加速。
- 数值：确定性样例用逐字节/逐元素相等；非确定性路径以冻结DF自身重复波动为参照，同时检查短程、长程、结构指标与原版边界；不把无NaN或大粒子RMS接近当等价证明。
- 原则上不接受数值公式变化。本任务“极轻微影响”的例外必须在候选运行前明确指标：目标负载完整帧收益至少10%、配对95%区间支持，且全场景汇总无显著退化、关键场景无新增穿透/应变/爆炸/数量/相位/回调差异；逐步误差需落在与DF原有舍入/重复波动相称的预设窄范围。没有可充分证明的例外候选则不启用例外；不能事后放宽阈值。
- 代表场景筛选采用配对进程；最终D3D11/D3D12全67场景、持续发射和必要长程。计时关闭observer与昂贵逐帧捕获，质量另跑；统计独立单位为进程对，保留原始数据/置信区间/失败与时钟质量标记。
- 每个alpha版本都必须有对应优化条目与结论；别名标签/相同源码树注明共享证据；Android/引擎渲染专用变更只审计适用性，不伪称已移植到DF核心或已测移动端。
- GPU计时与CPU方法观察仅作归因并标注扰动。最终排名使用未插桩交付DLL与控制组。
- 发布前：无未解释失败；原始输入/输出/二进制/源码哈希可追溯；报告详细列收益/退化/兼容边界；新代码提交/标签与远程一致；所有旧归档保留。
""",encoding='utf8')
    entry=PROJECT/'OPENFLEX_EXECUTION_LEDGER.md';old=entry.read_text(encoding='utf8');entry.write_text('# DisassemblyFleX alpha历史优化迁移 — ACTIVE / GO\n\n当前恢复：[AlphaMigrationExecutionLedger/00_CURRENT.md](AlphaMigrationExecutionLedger/00_CURRENT.md)。\n本任务输出：../Build/DisassemblyFleX-AlphaMigration-20261010/。以下各旧任务保持归档状态。\n\n'+old,encoding='utf8')
    rootentry=WS/'OPENFLEX_EXECUTION_LEDGER.md'
    with rootentry.open('a',encoding='utf8') as f:f.write('\n## Independent task: DisassemblyFleX alpha-history optimization migration — ACTIVE / GO (2026-10-10)\n\nResume DisassemblyFleX/AlphaMigrationExecutionLedger/00_CURRENT.md. Output: Build/DisassemblyFleX-AlphaMigration-20261010/. Preserve all earlier archives. User authorizes final commit, tag and push after validation.\n')
    print(ROOT)
if __name__=='__main__':main()
