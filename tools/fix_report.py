"""Detailed Chinese delivery report built from audited repair evidence."""
import json,math,statistics,os,collections
from datetime import datetime,timezone,timedelta
import fix_task as task
from performance_benchmark import write,sha
ROOT=task.ROOT
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def table(header,rows):return '\n'.join([' | '.join(header),'-'*90]+[' | '.join(map(str,row)) for row in rows])
def main():
    audit=read('evidence/FINAL_VALIDATION.json');assert audit['status']=='PASS'
    data=read('analysis/main-v2.json');emit=read('analysis/emit-v2.json');long=read('analysis/long-v2.json');gpu=read('analysis/gpu-v2.json');profile=read('analysis/context-v2.json')
    out=ROOT/'delivery';out.mkdir(exist_ok=True);lines=[]
    def add(text=''):lines.append(text)
    def row(mode,scene,comparison,source=data):return next(r for r in source['rows'] if r['mode']==mode and r['scene']==scene and r['comparison']==comparison)
    summary=data['summary'];d11=summary['d3d11 candidate/reference'];d12=summary['d3d12 candidate/reference'];old=summary['d3d12 candidate/legacy']
    add('DisassemblyFleX D3D12 正式性能修复与验证报告')
    add('时间（北京时间）：'+datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'))
    add('一、交付结论')
    add(f"正式 C++ 源码已经修复，Release DLL 已从冻结源码构建。新 DLL SHA256：{audit['candidate_sha256']}。原版及旧重建 DLL 的历史交付未覆盖。")
    add(f"67 个官方 FlexDemo 场景的等权几何平均：D3D12 新/旧重建版耗时比 {old['ratio_geomean']:.4f}，下降 {(1-old['ratio_geomean'])*100:.2f}%；新/原版为 {d12['ratio_geomean']:.4f}，仍有 {(d12['ratio_geomean']-1)*100:+.2f}% 差距。D3D11 新/原版为 {d11['ratio_geomean']:.4f}（{(d11['ratio_geomean']-1)*100:+.2f}%）。")
    add('本次消除了已经确认的逐帧常量缓冲区/描述符堆重复创建与销毁热路径，并完善在途资源的回收时机。剩余派发、描述符拷贝、barrier 和保留集合开销仍存在，不能将本次修复表述为所有场景完全追平原版。下文逐项列出实测结果和验收边界。')
    add(f"最终用于验收的 FlexDemo 运行 {audit['effective_flexdemo_runs']} 次，累计 {audit['effective_flexdemo_frames']} 帧；另有 13 项 API 回归、33 组确定性粒子案例、专用资源生命周期/多求解器测试。全部验收通过，84 份 shader 可执行程序保持一致。")
    add('二、正式代码修改及正确性条件')
    add('1. D3D12Resources.hpp/.cpp：增加常量缓冲区版本池。upload resource 第一次创建后保持映射，后续 Map 从已经完成所有相关提交的旧版本中取用。池按峰值并发用量增长并保留至对象销毁，不在每帧重新分配。排除当前 front，保持既有资源身份比较和 root CBV 缓存行为。')
    add('2. PendingUses12：使用实际 ID3D12Fence 对象和最后使用值，数值只在同一 fence 内比较。Map 预留版本，每次 bind/copy 又更新最后使用，避免“资源在上一批已经完成，但本批再次派发后仍按上一批 fence 判断空闲”的覆盖错误。不同队列/fence 都完成后才复用。')
    add('3. D3D12Context.cpp：shader-visible 描述符堆不再于每次 flush 后销毁，按提交完成情况循环使用。每个 dispatch 的 40 个描述符绑定协议不变；当前堆用完时只选择所有相关使用已完成的堆。')
    add('4. 外部 Context 切换时，把旧命令列表使用的 retained native 对象留在按旧 fence 跟踪的批次中。新 Context 提交完成不能代替旧队列完成；旧批次在其真实 fence 完成后回收。缓冲区包装对象提前释放时，已记录命令所需的 native 资源仍保持存活。')
    add('5. 每次分配/换堆只查询一次当前 fence 的完成值，复用该快照扫描池；遇到其他 fence 仍独立查询。已完成工作的快照用于保守判断，不以未来的预计值判断完成。')
    add('未改动 HLSL、shader 指令程序、求解频率、迭代次数、粒子数量、公开 ABI 或原有 ClearState/CBV 的兼容行为。主要源码差异见 evidence/runtime-changes.patch。')
    add('三、版本与环境')
    inputs=read('evidence/inputs-final-v2.json')
    for name,x in inputs['identities'].items():add(f"{name}: {x['path']}\nSHA256={x['sha256']}；{x['bytes']} 字节")
    add('环境：Windows 10 教育版 10.0.19045；Intel Core i5-13600K（14核/20逻辑处理器）；NVIDIA GeForce RTX 5080，驱动581.15；Windows平衡电源方案。未锁定GPU频率或CPU亲和性。Release工具链为MSVC14.44.35207和Windows SDK10.0.26100.0。')
    add(f"主测试和补测共用旧交付的同一个无窗口 FlexDemo EXE、原版 Ext DLL，以及35项相同资产。输入/资产在运行前后核对哈希。GPU运行前后遥测范围：{audit['telemetry_ranges']}。这是快照，不是逐帧传感器采集，低于几个百分点的差异仍可能受系统调度/频率波动影响。")
    add('四、可锁屏执行与测量口径')
    add('所有测试都是 CREATE_NO_WINDOW 命令行进程，逐次确认 FlexDemo 顶层窗口数为0、实际加载的核心 DLL 路径正确。使用 ES_SYSTEM_REQUIRED 避免空闲睡眠，不请求显示器点亮，不改变锁屏或电源计划。共享 alpha8.2c 的 gpu.lock，GPU测试及本任务的重编译串行执行，保留另一任务。未主动锁定用户桌面，也不声称做了人工锁屏前后的额外对照。')
    add('主测试：67场景×4轮，D3D12每组原版/旧重建版/新版三个进程，D3D11每组原版/新版两个进程，合计1340次。每次300帧，前60帧热身，统计61～300帧。场景顺序固定种子随机化，进程顺序轮换/反转。每次进程相互独立，诊断运行与主测试分开。')
    add('完整物理帧 complete_ms 从 Scene 的 Map/Update/Unmap 开始，涵盖上传、SyncScene、SetParams/UpdateSolver、输出请求，到最终阻塞 Map 完成。它包含物理更新及主机读回，不包含画面渲染、Present或VSync，因此不是可视化Demo的屏幕FPS。CSV写入、最终快照及帧末Unmap在这个计时区间外。wait_ms 包含提交、GPU等待和CPU资源整理，不能直接称为GPU执行时间。')
    add('主测试 profile=0/capture=0，关闭昂贵逐帧导出与GPU诊断，保留初始和最终状态。独立CPU诊断采用相同代理EXE；独立GPU诊断profile=1，均不混入主测试绝对时间。初始化/首帧不计入热身后主指标；未清空系统/驱动shader缓存，不声称测到了机器冷启动。')
    add('统计以每次进程240帧均值为一个样本，先取同组耗时比，再计算四轮几何平均及对数比值Student t 95%区间。帧不作为独立重复。±5%是工程阈值；四轮样本量较小、全场景没有多重检验校正，区间适用于本机/协议，不保证跨硬件普适。')
    add(f"时钟质量处理：辅助时钟差绝对值>1ms的整组先记录后保守复测，不按性能好坏选样本。本次明确替换记录：{audit['quality_replacements']}。早期main-v1被后续合并同fence查询的final-v2取代，原始预验保留，不计入最终统计。")
    add('五、全部场景的正式性能结果')
    add('D3D11：单位ms/完整物理帧；比值>1表示新版更慢。')
    add(table(['ID 场景','原版','新版','新/原','95%区间'],[[f"{r['scene']:02d} {r['name']}",f"{r['baseline_ms']:.4f}",f"{r['candidate_ms']:.4f}",f"{r['ratio']:.3f}",f"[{r['ci_low']:.3f},{r['ci_high']:.3f}]"] for r in data['rows'] if r['mode']=='d3d11']))
    add('D3D12：旧版指此前源码重建的正式交付DLL。')
    matrix=[]
    for scene in range(67):
        n=row('d3d12',scene,'candidate/reference');o=row('d3d12',scene,'candidate/legacy')
        matrix.append([f"{scene:02d} {n['name']}",f"{n['baseline_ms']:.4f}",f"{o['baseline_ms']:.4f}",f"{n['candidate_ms']:.4f}",f"{(1-o['ratio'])*100:.1f}%",f"{n['ratio']:.3f}",f"[{n['ci_low']:.3f},{n['ci_high']:.3f}]"])
    add(table(['ID 场景','原版ms','旧重建ms','新版ms','相对旧版下降','新/原比','新/原95%区间'],matrix))
    add('完整CSV包含帧内P95、进程间变异、Scene/API/等待分量及参数。每个场景等权的几何平均不能直接代替某款游戏的负载分布。')
    add('六、实际发射负载和长时间测试')
    add('Rigid Debris(35)、Adhesion(39)、Goo Gun(40)默认不发射。补测通过现有harness调用官方空格切换逻辑，两版/三版采用同样输入，不发送桌面键盘事件；各跑4轮、60+240帧。默认空闲结果与启用发射结果分列。')
    add(table(['后端/场景','对照','基线ms','新版ms','比值','95%区间'],[[f"{r['mode']}/{r['scene']}",r['comparison'],f"{r['baseline_ms']:.4f}",f"{r['candidate_ms']:.4f}",f"{r['ratio']:.3f}",f"[{r['ci_low']:.3f},{r['ci_high']:.3f}]"] for r in emit['rows']]))
    for mode,comparison in [('d3d11','candidate/reference'),('d3d12','candidate/reference'),('d3d12','candidate/legacy')]:
        values=[r['ratio'] for r in data['rows'] if r['mode']==mode and r['comparison']==comparison and r['scene'] not in [35,39,40]]+[r['ratio'] for r in emit['rows'] if r['mode']==mode and r['comparison']==comparison]
        add(f"用三项发射结果替代空闲结果后，67场景等权汇总 {mode} {comparison} = {math.exp(statistics.mean(map(math.log,values))):.4f}。")
    add('长时间：0/24/47/50/52，两个后端，每次1800帧（固定dt下约30秒物理时间），共25次。它用于较长轨迹和资源稳定性检查，只有一轮，不能当作四轮主统计。')
    add(table(['后端/场景','对照','基线ms','新版ms','比值'],[[f"{r['mode']}/{r['scene']}",r['comparison'],f"{r['baseline_ms']:.4f}",f"{r['candidate_ms']:.4f}",f"{r['ratio']:.3f}"] for r in long['rows']]))
    add('七、原有性能问题是否实际消除')
    names=['void* map(ConstantBuffer* buffer)','void dispatch(const DispatchParams* params)','void* map(Buffer* buffer, MapType type, bool wait)'];profrows=[]
    for scene in [0,18,47,50,52,57]:
        for name in names:
            selected={x['implementation']:x['context-cpu.csv'].get(name,{'ms_per_frame':0,'calls_per_frame':0}) for x in profile if x['scene']==scene}
            profrows.append([scene,name,f"{selected['candidate']['calls_per_frame']:.0f}"]+[f"{selected[key]['ms_per_frame']:.6f}" for key in ['reference','legacy','candidate']])
    add('Context CPU诊断：每场景三轮，统计第61～180帧，同一代理包装45个虚方法；计时本身有开销，因此用于定位，不替代主测试。')
    add(table(['场景','方法','新版次数/帧','原版ms','旧重建ms','新版ms'],profrows))
    add('常量Map的逐次原生资源创建已消失；最终Map等待区间的资源销毁成本也随之减少。专用回归在32批、每批256次派发后，常量版本数保持256、描述符堆保持3，没有在后续批次继续增长。该高水位验证来自真实DLL内池状态，并同时核对每次GPU写回值。')
    add('GPU timer诊断（SDK定义的GPU total，包含其阶段计时开销，不等同完整帧）：')
    add(table(['场景','对照','基线GPU total ms','新版GPU total ms','比值'],[[r['scene'],r['comparison'],f"{r['baseline_gpu_total_ms']:.6f}",f"{r['candidate_gpu_total_ms']:.6f}",f"{r['candidate_gpu_total_ms']/r['baseline_gpu_total_ms']:.3f}" if r['baseline_gpu_total_ms'] else 'N/A'] for r in gpu['rows']]))
    add('残余差距：新后端仍逐个复制32个SRV（包括空槽）和8个UAV，逐资源发barrier，并用集合管理native引用；原版部分路径只复制非空SRV、批量提交barrier。Context诊断显示派发开销仍高于原版。代码能确认结构差异存在，但本次未分别消融它们，不给出未经测量的独立百分比。没有更改shader来掩盖CPU成本。')
    add('八、生命周期、API和行为回归证据')
    add(json.dumps(audit['lifetime'],ensure_ascii=False,indent=2))
    add('专用测试的含义：原/新各8192次带不同常量的连续GPU派发，跨多个描述符堆；常量在上一提交结束后再次绑定而不Map，再连续Map，检测错误提前复用；包装对象在提交前释放，检查native对象保活；用CPU gate阻塞一条队列，另一条独立fence从大数值开始运行，防止跨fence错误比较；Direct和Compute队列都验证；三个solver交错运行120帧并在队列有工作时销毁/重建两个solver，与原版比较837340个输出word，全部精确。')
    gates=read('evidence/regression-final-v2/results.json');add(table(['回归项','结果'],[[x['gate'],'PASS' if x['passed'] else 'FAIL'] for x in gates]))
    add('33组确定性案例覆盖粒子、速度、密度、约束、充气体、刚体/塑性、几何碰撞、外部D3D11 render/async、D3D12及附加输出。93个导出名称/序号保持，无原核心DLL转发依赖。84个可执行shader程序从实际原/旧/新DLL扫描均相同。')
    add('最终输出统计（exact表示最终粒子state逐字节相同；all_final_snapshots_exact还要求其它最终快照一致）：')
    add(json.dumps(audit['output_summary'],ensure_ascii=False,indent=2))
    add('额外核查：D3D12 Rigid2（54）在本轮四次旧重建运行中输出稳定，但与原版不同；新版四次最终粒子状态全部与原版逐字节相同。因此它被单列为旧版差异向原版恢复，没有被含混归入非确定性。原/新版共同state SHA256为9d38b4638175daf4290f928744c23845262e82a3235b8f99bcaa023b6db55018，旧版为ed9204816306e01a7c3da35b225636e72c3e0daa9749220676fa4d65db20b80f。此处证明本轮结果，不将单场景样本外推为所有输入的保证。')
    add('所有计入验收的运行初始参数/二进制输入与逐帧活动粒子数量一致，最终粒子位置/速度没有非有限值，ID/phase/逆质量保持。另比较最终render、rigids、triangles、diffuse等已导出快照并保存数值差异；这是最终快照检查，不宣称主性能运行逐帧检查了所有派生浮点值。')
    add('原版FleX存在非确定性，长时间布料/柔体等轨迹可分离；analysis中的baseline_repeat_drift记录原版或旧重建版的重复差异。主测试中所有新/原版非精确粒子输出的场景，原版重复运行本身也存在差异；这不是声明所有新差异都落在四个样本的最大数值范围内，部分差异会更大。本次以确定性门禁、离散/输入检查、全部shader一致、专用生命周期数据验证及完整差异记录支撑修复，不将“无崩溃”当作所有输入逐字节等价，也未修改此前浮点阈值来把它们强行计成精确等价。')
    add('范围：本机NVIDIA/D3D11/D3D12和测试的同设备外部Context/Direct/Compute队列。没有承诺任意设备切换、未正确同步的跨队列资源读写、多线程并发调用、CUDA、AMD硬件、所有驱动或可视化呈现行为。原有D3D12 ClearState常量缓存等已知兼容行为沿用，原版native注册资源Getter等既有问题不属于此次性能修复。')
    add('九、复现和交付')
    add('正式源码在工作区 DisassemblyFleX；新DLL及依赖在本报告同目录。历史原版和旧重建DLL保留。源码包提供完整可编译工程与验收脚本，运行/构建应放回KG3D_Cloth/DisassemblyFleX，以便定位现有FleX SDK与工具链。')
    add('工作区根目录执行（使用新名称避免覆盖证据）：\n  python -B DisassemblyFleX/tools/fix_task.py python -B DisassemblyFleX/tools/build.py --name rebuilt-v1\n  python -B DisassemblyFleX/tools/fix_regression.py --build rebuilt-v1 --name regression-rebuilt-v1\n  python -B DisassemblyFleX/tools/fix_benchmark.py --build rebuilt-v1 --suite benchmark-rebuilt-v1\n  python -B DisassemblyFleX/tools/fix_analyze.py --suite benchmark-rebuilt-v1')
    add('重要索引：FINAL_VALIDATION.json；MANIFEST.json；analysis/main-v2.csv/.json、emit-v2、long-v2、context-v2、gpu-v2；evidence/runtime-changes.patch；evidence/final-v2-lifetime.json；evidence/regression-final-v2；jobs与runs中的精确命令、PID、加载模块、逐帧CSV和快照。')
    add('早期构建和被取代的预验数据均保留；最终只使用固定final-v2哈希的结果。完成后账本归档于DisassemblyFleX/PerformanceFixExecutionLedgerArchive/20261010-complete，OPENFLEX_EXECUTION_LEDGER.md保留可追溯入口。')
    (out/'REPORT_CN.txt').write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
    os.environ['MPLCONFIGDIR']=str(ROOT/'temp/matplotlib')
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,1,figsize=(15,12),layout='constrained')
    for ax,mode in [(axes[0],'d3d11'),(axes[2],'d3d12')]:
        rr=[r for r in data['rows'] if r['mode']==mode and r['comparison']=='candidate/reference'];x=[r['scene'] for r in rr];y=[r['ratio'] for r in rr]
        ax.errorbar(x,y,yerr=[[r['ratio']-r['ci_low'] for r in rr],[r['ci_high']-r['ratio'] for r in rr]],fmt='o',ms=3,capsize=2,color='#287a9c',lw=.8);ax.axhline(1,color='black',lw=1);ax.axhspan(.95,1.05,color='green',alpha=.1);ax.set_title(mode.upper()+' repaired / original complete physics-frame time');ax.set_ylabel('Time ratio');ax.set_xticks(range(0,67,2));ax.grid(axis='y',alpha=.2)
    for label,color,values in [('Original','#333333',[row('d3d12',s,'candidate/reference')['baseline_ms'] for s in range(67)]),('Old reconstruction','#dc743b',[row('d3d12',s,'candidate/legacy')['baseline_ms'] for s in range(67)]),('Repaired','#287a9c',[row('d3d12',s,'candidate/reference')['candidate_ms'] for s in range(67)])]:axes[1].plot(range(67),values,label=label,color=color,lw=1,marker='.',ms=3)
    axes[1].set_yscale('log');axes[1].set_ylabel('Mean frame time (ms, log scale)');axes[1].set_title('D3D12: original vs old reconstruction vs repaired');axes[1].legend();axes[1].grid(axis='y',alpha=.2);axes[1].set_xticks(range(0,67,2));axes[2].set_xlabel('Official scene ID; default emitter state; 4 process groups, 60 warmup + 240 measured frames')
    fig.savefig(out/'performance-fix.png',dpi=180);plt.close(fig)
    write(out/'SUMMARY.json',dict(candidate_sha256=audit['candidate_sha256'],summary=summary,validation=str(ROOT/'evidence/FINAL_VALIDATION.json'),report=str(out/'REPORT_CN.txt')))
    print(out/'REPORT_CN.txt')
if __name__=='__main__':main()
