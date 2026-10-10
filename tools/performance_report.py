"""Generate the detailed Chinese performance report from completed evidence."""
import csv,json,math,statistics,collections,os
from pathlib import Path
import performance_benchmark as b
def read(name):return json.loads((b.ROOT/name).read_text(encoding='utf-8-sig'))
def table(headers,rows):return '\n'.join([' | '.join(headers),'-' * 80]+[' | '.join(map(str,r)) for r in rows])
CLASSES={'slower_over_5pct':'明确慢于5%阈值','faster_over_5pct':'明确快于5%阈值','within_5pct_interval':'区间位于±5%内','uncertain_or_small':'差异小或区间未收敛'}
def main():
    main=read('analysis/main-v1.json');audit=read('evidence/FINAL_AUDIT.json');diag=read('analysis/diagnostics.json');emit=read('analysis/emit-v1.json');debris=read('analysis/debris-emit-v1.json')
    assert main['passed_runs']==1072 and audit['status']=='PASS'
    rows=main['rows'];delivery=b.ROOT/'delivery';delivery.mkdir(exist_ok=True)
    lines=['DisassemblyFleX 与原版 NvFlex 的 FlexDemo 性能对比报告',f'生成时间（UTC）：{b.now()}','']
    def add(text=''):lines.append(text)
    add('一、结论与适用范围')
    for mode in ['d3d11','d3d12']:
        d=main['backend'][mode]
        add(f"{mode.upper()}：67 个官方场景，候选/原版耗时比的等权几何平均为 {d['geomean_ratio']:.4f}，即 {(d['geomean_ratio']-1)*100:+.2f}%；各场景比值范围 {d['min_ratio']:.3f}～{d['max_ratio']:.3f}。分类：{ {CLASSES.get(k,k):v for k,v in d['classifications'].items()} }。")
    add('明确存在性能差异，主要发生在 D3D12。证据指向重建 C++ 后端频繁创建/销毁常量缓冲区和 GPU 描述符堆；并非 shader 程序指令换成了更慢的版本。D3D11 的整体结果接近，不能把“未发现明显差异”解释成每个输入、驱动和硬件都完全等速。')
    add('以下数据针对最终交付候选 DLL；诊断变体仅用于查明原因，没有覆盖交付 DLL，也没有作为通过全部 API/行为验收的新版本。')
    add('测试采用官方 FlexDemo 的全部 67 个 Scene 初始化、逐帧 Update/Sync、NvFlex API 上传、求解与完整主机输出读回，使用此前还原任务的无窗口适配层。没有窗口绘制、交换链 Present、VSync 和键鼠交互。因此数据表示物理更新及主机读回，不是可视化 Demo 的屏幕 FPS，也不是端到端游戏帧率。')
    add('\n二、输入、机器和可重现条件')
    inputs=read('evidence/inputs.json');env=read('evidence/environment.json')
    for k,v in inputs['identities'].items():add(f"{k}: {v['path']}\n  SHA256={v['sha256']}；{v['bytes']} 字节")
    add(f"CPU：{env['cpu']['Name']}；{env['cpu']['NumberOfCores']} 核 / {env['cpu']['NumberOfLogicalProcessors']} 逻辑处理器。")
    add(f"系统：{env['os']['Caption']}，{env['os']['Version']}。GPU：NVIDIA GeForce RTX 5080，驱动 581.15。电源方案为 Windows 平衡，未修改电源计划、频率、电压、进程优先级或 CPU 亲和性。每帧起止逻辑 CPU 编号另存 cpu-placement.csv。")
    add(f"资产数量 {len(inputs['assets'])}，运行前后哈希不变。原版与候选使用同一 Ext DLL、同一 EXE、同一资产、场景参数、步数和输出请求；实际加载模块路径逐次验证。两版嵌入 DLL 的 84 份 shader 可执行 SHEX/SHDR 程序块已独立扫描并验证哈希多重集合完全相同。DXBC 的反射等容器元数据不必相同；未宣称 NVIDIA 驱动最终机器码已被逐条比对。")
    add(f"主测试进程结束时遥测范围：{audit['telemetry_range']}。这些是运行前后采样，不是每帧传感器记录，也不保证同一纳秒时钟。空场景会降频，频率波动与后台调度是小差异的潜在混杂因素。")
    add('\n三、测试设计和计时口径')
    add('主测试：67 场景 × D3D11/D3D12 × 4 对独立进程 × 2 实现 = 1072 次；每次 300 帧，前 60 帧不进入主统计，统计第 61～300 帧的 240 帧。每次使用新进程；场景/后端顺序按固定种子 20261010 随机化，每轮反转配对先后。两版相同场景在计划中相邻；个别配对之间可能插入同样持锁的独立诊断或编译，完整 UTC 时间保留。')
    add('质量复测：main-v1 的 D3D12 scene56 repeat2 原版辅助时钟差为 −1.0003 ms，触发预设绝对值 >1 ms 的质量标志。负数符合两次时钟查询间调度误差，而不是物理“负休眠”；未据此修改阈值。原始整对结果保留但不进入最终性能统计，以相同参数的 clock-replacement-v1 整对替换，仍保持每格4对有效样本。因此主协议实际执行1074次，最终使用1072次；决策在复测前写入 evidence/quality-replacement.json，不按性能好坏选择样本。')
    add('各 GPU 测试以及本任务的较重编译共用 alpha8.2c 的 gpu.lock，不并发争用 GPU。诊断并非同时在 GPU 上执行。CREATE_NO_WINDOW 加 ES_SYSTEM_REQUIRED 防止空闲睡眠，不请求点亮显示器；每次验证 owned_top_level_windows=0，记录系统中断时钟与不含睡眠时钟的差异。所有操作均不依赖桌面，允许锁屏执行；未主动锁定用户桌面，也不声称记录了人工锁屏前后对照实验。')
    add('主指标 complete_ms：计时从该帧 Scene 的 Map/Update/Unmap 开始，经过上传、SyncScene、NvFlexSetParams/UpdateSolver、所有输出请求，到最终阻塞 MapBuffers 完成。scene_ms、api_ms、wait_ms 三部分相加约等于 complete_ms。wait_ms 包含驱动提交、GPU 完成等待、读回及后端释放资源等 CPU 工作，不能直接称 GPU 时间。帧末 Unmap、CSV 写入、状态统计和快照在此区间外。')
    add('主测试 profile=0、capture=0，无逐帧诊断、GPU timer 查询与重状态导出；保留初始与最终状态验证。DEMO_BATCH 另记录从第 31 帧到最终帧的批次墙钟时间，其中包含帧间日志/Unmap；其起点不同，本报告不把它混作第 61～300 帧的主指标。')
    add('scene 初始化耗时是 complete.json 的 init_ms，覆盖 Init(scene) 与初始 Map，不包含 LoadLibrary/NvFlexInit；首次帧另外可由 frames.csv 查看。没有清空 OS/驱动 shader 缓存，因此不是机器冷启动测试。未把进程总时长直接当作 DLL 初始化耗时。候选使用懒创建 shader，原版创建时机不同；60 帧热身用于隔开首次运行成本。')
    add('统计：先对一次进程的 240 帧求均值，再对每个独立 A/B 配对取比值；报告其几何平均，以及对数比值的 Student t 95% 区间（主测试每格 n=4，df=3）。帧不是独立重复，未将 240 帧伪装成 240 次样本。以 ±5% 作为工程差异阈值；只有区间整体高于 1.05 或低于 0.95 才标注明显慢/快，区间整体位于 0.95～1.05 才标注该协议下接近。n=4 区间依赖近似分布假设，全场景分类没有多重检验校正，是工程性探索结论，不是普适统计定理。')
    add('\n四、D3D11 全场景结果（ms/完整物理帧）')
    def scene_table(data):return table(['ID / 场景','原版 ms','候选 ms','耗时比','差异 %','95% 比值区间','分类'],[[f"{r['scene']:02d} {r['name']}",f"{r['reference_ms']:.4f}",f"{r['candidate_ms']:.4f}",f"{r['ratio_geomean']:.3f}",f"{r['difference_percent']:+.2f}",f"[{r['ratio_low95']:.3f}, {r['ratio_high95']:.3f}]",CLASSES.get(r['classification'],r['classification'])] for r in data])
    add(scene_table([r for r in rows if r['mode']=='d3d11']))
    add('\n五、D3D12 全场景结果（ms/完整物理帧）');add(scene_table([r for r in rows if r['mode']=='d3d12']))
    add('ratio > 1 表示候选更慢；ratio = 4 表示耗时 4 倍、增加 300%，不是增加 400%。几何平均对每个场景等权，不代表某一真实游戏的场景分布。CSV 还包含 API/等待分量、运行间变异系数、帧内中位数与 P95、参数与场景初始化耗时。')
    add('\n六、空场景与发射负载补测')
    add('Rigid Debris (35)、Adhesion (39) 和 Goo Gun (40) 的官方默认状态不发射粒子，主测试中的空闲结果不用于代表实际碎片/流体负载。emit-v1 与 debris-emit-v1 在每次 Init 后通过现有 harness 调用官方空格切换逻辑，然后运行同样 60+240 帧、4 对进程。此逻辑不发送系统键盘事件，锁屏可用。Viscosity 36～38 虽初始粒子数为 0，但场景会自行发射；逐帧活动粒子数记录证明测量阶段有工作。')
    for mode in ['d3d11','d3d12']:add(mode.upper()+'（启用发射）：\n'+scene_table(sorted([r for r in emit['rows']+debris['rows'] if r['mode']==mode],key=lambda r:r['scene'])))
    add('39/40 的 16 对发射补测最终状态全部逐字节一致，逐帧活动数量一致。35 的数值重复性另见下文输出审计，不用截图或单一有限性检查推断等价。')
    for mode in ['d3d11','d3d12']:
        effective=[r['ratio_geomean'] for r in rows if r['mode']==mode and r['scene'] not in [35,39,40]]+[r['ratio_geomean'] for r in emit['rows']+debris['rows'] if r['mode']==mode]
        add(f"仅在汇总时用 35/39/40 的发射结果替换其空闲结果，仍保持 67 场景等权，{mode.upper()} 几何平均耗时比为 {math.exp(statistics.mean(map(math.log,effective))):.4f}。这项重算有明确的场景配置变化，不与默认主表混用。")
    add('\n七、CPU 与 GPU 分解：D3D12 差距在哪里')
    add('context-v1 使用同一个诊断 EXE 包装两版 Context 的 45 个虚方法，统计调用次数与调用期间墙钟时间。使用原始 DLL，不修改 shader、资源参数或求解代码。每次 180 帧，统计后 120 帧，3 对重复；额外开启 API/CPU phase 诊断。代理与计时有开销，因此下表只能定位开销，不能代替主测试绝对值。内部后端方法互调不会经过代理，例如 Map 内部调用 flush；Map 数据包含这个内部执行，不能与内部子项重复求和。')
    cpu=[];context_rows=diag['context-v1']+diag['context-heavy-v1'];gpu_rows=diag['gpu-v1']+diag['gpu-heavy-v1']
    for scene in [0,18,47,50,51,52,57]:
        rr=next(r for r in context_rows if r['mode']=='d3d12' and r['scene']==scene and r['implementation']=='reference');cc=next(r for r in context_rows if r['mode']=='d3d12' and r['scene']==scene and r['implementation']=='candidate')
        for label in ['void* map(ConstantBuffer* buffer)','void dispatch(const DispatchParams* params)','void* map(Buffer* buffer, MapType type, bool wait)']:
            x=rr['context-cpu.csv'][label];y=cc['context-cpu.csv'][label];cpu.append([scene,label,f"{x['calls_per_frame']:.0f}/{y['calls_per_frame']:.0f}",f"{x['ms_per_frame']:.6f}",f"{y['ms_per_frame']:.6f}"])
    add(table(['场景','方法','次数/帧 原/候','原版 ms/帧','候选 ms/帧'],cpu))
    add('场景差距为何不同：Rayleigh Taylor 2D (50) 每帧 81 次常量 map、722 次 dispatch；诊断中候选常量 map 约 5.86 ms、dispatch 约 2.89 ms、普通 Map（含提交/等待/释放）约 5.60 ms，远高于轻负载场景的次数和累计开销。Bananas (57) 每帧 25 次常量 map，原版本身 GPU 工作较短，因此相对慢的倍数很大。Trigger Volume (51) 两版 Scene 阶段都约 0.85～0.92 ms，并且每帧都创建 4 个普通 buffer（各约 0.43～0.45 ms），这一共同的 Demo/API 成本稀释了候选额外开销，所以它的完整帧倍数较小。这里说明的是测到的组成，并没有用粒子数量单独预测性能。')
    gpu=[]
    for mode in ['d3d11','d3d12']:
        for scene in ([0,18,47,52] if mode=='d3d11' else [0,18,47,50,51,52,57]):
            rr=next(r for r in gpu_rows if r['mode']==mode and r['scene']==scene and r['implementation']=='reference');cc=next(r for r in gpu_rows if r['mode']==mode and r['scene']==scene and r['implementation']=='candidate');x=rr['frame_metrics'];y=cc['frame_metrics'];gpu.append([mode,scene,f"{x['gpu_total_ms']:.5f}",f"{y['gpu_total_ms']:.5f}",f"{y['gpu_total_ms']/x['gpu_total_ms']:.3f}",f"{x['gpu_latency_ms']:.5f}/{y['gpu_latency_ms']:.5f}"])
    add('gpu-v1 另用原始相同 EXE 开启 SDK GPU profiling（3 对，60+120 帧）。GPU total 为 SDK 定义的阶段 timer 汇总，GPU latency 为 SDK timestamp 所覆盖的设备区间；两者不等于完整 CPU 帧，也不保证覆盖所有拷贝。诊断本身会改变调度，故不与主测试逐项直接相减。')
    add(table(['后端','场景','原版 GPU total ms','候选 GPU total ms','比值','GPU latency 原/候 ms'],gpu))
    add('GPU 时间没有出现完整物理帧那样的数倍增幅，且 dispatch 次数相同、84 份 GPU 程序一致。这支持“差距主要在主机运行层”的判断；无法据此断言所有 GPU 指令在所有场景都完全等速。完整各 shader detail timer 保存在每次 detail.csv 和 analysis/diagnostics.json 中。')
    add('\n八、逐项原因与因果实验')
    add('1. 常量缓冲区创建/销毁：src/runtime/D3D12Resources.cpp 的 ContextD3D12::map(ConstantBuffer*) 每次调用 Context12State::buffer，后者 CreateCommittedResource 创建 upload heap，再 Map。原版 RVA 0x57260 与 VersionedBuffer::map RVA 0x5b0b0 会按完成 fence 寻找可重用的版本，已有版本直接返回保持映射的指针。候选每帧不断分配，同时把 GPU 所用资源保留到 flush 后释放，令分配开销落在 Solve/API，释放开销又落在最终 Map 的等待区间。')
    add('2. GPU 描述符堆：候选 D3D12Context.cpp 的 gpu() 每 4096 项新建 shader-visible heap，flush 完成即清空 gpuHeaps，下一帧继续创建；每个 dispatch 分配 40 个描述符。原版 DynamicDescriptorHeapD3D12::allocate RVA 0x56cb0 和 DynamicHeapAllocator::allocate RVA 0x5b5f0 会基于 fence 回收堆并复用。候选因而付出额外驱动堆创建与销毁成本。')
    add('数量关系也符合这个解释：scene0 每帧 111 次 dispatch，仅派发描述符就有 4440 项，已经超过一个 4096 项堆；scene50 为 722×40=28880 项，至少需要 8 个这样的容量区段。这是由已测调用次数与源码容量计算出的下界，并非额外记录的原生 CreateDescriptorHeap 调用计数。较多 substep/dispatch 会放大反复建堆成本。')
    add('3. 次要结构差异：候选为所有 32 个 SRV（包括空槽）复制描述符，原版只为非空 SRV 调用复制；两者均处理 8 个 UAV。候选逐资源调用 ResourceBarrier，原版收集到一个数组后批量提交；候选还用 std::set 去重保留 ComPtr。代码可以证明这些额外路径存在，但本次未单独消融它们，不给出未经测量的独立百分比。原版部分 copyResourceState/Aftermath 调用也与候选不同，不能把所有剩余开销简单归为某一项。')
    add('4. 同步：两版原实现均会在本协议下等待 GPU 完成。不能把差异解释为“原版异步、候选多了一个完整等待”。候选的等待区间包含 retained 清理等 CPU 工作；下述复用实验显示这部分随资源复用大幅下降。')
    add('5. D3D11：候选使用既有动态常量缓冲区及 WRITE_DISCARD，资源重命名交给 D3D11 驱动管理；它没有 D3D12 每次新建 committed resource 的同类热路径。两版相同 shader 和接近的提交/读回协议，使总体结果接近。D3D11 上的小幅逐场景差异还可能受调度、GPU 频率、浮点轨迹与缓存影响。')
    add('因果消融只在隔离的源码快照构建中改变内存/描述符生命周期，保持场景、shader、派发顺序和读回协议。reference 标签在这些套件中特指“原候选”，candidate 标签指诊断变体，不能误读成 NVIDIA 原版。')
    abl=[]
    for suite,label in [('cbpool-v1','只复用常量缓冲区'),('heapreuse-v1','只复用描述符堆'),('pooled-v1','两者同时复用')]:
        for r in read('analysis/'+suite+'.json')['rows']:abl.append([label,r['scene'],f"{r['reference_ms']:.4f}",f"{r['candidate_ms']:.4f}",f"{(1-r['ratio_geomean'])*100:.1f}%",f"[{r['ratio_low95']:.3f},{r['ratio_high95']:.3f}]"])
    add(table(['实验','场景','原候选 ms','变体 ms','耗时下降','变体/候选 95% 区间'],abl))
    add('常量缓冲区变体按已完成 fence 复用、保持 Map，且不重用当前 front，避免破坏既有 CBV 状态切换协议；描述符堆只在原有阻塞完成后复用。两项同时改动的效果不是两个单项百分比相加，因为分配、销毁、调度与驱动状态会相互作用。')
    add('每项消融 5 个场景 × 4 对。其中 0/18/47/52 四个场景全部配对最终粒子状态逐字节相同；24 Env Cloth Large 在原候选重复运行时也有漂移，变体与基线的最大位置差可能更大，不能将该场景作为行为等价或完全相同 GPU 负载的证据。主要因果结论由另外四个精确场景支撑。没有为诊断变体重新跑全部公开 API 与边界行为门禁，因此不应直接替换正式 DLL。')
    add('组合变体又用同一 Context 代理测量 0/47 两场景、3 对。完整数据在 pooled-context-v1；分配/释放成本下降后，dispatch 与最终 Map 的耗时都接近原版，证据与两条资源复用途径一致。')
    add('\n九、输出与测量完整性')
    add(f"本任务共 {sum(audit['runs'].values())} 次成功 FlexDemo 运行；分类统计 {audit['runs']}。运行退出、帧数、加载路径、零顶层窗口、最终非有限数审计均通过；计入统计的样本无未处理的辅助时钟质量标志，上述一对异常记录已明确剔除与替换。初始参数和初始二进制状态、每帧活动粒子数量在所有主测试与消融配对一致。")
    add(f"最终粒子状态摘要：{audit['output_summary']}。")
    add('原 FleX 本身不是确定性求解器，300 帧后的个别柔体/布料/刚体轨迹会明显分离。此次保存参考重复与跨 DLL 差异的数值统计，不以“数值有限”或“进程未崩溃”替代行为等价证明，也不把之前 30/120 帧验收外推为所有 300 帧逐字节等价。主测试回答相同初始问题和协议下的实际性能；对轨迹分离场景，部分 GPU 负载差异可能来自邻域/接触演化，应保留此限制。')
    add('D3D12 保留原版 ClearState 后常量缓存未同步等已知行为；因此只做同后端原版/候选比较，不依据 D3D11 与 D3D12 数字互相比快慢来推导相同物理负载。AMD 分支、其他驱动/GPU、异步图形互操作、多 solver 并行与渲染呈现不在本次测量范围。')
    add('诊断基础设施曾出现两次编译失败（包含路径、代理生成器正则）以及两个诊断套件完成事件写入 TypeError；失败日志保留，成功代理为 context-proxy-v3，Context/GPU 各 48 次运行均已通过，完成事件已补记。没有丢弃失败测试数据来美化性能。')
    add('\n十、交付、复现与后续顺序')
    add('主要文件：REPORT_CN.txt（本报告）；performance-ratios.png（全场景比值图）；analysis/main-v1.csv/.json（134 行主结果与配对审计）；analysis/emit-v1.csv；analysis/diagnostics.json；analysis/cbpool-v1.csv、heapreuse-v1.csv、pooled-v1.csv；analysis/output-differences.json；evidence/FINAL_AUDIT.json、inputs.json、shader-program-audit.json；runs/ 全部逐帧 CSV、快照、命令与 PID receipt。')
    add('在工作区根目录执行（使用全新 suite 名避免覆盖不可变证据）：\n  python -B DisassemblyFleX/tools/performance_benchmark.py --suite repeat-main-v2 --frames 300 --warmup 60 --repeats 4\n  python -B DisassemblyFleX/tools/performance_analyze.py --suite repeat-main-v2\n诊断和消融脚本位于 DisassemblyFleX/tools/performance_*.py；固定版本的已有构建默认拒绝覆盖，重建应使用新的版本目录。精确命令见 jobs 计划和每次 runs/*/job.json。')
    add('若下一步以性能追平为目标，优先实现并正式验收 D3D12 常量缓冲区版本复用和描述符堆回收，再考虑批量 barrier、空 SRV 描述符复制与保留集合开销。必须补齐生命周期、外部 Context、多个 solver、异步队列等回归；本报告的诊断提速不能代替这些交付门禁。本轮请求的性能比较与原因分析已经完成。')
    (delivery/'REPORT_CN.txt').write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
    # Standard plotting output suitable for exporting/sharing.
    os.environ['MPLCONFIGDIR']=str(b.ROOT/'temp/matplotlib')
    for key in ['TEMP','TMP','TMPDIR']:os.environ[key]=str(b.ROOT/'temp')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,1,figsize=(15,9),layout='constrained')
    for ax,mode in zip(axes,['d3d11','d3d12']):
        data=[r for r in rows if r['mode']==mode];x=[r['scene'] for r in data];y=[r['ratio_geomean'] for r in data]
        ax.bar(x,y,color='#287ba5' if mode=='d3d11' else '#d56835');ax.errorbar(x,y,yerr=[[r['ratio_geomean']-r['ratio_low95'] for r in data],[r['ratio_high95']-r['ratio_geomean'] for r in data]],fmt='none',ecolor='#273746',capsize=1,lw=.7)
        ax.axhline(1,color='black',lw=1);ax.axhspan(.95,1.05,color='green',alpha=.12);ax.set_title(mode.upper()+' | rebuilt / original complete physics-frame time (4 process pairs)');ax.set_ylabel('Time ratio (>1 = slower)');ax.set_xticks(range(0,67,2));ax.grid(axis='y',alpha=.2);ax.set_xlim(-1,67)
        if mode=='d3d11':ax.set_ylim(min(.85,min(r['ratio_low95'] for r in data)*.97),max(1.15,max(r['ratio_high95'] for r in data)*1.03))
    axes[1].set_xlabel('Official FlexDemo scene ID; default emitter state; bars = geometric means, whiskers = 95% paired t intervals')
    fig.savefig(delivery/'performance-ratios.png',dpi=180);plt.close(fig)
    b.write(delivery/'SUMMARY.json',dict(backend=main['backend'],audit=str(b.ROOT/'evidence/FINAL_AUDIT.json'),report=str(delivery/'REPORT_CN.txt'),candidate_unchanged=inputs['identities']['candidate']['sha256']))
    print(delivery/'REPORT_CN.txt')
if __name__=='__main__':main()
