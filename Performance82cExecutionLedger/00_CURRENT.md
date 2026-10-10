# 已完成并归档

详细中文报告：I:\CodeX Project\KG3D_Cloth\Build\DisassemblyFleX-OpenFleX82c-Performance-20261010\report\index.html
逐项索引：I:\CodeX Project\KG3D_Cloth\Build\DisassemblyFleX-OpenFleX82c-Performance-20261010\report\coverage.html
报告包：I:\CodeX Project\KG3D_Cloth\Build\DisassemblyFleX-OpenFleX82c-Performance-20261010\DisassemblyFleX-OpenFleX82c-MeasuredPerformance-Report.zip
验收：I:\CodeX Project\KG3D_Cloth\Build\DisassemblyFleX-OpenFleX82c-Performance-20261010\analysis\final-audit.json
成功进程：5995；失败证据：47；成功执行帧：4563060。
原始逐帧/状态/字节码证据保留在 I:\CodeX Project\KG3D_Cloth\Build\DisassemblyFleX-OpenFleX82c-Performance-20261010\runs。
失败组合、内联/融合/未触发范围已在报告列明；它们不是0耗时或数值等价证明。
正式库/源码未覆盖。此任务无活动作业，不再按历史ACTIVE断点继续测试。
完整账本归档：I:\CodeX Project\KG3D_Cloth\DisassemblyFleX\Performance82cExecutionLedgerArchive\20261010-complete

以下保存历史过程，只作审计：

# DF / OF alpha8.2c 实际性能逐项比较 — ACTIVE / GO

用户2026-10-10新要求：基于FlexDemo实测逐函数/方法/shader/入口，准确数据、算法优劣、可结合性，锁屏CLI持续GO到交付并归档。

## 恢复顺序
本文件→state.json→tasks.json→events.jsonl→I:/CodeX Project/KG3D_Cloth/Build/DisassemblyFleX-OpenFleX82c-Performance-20261010下jobs/receipts。复用完成产物，核查PID后从未完成case续跑，不重开旧归档任务。

## 固定基线
- DF正式final-v2：Build/DisassemblyFleXPerformanceFix-20261010/delivery/NvFlexReleaseD3D_x64.dll，SHA256 0407fe58026c9d8dc93c36d5adf42d554bb3e660fe1f79eafd666d9a3e81e357。
- OF正式Release/alpha8.2c/SDK/alpha82c-final-core-v3/OpenFleX.dll，SHA256 46d2d3ddc01377e0ff1b6019bab68d8801fc620ff017e0599278cb62c0c61b7e。
- 上轮静态清单位于Build/DisassemblyFleX-OpenFleX82c-Static-20261010：6723 C++定义、790 HLSL函数、93API对+56扩展/Ext、356编译记录。仅作为ID/源码依据，不使用历史跨协议倍率代替新实测。

## 当前断点
已新建GO与账本。未开始新GPU运行/构建。已知同一个headless FlexDemo api_shim支持openMode动态前缀，DF/OF可同harness。旧benchmark共67场景，默认无Draw/Present；主指标包含场景CPU、Set/Update/Get、Map完成。现有profile位包括API/GPU。
- DisassemblyFleX/tests/demo/headless.cpp及api_shim.cpp，DisassemblyFleX/tools/performance_benchmark.py可复用但不得写旧任务账本。
- Release/alpha8.2c/benchmark有DemoFine.exe/DemoHotspot.exe、headless.cpp、api_shim.cpp；OF构建工具/CPU telemetry/GPU AsyncProfiler可参考。
- 读取C++文件用read_bytes().decode().replace('\r','')按LF定位；文件含CRCRLF，PowerShell Get-Content行号可能不一致。
- 此路径范围没有适用AGENTS.md，唯一PhysX/AGENTS未进入其实现范围。禁止未经用户授权的子agent，当前不派发。
- 正式矩阵前先核对两种harness差异，冻结统一harness并pilot。CPU方法插桩只在诊断构建、必须度量扰动；GPU融合辅助不能给虚构独立时间。

## 不变量
正式DF/OF/Release/上轮静态报告不可变；本次产物只在新Build目录及本账本。保留以前所有归档。GPU运行共享锁/保活SystemRequired/禁止并行编译扰动；无需亮屏或解锁。不能因为测量粒度有限便放弃任务，必须逐项给测量值或真实不可分离/未覆盖理由。


## 断点更新：统一harness与主矩阵
已构建builds/harness/FlexComparisonDemo.exe，同一EXE支持df-d3d11/of-d3d11/df-d3d12/of-vulkan，保留原场景代码，只加选择、合同、可选诊断hook。baseline/中复制正式Core/Ext，evidence/inputs.json固化SHA。pilot-v1场景0/23/63，180帧全部通过，225 OF默认环境匹配、逐帧contract一致、有限性0异常。相同初值轨迹已显著分歧，不能把场景速度直接当成同质量算法优劣。
正式primary-v1：67场景×DF/OF×6轮=804进程，每次1200帧、排除120帧，profile=0/capture=0但DEMO_BATCH最后帧含独立输出捕获/有限检查。每场景每轮A/B反转已修正，不能再同时rotate+reverse抵消顺序。当前准备启动主矩阵。GPU测试期间不运行编译或重分析，可写后续诊断源代码。待主矩阵完成后构建方法/GPU插桩（正式库不动）。
run_matrix.py支持resume PASS receipts；失败不可覆盖，须另建attempt并保留失败。共享GPU byte lock沿用Build/OpenFlexAlpha82c-20260928/gpu.lock，SystemRequired不亮屏。重要：正式结论的CI以独立进程paired repeats为样本，不把1080帧当独立重复。


## 诊断插桩已写但尚未生成/编译
tools/PerfProbe.h/.cpp、instrument_sources.py、build_diagnostics.py已准备。正式primary-v1运行中不得编译。结束后运行build_diagnostics.py --generate。该脚本复制上轮冻结sources至sources/diagnostic-v1，只修改隔离副本。CPU使用源码函数体RAII QPC，输出inclusive/self/calls/calibration；self仅减同DLL嵌套探针，不能作为全CPU执行时间；构造初始化/析构成员不包含；constexpr、trivial inline、数学header、lambda、宏accessor分别归属父级，不能造独立时间。
GPU D3D11拦截真正CreateComputeShader/Dispatch/Indirect，SHA256写入shader COM私有GUID防地址复用，保存实际DXBC及源entry/defines编译记录，每dispatch timestamp+disjoint校验。GPU计时为诊断，开销需通过同一诊断DLL off/cpu/gpu对照量化。尚未编译验证，遇编译错误从隔离源码/生成脚本修正，不改正式库。
继续：primary-v1全部PASS→生成/构建diagnostic-v1 DF及OF（原VS2022与VS2019编译器）；检查unclassified_dispatch_calls覆盖；pilot off/cpu/gpu输出/计时有效性；后续全场景剖析、质量、持续发射、后端/受控输入/组合实验。主harness已冻结且正在用，任何startup/API专项额外修改应另建harness-diag，不覆盖primary-v1 EXE。


## 断点更新：primary完成 / 诊断v3构建
primary-v1共804进程、964800帧已PASS；summary初步DF/OF场景等权geo=1.12615，等帧总ms DF55.3198/OF55.9137。43 OF faster、21 DF faster、3未区分（未做多重校正）；不是最终结论。有两组suspend-clock标记：scene51 repeat0、scene66 repeat4，需保留并整对补测，再将替代映射纳入分析恢复每场景6对。contracts、初始params全部一致，endpoint有限性通过；轨迹不是相同。
诊断v1成功构建并pilot24通过，D3D11 GPU所有dispatch hash均追踪、timestamp有效，3场景DF37/36/29 unique，OF19/22/49。CPUv1对4个逐元素copy helper的探针破坏优化，OF23从约0.8ms变3.7ms，不能作正式成本。v2改为>=1024字节才计时并排除短helper/已有telemetry，pilot72已PASS；CPU-on对off扰动小，但OF23 off仍约1.058 vs正式0.821，代码生成扰动仍在。
当前正在构建diagnostic-v3（只OF），完全保留4个copy helper原文不插桩；DF可继续使用diagnostic-v2。v2的bulk计时仅作有条件诊断，不能造小元素独立耗时。v1/v2源及binary保留，不覆盖。构建脚本pipeline session95832，检查jobs对应PID/log；未运行GPU矩阵。
实现文件 tools/PerfProbe.h / PerfGpu.h / PerfProbe.cpp：CPU atomic启用、线程私有QPC/inclusive/self/calls；GPU actual DXBC哈希写COM PrivateData GUID，逐dispatch timestamp+disjoint、实际DXBC/entry/defines输出。CMake诊断隔离副本修复tests-OFF重复FluidDensityVorticityGather规则；CPU/GPU header拆分避免Windows rpcndr small宏污染，均未改正式源。
下步：v3完成→相同3场景off/cpu/gpu+正式复测，查off偏差是否恢复；GPU及API全67剖析、独立质量、48持续发射主测、两个挂起标记整对补测、D3D12/Vulkan补充与受控输入/组合候选。候选设想（尚未实现/确认）：DF借鉴OF无特征资格跳过无三角mesh的CollideTriangles和其重复CB上传；不能跳CollideShapes（它也处理planes）。OF quadratic/POLY6关闭可作分支消融但不能当纯公式单因素，因为资格联动packed路径。所有组合必须单独源码/构建/性能/质量验证后才能下结论。


## 最新恢复点：2026-10-10 18:35后
- diagnostic-v3 OF已构建、pilot36通过。它完全不插桩4个逐元素copy helper（保留v2 bulk-only数据）；OF23 off约0.890ms vs正式0.804，仍有代码生成扰动，CPU-on约0.866。因此诊断方法时间必须标为diagnostic source-body wall，不能称正式DLL纯CPU精确成本。DF v2 off基本贴近正式。v3/DFv2的GPU独立派发哈希/时间戳可用，需最终验证全部valid/unknown。
- primary两个时钟标记组已整对补测PASS，替换mapping=evidence/primary-replacements.json，原记录不动。更新primary summary：DF/OF geo1.124741，95%CI1.120258..1.129242；等帧total DF55.323928ms/OF55.917543ms；43OF快/21DF快/3未区分（未多重校正）；所有合同/初始params一致，端点有限；0未补的clock-exclusion。用于统计的804run，实际多4重测。
- emission-v1 4场景39/40/64/65×两臂×6轮=48已完成；待analyze_primary --suite emission-v1。
- 当前正运行 api-native-v1 全67×两臂×3=402，360帧/排除120，profile6（API+CPUphase，无内置GPUtimer），OPENFLEX_CPU_PROFILE_PATH={run}/native-cpu.csv、VERBOSE1。这是正式DLL已有遥测+外层API计时，不改二进制。整条shell session2330先retest→分析→emission→api，目前在api阶段，jobs controller有pid/进度。不可同时编译或重分析。
- 正式OF CpuTelemetry没有导出的reset；native-cpu.csv含初始化/全360帧/关闭的全生命周期总计，不能直接当排除120帧的稳态值。api.csv及cpu-phases.csv可按frame过滤；计数型metric total_ms=0不当零耗时。
- 重要新发现：Vulkan已有逐dispatch GPU profiler，无需新写：src/vulkan/VulkanComputeProgram.cpp OPENFLEX_VULKAN_KERNEL_PROFILE_PATH。输出无表头列entry,x,y,z,calls,barrierNs,dispatchNs,minNs,maxNs，按program实例聚合全生命周期；检测queue timestampValidBits及period、完成event、query success。profiling会禁用prepared packet replay（line1435），开销必须标注！InitProfiling记录createInfo.entryPoint名字，多个variant同名可能重叠，需结合源/注册表及必要额外身份插桩说明。
- tools/quality_analysis.py已写，未执行：state二进制n+36byte记录(id,pos4,vel3,phase)；fluid位1<<22已核对SDK；同ID距离、自身重复、按phase的可选KDTree云距离。只能检验实际请求的渲染输出；capture0的0 nonfinite除最后DEMO_BATCH帧外是占位，不作全程证明。
- 计时方法官方文档链接保存在evidence/timing-method-sources.json，报告应引用；QueryThreadCycleTime周期不能按某GHz换墙钟。
- 还需：全67 GPU actual-shader、C++方法诊断矩阵；独立capture质量；额外API微测/初始化；DF12和OF Vulkan后端及nativekernel；受控共享输入复测；隔离混合候选验证；中文全量报告/机器表/归档。不能提前完成GO。


## 最新执行链：19:00附近
api-native-v1 402进程已PASS（67×DF/OF×3，360帧profile6）。额外harness已构建builds/harness-additional/FlexComparisonDemo.exe，注册df-additional/of-additional，主harness原样；AdditionalProbes.h提供初始化/关闭api-lifecycle.csv、直接DLL导出微测api-micro.csv、共享粒子输入回放DEMO_REPLAY_INPUT。additional-smoke-v1 2进程已PASS。回放在Scene阶段覆盖positions/velocities/phases/active，求解完成比较应使用api_ms+wait_ms排除回放拷贝；只优先选择无rigid的23/63/47，不能声称所有hidden state完全重置。输入FNV在载入时预计算，每帧记录相同来源帧/哈希。
GPU-only构建gpu-v1已PASS，完全不插CPU方法探针，保留CreateShader/Dispatch+entry/defines追踪。新增FLEXPERF_GPU_STRIDE和GPU_INIT，只记录frame0、frame1及firstFrame后按stride抽样。GPU-only-pilot-v1 36进程PASS：69,768行dispatch、333创建容器、109实际观测容器；0 invalid/unknown，224仅创建未执行。off基本回到正式速度，适用于后续GPU归因；profile帧仍有观测开销，不当正式FPS。
当前长链session97715：gpu-all-v1(67×2×2=268，1200帧、first121、stride8、init1) → gpu-emission-v1(4×2×2=16，同样抽样) → methods-all-v1(67×DF diagnostic-v2 CPU/OF diagnostic-v3 CPU×2=268，1200帧、first121 last1200) → quality-all-v1(67×DF/OF×2=268，360帧capture1)。单GPU串行，不能并行编译/重分析。jobs/controller与state记录当前PID。
新工具：analyze_gpu.py已验证pilot，按hash保存DXBC程序集、static字节码/entry/defines对应、init/warmup/steady逐dispatch统计；平均每抽样帧分母包含未调用该kernel的已采样帧，不能当每次调用。quality_analysis.py尚未跑，fluid位已核对为1<<22。
build_candidate.py已写但未执行：未插桩df-control；df-empty-triangle（借OF无特征资格，只在geometry.vertices.buffer为空时跳过CollideTriangles及其多余CB上传，保留counts clear和CollideShapes/planes）；未插桩of-control；of-quadratic（POLY6_DENSITY_KERNEL=OFF，联动packed资格，标为路径组合消融，不是纯公式单因素）。必须等当前链完成，先建control再候选，做同编译器/配置、smoke质量、性能、回放及回归，不得提前声称有效。
持续发射summary初步DF/OF geo0.71508，全部4场景DF快；scene40 repeat1 OF有clock标记，需要整对补测并为emission扩展replacement映射（当前analyze_primary只支持primary mapping）。保留所有原始运行。
后续还需API微测正式重复、共享输入回放、后端DF12/OFVK及Vulkan native kernel profile，Native_VK profiler含barrier/dispatch并禁prepared replay，需开销说明。最终完整中文报告/逐项覆盖/归档尚未开展。


## 19:10附近补充工具与执行状态
- gpu-all-v1 268、gpu-emission-v1 16已PASS；methods-all-v1正在第二轮，结束后session97715会自动启动quality-all-v1 268（360帧capture1）。不要另启动并行GPU/编译。
- analyze_methods.py已写，待methods完成后运行：对6723定义逐项匹配实际source-body数据，标注未触发/inline/constexpr/deleted/外部引擎等。读取api-native-v1的逐帧API及正式OF全生命周期native-cpu，避免混淆。
- analyze_gpu.py已通过gpu-only-pilot，后续对gpu-all/gpu-emission分别汇总。GPU-only库off接近正式，采样开启仍有观测开销；数据不能取代primary排名。
- analyze_primary.py新增solver度量（api_ms+wait_ms，且要求两侧replay-inputs.csv完全相同）和Holm多重比较校正（若scipy可用）；之后重新生成primary/emission最终统计。
- prepare_supplements.py已执行，variants增加ofvk-profile（显式225runtime项）、df/of-replay-s23和s63（基于pilot-v1 DF快照，只有粒子输入共享，隐藏域不是全重置）。
- build_candidate.py已完成未执行；等待当前链全部结束再build control/hybrid。build_diagnostics的GPU-only版本显式保留/OPT:REF /OPT:ICF /INCREMENTAL:NO并加DEBUG，CPU诊断v2/v3历史不重写。
- retest_emission.py已写未执行，重测emission scene40 repeat1两臂，写emission-replacements.json，analyze_primary已支持该映射。
- additional harness已编译及smoke2通过。后续API微测可设DEMO_API_MICRO=1和FLEXPERF_PROCESS_AFFINITY=0x1固定逻辑CPU0；主矩阵仍默认CPU调度。run_matrix已支持该仅进程临时亲和性并记录，未修改系统设置。微测是直接GetProcAddress函数调用平均（含循环/间接调用），有Noop控制；不把cycles按GHz换时间。
- 后续长链建议：当前quality完成→分析现有数据→API微测/回放/后端smoke（尤其OFVK）→构建df-control/df-empty-triangle/of-control/of-quadratic并质量/性能→后端完整/专项API不足补测→中文可检索全量报告及归档。


## 19:25后最新断点：候选/后端smoke
所有先前大矩阵均PASS：gpu-all 268、gpu-emission16、methods-all268、quality-all268。分析已完成：gpu-all 3,518,272 dispatch行/353创建容器/191观测，0invalid/unknown；gpu-emission295,740行/327创建/113观测，0invalid/unknown。方法503定义实际观测/32900条run-method；正式API33名字/5568条，native CPU229 metric/19404条。质量134对/1206快照对/1206自身重复对，contracts一致、捕获粒子nonfinite0。
实际热点例子：scene63 DF逐dispatch GPU合计约1.09ms，OF约2.11ms；OF有更重的CompactNvDirectedRows、density cooperative、mixed contacts、tagged/statistics工作。scene23 OF GPU合计约0.578ms低于DF0.645，但完整帧OF更慢，须结合CPU/传输解释。注意这些为timestamp采样诊断，不直接当成正式完整帧或融合helper单独耗时。
四个未插桩候选/控制已全部构建：df-control-v1、df-empty-triangle-v1、of-control-v1、of-quadratic-v1，variants.json已登记。源码哈希/更改详见evidence/<name>-build.json；没有改正式库。
当前长链session19379：candidate-smoke-v1（0/18/23/39/47/52/63/66×6臂=48，360帧capture1）→backend-smoke-v1（0/23/63×df12/ofvk/ofvk-profile=9，180帧capture1）。先检查退出/有限/合同/候选相对重建控制的输出，再决定长矩阵。
已建额外微测分析analyze_micro.py、回放solver分析、prepare_supplements.py。run_matrix未来每suite复制driver.py，支持可选进程affinity仅用于微基准；实际main矩阵默认调度不变。
后续：当前smoke通过→补测emission40/r1→API微基准(3场景×2×6，可固定CPU0)→shared replay23/63(DF与OF及必要quad)→DFhybrid全67与control/正式6轮+quality；OFquadratic先受影响场景与control/正式对比、质量和回放；DF12/OFVK默认/显式profile追加，Vulkan native kernel profile可用。最后统计/多重比较校正/中文全条目报告+证据、归档。仍有大量必要工作，不得提前完成GO。


## 当前恢复点：补充矩阵链 session82107
上一长链已全部PASS：df-hybrid-main1206、df-hybrid-emission72、of-quadratic-main342。初步同编译控制比DF空三角跳过geo1.00844，OF quadratic0.99583未显著；DF formal vs rebuild1.00050，Holm67均未区分。DF主候选两组clock标记(s58/r4/control,s66/r4/hybrid)，run_supplements.py整三臂补测并写generic replacement mapping。
最终primary重算Holm：40 OF快、20 DF快、7未区分；geo1.124741。emission补测后geo0.713585，四场景DF快。analyze_primary已修复多臂pair输出覆盖、增加selected_arm_runs。
quality-all输出流检查已通过11988项/4848实际请求项/0问题；检查器原多余括号语法已修复。候选质量已按全矩阵末帧和自身重复完成(DF402对,OF114对,DFemit24对)，合同一致/捕获粒子finite，不等于数值同等。
VK身份构建vk-identity-v1已成功，登记ofvk-identity-off/gpu：已有timer entry+SPIRV SHA256与保存module；profiling禁prepared packet replay，需度量扰动且不当生产排名。
当前串行run_supplements.py：DF clock补测6 → API micro36(60帧/CPU0) → API lifecycle全67×2×2=268(60帧profile6) → replay23/63各6臂×6=36(1200帧capture1) → backend-all67×df12/ofvk/ofvk-profile×3=603(360帧capture1) → VK profilepilot18 → VK kernels全67×2=134 → DF12内置timers全67×2=134。检查jobs/controller/PID，不要重复启动；运行中不编译或重分析。source/binary/formal未改。
后续必须：解析补充/API lifecycle/VK SPIRV/DF12 timers；所有新增clock flag同规则补测；最后候选+回放+quality共同解释；生成详尽中文HTML/TXT与逐6723方法/790 HLSL/356编译record/149API入口全量覆盖表，不能为inline/融合/未触发填0。仍未完成报告/归档。


## 21:45后重要恢复点：后端配置冲突已定位，任务继续
session82107 在 backend-all-v1/s17/r0/ofvk-profile 返回68后正常fail-fast结束；旧排队session58225也已退出，均不再活动。其前面 API micro36、API lifecycle268、replay23/63各36均已PASS。DF hybrid clock重测6已PASS并写mapping。不要重跑已完成矩阵。
当前唯一长链 session21095 = tools/resume_backends.py。它从原backend-all-v1冻结plan继续，已PASS跳过，FAIL原记录保留；然后VKprofilepilot18→VK kernels134→DF12 timers134→run_backend_methods.py。后者计划backend-methodpilot36→method-backend268→VK/DF12 emission各8→VK默认profilepilot18→VK默认kernel134→SDF单开关隔离对照→metadata getter微基准36。GPU串行且无并行构建。
新增runner仅在父控制进程FLEXPERF_CONTINUE_FAILED_CASES=1时继续其他case；不会覆盖FAIL。suite最终状态可能COMPLETE_WITH_FAILURES，失败不是性能值；原plan参数不变，driver-continue.py另存。所有分析必须跳过FAIL并明确列出失败/排除项，不能断言所有receipt PASS。
关键发现：OF Vulkan默认scene17已PASS，显式225项D3D11 profile会FAIL：OpenFlex.cpp:9236按OPENFLEX_D3D11_SDF_DISTANCE_BOUND=1计算sampleBounds，SdfSampleBounds.h:38向reserved2写0x53444231，OpenFlex.cpp:5724调用Stamp；VulkanBackend.cpp:7492-7493却要求reserved2==0，报convex/SDF resource contains non-finite or reserved data。不是已证实输入含NaN；是跨后端配置/资源验证冲突。已安排ofvk-profile-sdf-off只改这一个env的对照，正式DLL未修/未覆盖。失败场景集合将从backend-all自动收集。
metadata harness已单独构建(harness-metadata/builds/harness-metadata)，补充8个C++修饰名getter；原micro18项没覆盖这些因为GetProcAddress只查C名。新构建从精确PE导出名解析，仅微测期间把当前线程固定CPU0，初始化不限制。尚未运行metadata矩阵，run_backend_methods尾部会执行。
已写未执行：analyze_supplements.py(VK生命周期+实际SPIRV/DF12类别detail/API lifecycle)、quality_digest.py、build_coverage.py(6723+790+356+149全部静态项和actual DXBC/SPV，按family自包含可检索HTML)、build_report.py详细中文报告+CI图、final_analysis.py依赖所有测量结束再运行。工具均只输出本次Build目录/账本。
后续分析要完成FAIL适配：analyze_primary已允许complete-with-failures并列failed_pairs/排除<2有效pair；quality_analysis跳过FAIL；methods跳过backend失败；analyze_supplements.jobs跳过FAIL；retake_flagged只重测完成的臂，suite名称clock-retest-前缀避免glob重叠。build_report已过滤PASS计数但尚需加入正式失败列表/原因章节；final_analysis部分gate已支持失败。检查新代码语法并实际跑后修复。final_analysis尚未启动，报告未生成/归档未开始，GO仍ACTIVE。


## 22:00附近工具与队列补充
backend-all-v1已完成603计划case，状态COMPLETE_WITH_FAILURES（已知SDF profile冲突，默认Vulkan通过scene17）。session21095继续VK kernels等后端诊断。新增VK默认配置的identity kernel矩阵134及开销pilot18，避免仅剖析非默认profile；单开关隔离从实际失败场景集合自动建立。当前长链run_backend_methods尚未启动/或后续才读取，应含最新尾部。
为补足初始化方法，新增build_lifecycle_harness.py：在NvFlexInit前与Shutdown前后启用诊断probe，稳态60帧禁用；只合并library/scene初始化和shutdown成本，绝不能摊成每帧。新variants df/of/df12/ofvk-method-lifecycle，FLEXPERF_INIT=1、FIRST=999999、LAST=0；VK诊断禁单个SDF_DISTANCE_BOUND冲突项。计划methods-lifecycle-all67×2×2=268、backend代表0/17/23/36/63×2×2=20，位于backend长链最后。analyze_methods已支持extra-suite、temporal_scope、frames=0时每帧字段为null。
已排队 session26097：等待唯一resume_backends.py PID退出→核查methods-lifecycle-backends完成→final_analysis.py→audit_delivery.py。如前链失败该队列应退出，须检查PID/日志后再恢复，不要重复启动。final_analysis先对后端/回放/微基准/开销标记块补测，再统一分析、输出逐项HTML和CSV、中文主报告及CI图，随后完整性审计；尚未实际执行。
新工具：export_flat_metrics.py输出CPU/API/D3D11/D3D12/VK/coverage CSV；audit_delivery.py逐原始文件hash、实际DXBC/SPIRV hash、所有HTML链接与JS syntax、全量条目数；package_delivery.py在audit+review通过后生成报告/清单/候选包（完整raw不重复压缩，保留原目录）；archive_ledger.py在最终验收与包验证之后才归档。后两者未运行。
待报告生成后：修复任何分析/链接/JS错误；查看primary-ci.png并审核数值与措辞（尤其SDF仅显式profile失败）；处理clock标记的诊断粒度边界；写review-signoff.json明确assistant检查；package_delivery→archive_ledger→GO complete→详细中文最终交付。不要提前完成/归档。
