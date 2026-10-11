# DF alpha历史优化迁移 — ACTIVE / GO

恢复顺序：本文件 → state.json → tasks.json → versions.json / optimizations.json → events.jsonl → I:\CodeX Project\KG3D_Cloth\Build\DisassemblyFleX-AlphaMigration-20261010/jobs 与不可变运行回执。
当前Git基线：51cac80f7bb0f466869da573ae9422f0885a9672，main与origin/main原先一致。
冻结源码：I:\CodeX Project\KG3D_Cloth\Build\DisassemblyFleX-AlphaMigration-20261010/baseline/source；冻结DF DLL及原版NV DLL/Ext在baseline/df与baseline/nv。
初始冻结已完成；下文旧断点仅作历史，恢复时以文件末尾最新断点和实际controller/receipt为准。正式src尚未合入，候选均在Build隔离目录。

用户目标：逐alpha版本顺序审计并迁移有效优化；默认不影响计算与表现；只有极大收益且影响极轻微的候选才考虑例外。以实际测量和验收判断，不机械移植所有旧代码。全程允许锁屏。完成后commit、更新HEAD/tag并推送，归档本任务。
全部旧账本/Release/Build报告原样保留。OpenFleX、KG3D_OpenFleX作为只读历史来源；不向它们提交迁移改动。
当前无适用AGENTS.md；禁止未经用户授权的子agent，本任务不派发。
已发现OF与KG3D的alpha2.2至8.2c标签；早期0.1至2.1在Release/ARCHIVED_VERSIONS.csv标为MOVED_TO_DELETED，需继续查Deleted/History而非认定缺失。Release当前可见6.5c起，不能当作全部历史。
所有Git网络操作必须从环境彻底移除GIT_CURL_VERBOSE、GIT_TRACE*、GCM_TRACE*（不能设字符串0，旧Git仍会输出认证头）；捕获输出并脱敏后才显示。禁止打印凭据，禁止强推。用户已授权最终commit/tag/push。
复用前任务纯测量方法可以，但不得直接调用会写旧LEDGER的common.py/build.py/fix_task.py。新工具所有状态只能写本账本和新Build目录。
单GPU共享锁沿用Build/OpenFlexAlpha82c-20260928/gpu.lock；禁止在性能运行时并行编译/重分析；CREATE_NO_WINDOW和SystemRequired，不要求亮屏，不改变系统电源计划。
下一步：补齐0.1起全部版本/标签/归档证据，确定版本和优化顺序，冻结准入协议，再从最早版本开始候选实现/验收。最终报告需列每项采纳/已有/不适用/拒绝/依赖/证据不足。


## 最新断点：2026-10-11，alpha0.1候选验证进行中
- M0发现115个alpha版本/发布变体，从0.1至8.2c。history/version-inventory.json + ledger/versions.json含96类tag来源/旧Release归档/History。1123份文档已复制；无不同source-tree的同版本别名。
- 旧0.1～2.1发布源在Build/WorkspaceArchive-20260905/restic仓库（明确空口令标志），已只读dump到本任务history；21份OpenFleX源码全部按独立manifest SHA256验证(每份1064～1075文件)。未恢复覆盖原Release。源码路径history/alphaX/source/OpenFleX。
- 新tools/alpha_migration/common.py只写新账本，安全Git移除所有trace/curl-verbose变量，隐藏子进程/共享GPU锁。build_candidate.py直接构建独立source快照，不写旧任务账本。两处基础设施问题已修：Git archive不包含空cmake目录；event payload重复time键。编译本身已通过，不重复构建。
- control-v0已构建全部核心/原始oracles，DLL b0e930ed7a22e3115c467a0919aec42c759b975e4cd7e90758bb04182f10e544；84份DXBC与冻结正式DF逐字节一致(evidence/control-v0-shader-audit.json)。
- 统一harness由上一任务已验证版本原样复制：harness/bin/FlexComparisonDemo.exe，SHA b859ce9dcfa4d639e22a90453b1fbfc1e0c4309e1932f93e0e92e5a0418cc88a；35资产复制并核对hash，新demo-stage，所有输出新ROOT。profile/capture协议沿用；没有改变原Demo场景。
- baseline-pilot-d11-v1和d12各54进程(9场景×formal/control/NV×2,360/120,capture1)已PASS执行/有限性/合同。D11正式/重建geo0.9963 CI宽；D12有scene25/r1/formal时钟标记，后续应整组三臂补测保留原记录。pilot只证明流程与初步一致，不是最终排名。
- 首个候选A001-01起源于alpha0.1源码D3D11Backend.cpp:2148 ShapeCount()==0提前返回。a01-empty-triangle-v1只在shape.count && geometry.vertices.buffer时执行CollideTriangles及前一次CB上传；保留counts clear、Shapes/planes、动态布料三角形处理、所有迭代/回调。DLL d123b3f6b0bacb451f792746d464207398252d12f9d3b93951741ea6e79c46eb，编译PASS；尚未接受/合入正式src。
- 当前GPU长链session93800：a01-screen-d11-v1已PASS(20场景×2臂×4,1200/120,capture0)，a01-screen-d12-v1运行中。只做端点/执行筛选，尚需质量/回归与正式候选决策。禁止同时编译或重分析。
- 已准备未运行：index_history_evidence.py(冻结Git bundles、早期源码diff、tag文档/源码diff、后期zip账本、提取未审阅线索，必须GPU空闲后执行)；run_regressions.py(14类原始oracle输出和旧test event均环境重定向到本账本；buffers自己加锁，其他外层加锁；diagnostic timer names/zero-mask会因真实空派发消除而变化，若失败保留并单独审计计时语义，不改原test隐瞒)。
- 已准备未执行的alpha0.2候选工具prepare_a02_descriptors.py：按alpha0.2减少资源操作/提交思路，在DF D3D12保持40描述符内容/排序/资源barrier顺序，只把40次CopyDescriptorsSimple换一次40 source-range CopyDescriptors。其收益需实测；OF没有D3D12，必须标为思路适配而非原代码直接移植。需要先完成alpha0.1验收再选择base。
- 历史alpha0.2包含counting grid、cooperative neighbor、fluid velocity neighbor reuse、PBF substep clear、static CCD、persistent shape buffer、coplanar metadata、spring/Jacobi/rigid融合、uniform/zerooptional/poly6/packed/fluid统计等；不少改变数学或对应旧OF特有成本。当前DF已单次每子步邻域、CSR half-spring、无额外iteration snapshot，因此逐项审计不能直接套入。alpha0.2历史还有明确拒绝的contact reuse、native triangle init等，要保留失败教训。
- 后续潜在数学不变热点（尚未实施/论证）：D3D12 descriptor/barrier batching、每recording资源retain去重加速；D3D11受控窗口内CB/sampler重复绑定（外部context/callback失效必须完整）；substep两次相同CB上传；spring dispatch按max referenced particle缩短空尾部（不能按activeCount简单截断，SetSprings当前全GPU radix，需要额外证明/避免同步回读）；shader/邻域变化必须非常谨慎，不自动接受老OF物理容差。
恢复后先查jobs/controller/PID与session93800，复用所有完成receipt，不重开旧任务。全115版本审计、迁移、全量终验、报告、commit/tag/push与本账本归档均未完成；GO ACTIVE。

## 最新断点：2026-10-11 01:08，A002 barrier候选构建/验证链

- **上面的session93800等均已完成，不要重跑。** 当前新链session41125：构建a02-barrier-batch-v1 → 14回归 → a02-quality-d12-v1（三臂v3/descriptor/barrier，12场景×3，1200帧capture1）→ a02-barrier-screen-d12-v1（三臂20场景×4，1200/120，capture0）。恢复首先读这些controller/PID，禁止重分析/编译与GPU性能同时运行。
- 所有正式PROJECT/src、shader尚未改；候选在ROOT/proposals、sources、builds。正式Git仍51cac80。没有任何候选达到最终全量验收/发布，不要声称完成。
- 新硬件冻结evidence/hardware.json：Win10教育版19045，i5-13600K/20逻辑核，RTX5080/581.15，64GB，平衡电源计划；未改电源计划。I盘余量约1.17TB。
- control-regressions-v1：14/14 PASS。a01-v1原空triangle派发删除导致diagnostic计时名称从4个CollideTriangles合并成1个，原失败回执保留。a01-v2在空路径保留原shader label地址的begin/end计时条目（不发假GPU工作），14/14 PASS，DLL a504429028d0cd3b0b8ff3d3d283aa129e8983765ca2797b290820c405472e3b。
- **A001 v1/v2不限制删除范围已拒绝**：a01-quality-d11/d12-v1各12场景×3对×600 capture1，合同/ID/phase/逆质量相同、确定性场景精确，但D12 scene0在600帧出现稳定微差。追加a01-d12-scene0-investigation-v1：formal/control/v1/v2四臂×8×1200。v2自身位置RMS最高0.0706447，control自身仅0.00024855，额外波动超出控制。不能用candidate自身噪声作baseline！即使84shader完全相同、API全PASS，也不因~1%收益启用微差例外。
- **A001 v3**：仅当无springs/rigids/inflatables/dynamic triangles/maxDiffuseCapacity且缺shape或triangle vertex storage时省空派发；否则保留原GPU命令序列。工具prepare_a01_conservative.py。14/14 PASS，原84DXBC完全一致。a01-v3-quality-d11/d12-v1各12场景×3对×1200 capture1：参数/合同/ID/phase/逆质量、finite均PASS；D12 scene0恢复24/24逐字节相同；17/33/47/52等确定性路径全部exact，其他布料原自身非确定性仍明确保存。尚需最终全场景/输出域等门。
- A001 v3性能：a01-v3-screen-d11-v1 20场景×4对，geo控制/候选1.00187338，CI[0.99956310,1.00418900]，D11无统计显著全局收益。scene18/r3/control出现时钟标记，已**整对补测**并保留原receipt，evidence/a01-v3-screen-d11-v1-replacements.json。
- A001 v3 D12性能在a02-screen-d12-v1三臂：20场景×4，control/v3 geo1.00483391 CI[1.00105845,1.00862361]，~0.48%小收益；Holm20场景均不分离，不能夸大每场景。
- A002-01 descriptor：prepare_a02_descriptors.py --base a01-empty-triangle-v3；构建a02-descriptor-batch-v1、14/14 PASS、84DXBC exact。20场景×4对v3/descriptor geo1.01148035 CI[0.99976950,1.02332837]，~1.15%方向但尚跨1，**暂不是确定获胜**。下一三臂质量/性能链继续验证，没有采纳例外。
- A002-02 barrier：prepare_a02_barriers.py保持全部40 SRV/UAV transition顺序、UAV barriers、keep/fence/lifetime，只用prepareTransition聚合数组一次ResourceBarrier，copy/clear/indirect其他路径不变。Microsoft官方API明确数组等价按序N次调用，链接见evidence/barrier-batching-reference.json。该工具已运行，当前session41125验证。
- 已写未运行prepare_a06_cpu.py：--kind shader-names（std::less<>透明shader-map查找+bounds/rigid固定字符串，避免每pass临时std::string）、retained-set（D12 std::set→unordered_set，成员容器不迭代，retained vector原先后保持）、ipo（Release GL/LTCG/Gy/Gw，保留fp:precise）。三项必须独立增量实测再组合。当前不要跳过alpha0.3候选家族决策直接宣称全部移植。
- 已准备下一alpha0.3深层无损候选家族但**未实现**：spring空尾按最大引用spring粒子ID裁剪原512thread/8lane shader。不能用activeCount裁剪。SetSprings全GPU排序，建议在排序后tiny integer辅助shader读front.key[2*nSprings-1]生成DispatchIndirect args，旧SolveSprings shader保持原样、包含所有非空CSRrow；须证明空行无UAV写、无CPU回读/同步、invalid/sparse/highID/resize/clear/multisolver/copy合同行为及稠密路径成本。原75smasm已证明空row不写。是否实际值得做需测量，尚无工具或新shader。
- 历史审阅：history_decisions.json已有173项；record_early_audit.py(0.2/0.3,38)、record_a04_a06_audit.py(44)、record_a07_a18_audit.py(33)、record_a19_a20_audit.py(23)、record_a21_audit.py(35)。审阅游标alpha2.1，下一alpha2.2。记录含已有/不同架构/改变数学或cadence/历史失败/可实验家族，**所有candidate-family仍待明确关闭或实现**，不能只生成标签就算全完成。
- 特别历史结论：OF alpha0.4、2.1多项大GPU提速来自降rigid/contact/aero频率和跨帧neighbor缓存，这不满足本次结果约束。alpha1.7曾因省identity Body派发暴露浮点轨迹残差，与A001教训一致。alpha2.3历史明确拒绝2.1的降频，只保留精确数据优化。最新阅读了2.2恢复/生命周期、2.3 W20/21接受、W22/23缓存拒绝、W6 active-prefix接受、W19依赖静态拒绝；2.3后半GPU段/2.4/2.5系列只看了标题和差异清单，尚未登记决策。
- 历史索引修正：原KG Git diff误用根src/shaders，实际源码嵌在OpenFleX与KG3D_OpenFleXBody。repair_history_deltas.py已完成94条修正，旧错误filter patch保留*.initial-root-filter.patch，新的KG3D_OpenFleX-code.patch才权威，history/corrected-source-deltas.json含hash；同时补alpha2.1 restic源码→alpha2.2首Git tag的源码差异。**旧KG patch=0不能当代码没改。** index_history_evidence.py已修正root filter、段落真实line计数、关键词边界，但还没整体重跑paragraph index；当前optimization-evidence.json旧line不要用作精确行号。
- alpha1.9 patch大部分为NvFlex→OpenFleX重命名；已生成仅供审阅的rename-normalized-review.patch，未改原source。剩余包含FL11.0第9UAV修复(DF原8槽无需移植)、OF短边补偿器和诊断，不误称纯打包无代码差异。
- 质量工具增强：quality_analysis检查position.w finite并比较inverse mass；assess_quality输出逐场景cross与**分别的control/candidate self**，以及每帧min/maxY、速度、应变、plane penetration。不能把二者self合并阈值视为证明。历史旧分析可保留，最终用新工具。
- 统计工具修复：clock exclusions含被排除整场景；repeat panels不齐时不出aggregateCI，equal-scene geomean真正等权；zero-stdev+zero-effect p=1。retest_clock_blocks整组补测。baseline-pilot-d12 scene25旧标记也已整三臂补测，当前九场景全部纳入，formal/control geo1.01882 CI[0.92565,1.12137]，仍仅pilot。
- 工具run_regressions现有任一失败会exit1，后续链不继续性能；旧v1 diagnostic FAIL不隐瞒。common.py强制UTF8 stdout（之前中文乱码仅终端编码，文件原字节未坏），增加BOM/GB18030读旧文档fallback。review_history.py是阅读助手，不自动验收。
- 下一步：接续session41125；确认A002质量/统计后裁决descriptor/barrier，A001 v3按最终广域数据裁决；完成alpha0.3候选家族和后续CPU项。并顺序审阅剩余94版本(alpha2.2..8.2c)、解决所有pending families，最终67场景两后端+发射+长程+资源/ABI/公开输出域回归、整合正式源码/DLL、详细中文报告、归档、commit/tag/push仍全部未完。继续GO，不终止、不标complete。

## 最新断点：2026-10-11 01:25，A003弹簧空尾实测链

- session41125已全部完成。A002两项分别的CI仍跨1，但**组合**a02-barrier-batch-v1对a01v3的20场景×4配对geo=1.0128819905，95%CI[1.0066468848,1.0191557160]。独立Holm场景均不分离。质量12场景×3×1200全部合同/ID/phase/mass/finite通过；确定性场景exact。scene0末帧微差0.00024855 RMS与此前control自身8次重复已观察值完全相同，未扩大到被拒v1/v2的0.07量级。原84DXBC exact。账本A001 v3及A002组合记provisional keep，仍待全量终验，不能说单独descriptor或barrier已显著获胜。
- A001 v3 D11时钟整对补测完后geo=1.0018733786 CI[0.9995630967,1.0041890003]；无全局统计显著收益。D12原先0.48%仍有效。baseline pilot D12旧标记也已三臂补测，不再欠补测。
- **A003已实际实现，不再只是提案**：prepare_a03_spring_extent.py，base=a02-barrier-batch-v1，候选a03-spring-extent-v1。GetShader可从新增辅助registry解析helper；新shaders/auxiliary/SpringDispatchArgs.hlsl只用整数从SetSprings的已排序endpointKeys末项生成ceil((maxID+1)/64)间接参数，原032/075 Spring程序完整保留。原始84shader registry与manifest不变，新helper独立aux_shader_manifest.json、DXBC/asm。helper仅17个integer/control/store指令，无浮点运算。
- A003只在SetSprings时capacity>=16384且activeCount==0或<=capacity/2生成helper参数；Update每轮仅在参数ready、capacity/count匹配且activeCount仍<=capacity/2时用原spring shader的DispatchIndirect，否则direct全容量。bound来自实际最大spring引用，**不是activeCount**，sparse高ID不裁掉。零count立即ready=false；CopySolver前关闭private bound缓存；ownedBuffers/ownedConstants拥有新增args/CB。无CPU读回/扫描/同步。
- 编译PASS，DLL SHA256 26ce771abde1a1d3d77e008337cd14d98f104203709cfd50ee301232bfa33384。a03-regressions-v1=14/14 PASS；audit_shaders原84 exact。新tests/spring_extent_oracle.cpp来自tools/alpha_migration/templates，用实际DLL做16组D11/D12×generic/NV×low/sparse-high/small/dense用例，32次GPU bound读回验证。12帧中SetSprings16→64→0→32→64，比较5个时点全容量positions+velocities：**全部逐字节一致**。a03-spring-focused-v1回执PASS。辅助shaderinvalid endpoint fallback虽代码保守，但专项非法输入helper测试还没做，不要声称覆盖。
- **当前运行session74702** 顺序：a03-target-d11-v1与d12（scene64/65、2400/warm240、6对、capture0）；a03-quality-d11-v1与d12（0/25/29/64/65、1200、3对、capture1）；a03-emission-d11-v1与d12（64/65、1800/warm120、3对、capture1、emit）。先查实际controller，复用PASS，不重跑。尚未做A003统计/质量分析或accepted决策。
- 目标来自原FlexDemo真实scene64/65：初始3072 active、capacity68608、29718 springs；别的标准cloth多为capacity==active，A003保持direct。scene29 tearing1681/2681且容量小，保持原路径。没有改Demo资产/粒子数/参数以制造收益。
- 预备后续更深入且可能数学不变的**未实施**思路：alpha0.3 C09 plane-only specialization。原070_g_Flex_CollideShapes.smasm仅一次`if_nz cb0[26].x`(约382行)，控制全部primitive/BVH/SDF块；kNumShapes来自KernelParams.cpp32的shape.count。可在真正上传kNumShapes==0且无callback干预时使用新增aux程序，删除这个已确定不执行的完整if分支，保留其余原指令/FP顺序、原label pointer与原84通用fallback。用DXBC assembler+Lifter配对恢复辅助源，不能通过FXC重排活跃浮点。必须验证if匹配/else、shader标签API、0/1形状切换/callback及每个active输出，再实测，不保证值得做。
- 另一**未实施**思路：参考alpha2.4 W33线程组占用率，把原8lane/particle spring的512线程组试256，原032/075组内通信仅每8lane；作为新增aux派生kernel保留84fallback，除dcl_thread_group与TGSM长度外全部运算指令一致。host除数及A003helper args的每组粒子数须同步，并重新跑稀疏oracle。此项属于alpha2.4，先完成前序候选/CPU优化再做；没有代码/数据。
- 历史已详细读到alpha2.4但**登记游标仍2.1**：2.2主要KG capsule事务发布、lifetime pin、GPUrequested fail-closed；2.3 W20查询池/W21spring CB/W6dense extent/W24transient prefix copies/W25neighbor CB接受，W22各pass缓存/W23solver+contact缓存失败，W19依赖降频静态拒绝。2.4 W33 spring64→128、W37rigid apply64→128、W38CSR normals64→128、W42moveLimit64、W43Deform64接受；W30/32/34/35/36/39/40/41/44失败，无approx。2.5..2.5d仅标题/patch统计初览，未细读/登记。
- 工具更新：build_candidate.py发现tests/spring_extent_oracle.cpp时自动构建该target；run_spring_extent_oracle.py GPU锁+SystemRequired+300s超时输出新账本。辅助构建脚本只在proposal里生成，不应误把原84验证器改成85；最终报告需明确哪些新helper是自写优化、哪些原程序保持。
- 下一步先分析/裁决A003，必要时profile1单独归因原Spring timer，再推进C09和alpha0.6三个CPU候选；继续94剩余版本登记与所有pending-family关闭、最终全量回归/性能/报告/commit/tag/push/归档。GO ACTIVE。

## 最新断点：2026-10-11 02:30，A006四项独立CPU候选性能筛选

- **当前运行session83871**：a06-screen-d11-v1（a03-spring-extent-v1 / a06-shader-names-v1 / a06-ipo-v1 / a06-bindings-v1）；随后a06-screen-d12-v1（a03spring / shader-names / ipo / retained-set的-d3d12 variants）。每API20场景×4臂×4repeat、1200/warm120、profile0/capture0。先查controller/PID，不要重跑或与编译/重分析并发。
- A003弹簧候选**provisional keep**：scene64/65六对2400帧完整帧速度比D11=1.030618669 CI[1.023100795,1.038191785]，D12=1.037710230 CI[1.030834063,1.044632265]。D12 scene64/r2 clock标记已整对补测并留原receipt。注意只代表两目标场景，不是67全局。
- GPU归因a03-profile-d11/d12-v1全部PASS，分析a03-spring-gpu-attribution.json：SolveSprings帧内聚合均值D11约0.0961373→0.0608124ms、D12约0.0676292→0.0289682ms。profile有观测扰动，只作归因，正式排名用profile0数据。
- A003正式质量与持续发射（64/65、1800帧，3072→45372 active）主state位置/速度/ID/phase/逆质量均逐字节一致。新compare_aux_outputs.py审了params/rigids/triangles/render(法线、smooth、aniso)/diffuse所有已捕获域。D11目标场景render微差仅normals，最大1.788139e-7，与两臂自身重复完全相同；其余render字段exact。D12这些域全部exact。D11 diffuse数组顺序不同：diffuse_quality.py按完整8float多重集和无ID空间分布比较；scene65全部24/24多重集exact，scene64饱和32K容量时12/24exact，其余最近邻mean/p95在baseline自身波动范围，counts和平均lifetime相同。不能声称所有diffuse粒子按下标相等或所有值全局bit-exact。
- D12两场景diffuse数量0曾触发原版复核：nv12-diffuse-reference-v1两场景1800emit已PASS，**原版NV D3D12末帧也是0**，是现有模式边界，不是本轮优化删除水花。回执原样保留。
- A003-02 plane候选已完整实现/实验并**REJECT_PERFORMANCE**：a03-planes-v1 SHA c560d66f17aeb77bb3ea54ae8e48ca3a2bcf58e8a21027e0286eb5c9f3206ddc。prepare_a03_planes.py从原070抽取并删除唯一if_nz cb0[26].x完整false分支（无else），只减未使用stack/temp声明，剩余活动算术指令与顺序完全保留；原84不变，新aux派生HLSL/smasm+manifest单独存在。保留原shader label pointer；仅shape.count==0、上传的kNumShapes==0、无callbacks选用。14回归PASS、144 D11/D12直接kernel差分（counts/planes/velocities、0/1/3/8planes、active0/1/127/128/129/257、contacts1/6/16、ULP阈值、原有contacts和尾部哨兵）全部bit exact；9场景×3×1200质量PASS。
- plane 20场景初筛D11修复2个clock整对补测后geo1.00153801 CI[1.00014125,1.00293673]，各场景均不分离；D12geo1.02100 CI很宽跨1。对真正适用25/28/47再做**预定8对×2400**确认：D11geo0.99927401 CI[0.99556383,1.00299802]且一场景Holm确认更慢；D12geo0.99777972 CI[0.99337903,1.00219990]。没有可靠收益，已舍弃。**后续所有候选base均a03-spring-extent-v1，不要带入plane程序。** plane相关源码/二进制/证据作为失败实验保留，不合入正式src。
- plane初次准备缺cs_5_0标头导致Lifter在编译前报错，已修并写event；proof的original_source_sha256最初是规范化文本hash，已改为真实文件字节hash并另存normalized_text_sha256，源/程序未因这次元数据修正改变。
- **A006四项相互独立**，均以a03spring为base：
  - A006-01 a06-shader-names-v1：shader std::map用std::less<>透明查找；bounds/rigid shader名称由拼std::string改固定const char*，保持NV/AMD优先级/每个名称完全相同。
  - A006-02 a06-retained-set-v1：D12 retainedSet由std::set换unordered_set；只做membership、不迭代，retained vector首次使用顺序、AddRef/fence/lifetime不变。
  - A006-03 a06-ipo-v1：/GL+/LTCG/Gy/Gw/REF/ICF，仍fp:precise，未改HLSL/原84指令。
  - A006-04 a06-bindings-v1：新prepare_a06_bindings.py。D11仅在无任一solver callback、numParticles>0的Update内RAII begin/end scope；首次完整32SRV bind/unbind建立全空证明，后续只省已空SRV尾部；**全部8UAV绑定/解绑原样保留**。同scope CB0/CB1与sampler重复绑定可省，但map/unmap/copy常量、ClearState、updateContext、contextPush/Pop、scope进入/退出全部失效。CB空参数保留原继承行为。无改变shader/dispatch/物理频率。
- 上述4个生产build和a06-bindings-validation-v1诊断build均构建PASS、**各14/14原始回归PASS**。诊断编译选项DISASSEMBLYFLEX_VALIDATE_BINDINGS=ON会在实际native context查询/核对每dispatch SRV/UAV/CB/sampler及解绑后全空；a06-bindings-native-validation-v1 22场景×600 capture1全PASS。诊断DLL绝不能排性能名次。
- 工具build_candidate.py新增--cmake-arg，receipt记录参数且复用构建时严格核对；register标diagnostic_only。run_matrix禁止诊断DLL以profile0/capture0跑性能，analyze_primary拒绝诊断臂。普通构建参数默认[]，旧构建可复用。工具common.event改首参event_type，并把payload.kind保留为subject_kind，修prepare_a06_cpu事件同名参数冲突；首次失败发生在准备末尾，源码/账本已写，无重复编译。
- M1当前**39/115版本、218条idea**，游标alpha3.0c，下一alpha3.1。新增record_a22_a25d_audit.py(32)、record_a26_a30c_audit.py(13)。alpha0.4 E08 phase-first已通过原058源码确认**DF本来已具备**（先phase/group/rest过滤，再读candidate position并算距离），已从candidate-family修为already-present；C09关联被拒A003-02；extent家族关联A003-01。
- KG路径在alpha2.9又从KG3D_OpenFleXBody改成KG3D_OpenFleX，之前嵌套root修正仍漏后期Body。现index_history_evidence.py/repair_history_deltas.py都改为**完整Git树diff**（仅省generated headers，完整bundles/changed-file list仍保留），**187条修正已运行完成**，history/corrected-source-deltas.json是最新；旧过滤版保留*.previous-filter.patch / *.initial-root-filter.patch。不要用旧patch=0宣称core/body没改。alpha2.2 release→first-tag桥接仍保留。
- alpha2.6线性authored vertex/soft-cluster逆映射属KG，DF无该映射层；构建期DXBC DF早已有且本轮helper也离线编译。2.7~2.8为bootstrap/history handoff/moving rigid centers/u2 alias/singleton island输入修正；2.9 native VS/Debug if constexpr guard、2.9b前缀改名；3.0/3.0b/3.0c为graph初始化marker、host-specific zero-delta和STANDBY restore。均逐版本记录并对照两repo差异，不把应用层修复移成DF新物理方程。
- **后续未实现的深入候选**：alpha2.4 W33启发spring group512→256，保留8lane粒子归约和全原活动指令，仅改group/TGSM声明，可新增aux而保留84 fallback；A003 args从64粒子/组同步到32，专项oracle期望同步并重新比较完整输出。按版本顺序在A006等前序决策后做。其他candidate-family（uniform特化、sphere-cell cull、shape内容cache等）须明确静态关闭或有证据实验，不能留pending冒充完成。
- 正式src仍未合入，Git仍51cac80。全115审阅/剩余家族决策、最终67场景两后端+持续发射/长程/公共输出/资源/ABI门、正式组合源码/DLL、中文详细报告、归档、commit/tag/push仍未完成。持续GO，禁止提前complete或final停工。

## 最新断点：2026-10-11 04:05，A037运行 / 最后一组候选准备

- 当前正式src仍未合入，基准HEAD 51cac80；累计候选base为a06-combined-v1（A001v3+A002两项+A003 spring extent+A006 names/retained/bindings）。IPO、planes、A021、A024均拒绝，不得带入。
- A006组合20场景4对：D11速度比1.003669729 CI[1.000745215,1.006602789]，scene47约0.94%回退须最终复核；D12 1.017697471 CI[1.006039716,1.029490314]。CPU profile4证明binding/lookup/retained提交周期下降，不能当GPU或游戏FPS。
- A021重复constants上传：两API无可靠收益，已拒绝。A024 spring256：两API9场景各4对速度比0.997132/0.998332，区间跨1，直接spring oracle及14回归通过但无收益，拒绝。
- A037 distance/fullrow 两独立候选各14回归及450直接kernel差分通过（rows/count/tail bit exact），build SHA及source在evidence。session81669串行跑a37-screen-d11-v1和d12-v1，各20场景3臂4对1200/warm120。勿并发编译/GPU。
- 新prepare_a39_dead_stream.py：尚未执行，原032/075未读t0的HalfSpringIndices分配/绑定移除。新prepare_a82_radix.py与4个Radix8*.hlsl、radix_extended_oracle.cpp已写，尚未执行/编译/测试。八位候选仅keys对齐1024、2048..1M、bits24/32，前16bit用两次8bit，其余原4bit，保持back/front最终物理内容；hist/scan/scan-sums/stable-bitset scatter。必须测试后才能声称正确/收益。
- 历史审阅已到全部115版本末alpha8.2c；record_a67_a82c_audit.py新增52条，合计391条历史ideas，alpha0.1单独optimizations关联。未最终关闭candidate-family与版本状态。需具体对应实际实验/适用性，不可泛称全部有效优化已移植。
- 下一：完成A037质量/计时决策；A039/A082独立实现验证；最终仅赢家组合正式src，fresh build，67场景双API生产配对与另跑质量、持续发射、长程、全部API/resource/aux输出；中文报告/归档/commit/tag/push。持续GO，不得提前完成。

## 最新断点：2026-10-11 04:24，最后候选性能运行中

- 活动会话5877运行run_last_candidates.py；jobs/last-candidates-pipeline.json PID4704。当前last-screen-d11-v1（PID17624），随后d12：a06-combined-v1 / a39-dead-stream-v1 / a42-packed-springs-v1 / a82-radix-v1，各20场景4臂4对1200/warm120；不要并发GPU、编译或重分析。原session59079因NV私有接口专项已退出失败，失败receipt单独保留。
- 会话44972运行run_followup_candidates.py（PID15896），等待上述pipeline PASS；随后对A037与last各API做完整时钟标记block补测及重分析，A037-distance双API9场景3对1200质量+aux、D12三场景3臂2对360 profile1归因。请先核对两个pipeline状态，避免重复启动。
- A037-distance/fullrow均14回归+450直接kernel差分PASS。20场景screen已完成：distance初步geo D11~1.00368、D12~1.00473，但少量clock block待补测，整体CI暂不给；fullrow D12约0.9617且多场景明显回退，不考虑保留。最终决策待补测/质量。
- A039：删除原032/075完全不声明或读取的HalfSpringIndices分配和t0绑定；14回归、16 spring full-capacity byte cases/32 args checks及84容器exact全PASS。逻辑存储省4*half-capacity bytes，不等于已测driver峰值显存。
- A042：基于A039，把opposite/rest/stiff三个4B流改为精确12B结构，原SpringsReorder按0/4/8byte写同样bits；两个派生SolveSprings只有metadata load/mov改变，原全部浮点指令和八lane树不变，原84保留。14回归、加强到512约束/混合正负与+-0刚度/高连接度的16 sparse/dense/highID cases逐byte PASS，84exact。是否保留仍待性能/全仿真质量。
- A082：base仍a06组合。仅2048..1M、1024整块、bits24/32，用两个稳定8bit pass替代低16bit的4个4bit pass，然后执行原余pass；4个新增纯整数HLSL，front/back最终物理内容与counter parity保留。162组both-API差分覆盖0/小/非整块/1M、bits0/4/16/20/24/28/32、随机/重复键、重复混合调用，stable CPU顺序+两侧完整buffer/tail均PASS。
- A082初次14回归中的扩展radix oracle在原NV D12路径abort 0xc0000409；D11两容量81cases已PASS。独立instrumented exe再次NV-vs-NV只backend2在reference阶段同样abort，候选未开始；DF a06-vs-a82两个API162cases全PASS。证据diagnostics/radix-extended/df-candidate.json，logs/radix-diagnosis-nv-self-d12.log，jobs/radix-diagnosis-*.json。原失败保留，不称NV私有D12专项通过。run_regressions新增显式--radix-reference-build，仅此gate用冻结a06；其余13门仍原NV。a82-radix-v1-regressions-df-radix 14/14 PASS。pipeline已按新名续跑，禁止抹原失败。
- 历史最后20版本52条已记，全部115版本审阅至8.2c。close_eligibility_review.py关闭uniform-fluid、sphere-cell cull、capsule-static：DF缺可靠来源/dirty/浮点保守界证明，保持原行为；不是断言普遍不可能。A042覆盖4.2/7.3精确打包族；A082覆盖8.2稳定radix族。最终统一关联各family/版本status尚待做。
- 新工具analyze_gpu_details.py（profile1仅归因、速度比CI经exp转换）与quality_flags.py（严格输出和独立baseline repeat包络审阅flag，不能自动放宽或接受）已写。A006 D12 CPU4补测后分析仍需重算names/retained以使用mapping。
- 正式代码仍51cac80未合入。最终仅赢家组合、新鲜构建、双API67场景/持续发射/长期/ABI资源/公共输出/中文报告/账本归档/git commit tag push均未完成；持续GO，不得提前final或complete。

## 最新断点：2026-10-11 04:43，收窄A037后的最后准入验证

- 5877 / last-candidates-pipeline于04:35:59 PASS，44972 / followup-candidates-pipeline于04:39:41 PASS；旧等待进程均已完成。当前唯一作业session56586，run_remaining_validation.py，jobs/remaining-validation-pipeline.json。先查状态/PID，禁止与GPU性能/编译并发。
- A039/A042/A082两API20场景四臂四对1200全部PASS，无clock flags。A039与A06完整帧CI均跨1，仅作为逻辑内存省4*half-capacity bytes的provisional keep，不声称整体FPS提升。
- A042必须按自身base A039比较：D11 geo1.0033289108 CI[1.0000350531,1.0066336176]，无scene Holm分离；D12 geo0.995048978 CI[0.9930046975,0.9970974670]。已REJECT跨后端performance，后续不得合入packed shader/stride12。
- A082与A06全20场景总体CI跨1，不宣称普遍提速。对齐数量的25/27/64/65有局部收益，D11 coupling约1.5–1.7%，D12约2%；仍provisional pending质量/组合67终验。162整数排序对照及14门显式radix DF控制PASS；原NV D12私有fixture限制仍保留。
- A037完整时钟block补测/重分析已完：distance全范围D11 geo1.0032685948 CI[0.9987236668,1.0078342056]；D12 geo1.0042329354 CI[0.9968281508,1.0116927253]，全局不显著，scene9/28局部快。fullrow拒绝：GPU profile1 D12 CollideParticles scene9 .0953843→.248203ms，33 .0455825→.122339，52 .0459999→.152866；450直接输出exact但GPU更慢。Control flow/reconvergence可能原因，未采硬件stall/occupancy计数，不能断言具体机制。
- A037-distance-v1全仿真质量：strict contracts/IDs/phases/mass正常，9/47/64/65等确定域一致；cloth23/25/27/28原重复RMS本已较大，部分候选波动超出有限baseline观察包络。没有以候选噪声放宽阈值，也未用数值例外。**保守收窄**v2：有spring/inflatable/dynamic triangle/任何diffuse capacity时选原058；只在这些均0时用distance-first。scene9 Plastic Bunnies确实2440active/0spring/0tri/1050rigids，保留目标收益。旧v1完整scope已记previous_trials rejected-unrestricted-scope。
- a37-distance-v2已build SHA cffc5a20ada34fb09d00cbeabcfcb5c2bb8672aba812ae7599199d63936407cf，14门+450kernel+84original容器全部PASS。prepare_a37_restricted.py只改选择条件，原/derived程序不变，无scene-ID判断。
- 当前remaining pipeline每API先a37-v2-confirm（A06/v2，scene9/47，6pairs2400/warm240，clock整对补测、分析），然后remaining-quality（A06/v2/A82，10scenes0/9/23/25/27/28/33/47/64/65，3repeats1200 capture1）及state/aux/quality_flags；最后a82-attribution profile1 scenes25/33/64，2pairs360。若失败先保留/解释，不能盲继续。
- CPU4历史补测后的A006 D12分析已重算，正确suite名a06-cpu-counters-d12-v1：retained Solve cycles速度比1.0492738 CI[1.0396549,1.0589817]，Whole1.0430972 CI[1.0331025,1.0531886]；names Solve1.0262996 CI[.9937056,1.0599628]，Whole1.0169631 CI[.9875089,1.0472959]，**D12 names CI跨1**，不要沿用旧更强结论。D11 names/ bindings此前正CPU证据仍保留。
- 新compose_reviewed.py可在共同A06 base上干净三方合并不同文件段，registry按name并集且拒冲突；新增--split-radix-oracle会恢复原NVIDIA D11 inherited radix测试，将162例放独立tests/radix_extended_oracle.cpp与DisassemblyRadixExtendedOracle目标。build_candidate已支持此新target；run_extended_radix_oracle.py显式DF control。若A82最终保留，用此分拆以不改变原14门默认语义。工具已写，**尚未执行组合**。
- 下一：读remaining结果并决定A037v2/A82准入；理想候选从a06-combined-v1组合a37-distance-v2,a39-dead-stream-v1,a82-radix-v1（不含A042），需要fresh集成build+14NV门+450neighbor+16spring+162扩展radix。正式PROJECT/src仍未修改、HEAD仍51cac80。再完整双API67场景生产配对（建议df/control-v0/final三臂4repeat）与独立质量、持续发射、长期、公共输出/资源、报告/历史family全部关闭/归档/commit/tag/push。GO仍ACTIVE，不能提前final/complete。

## 最新断点：正式源码已合入、final-v1专项通过，终验队列已启动

- integrated-v1由compose_reviewed.py在a06组合上合并a37-distance-v2,a39-dead-stream-v1,a82-radix-v1，registry6项（1整数spring args、1原058派生distance、4整数radix）；A042/IPO/planes/fullrow/constant/group256均未纳入。三方合并已逐源段复核，原84不变。
- integrate_candidate.py已将27个实际变化文件写入正式PROJECT，保留无关文件。fresh build **alpha-migration-final-v1** SHA256 **5e3a2f61633aba938dc48ea61b9a9f5adefaea047c8cd553a5c8f8453e46e397**；Ext仍c448c3...。14原NVIDIA门全部PASS（原D11 radix入口已恢复，非换基准），额外16spring/32args、450neighbor、162 DF+CPU bothAPI radix与84original容器exact全部PASS。session79514已完成。
- remaining-validation-pipeline于04:49:58 PASS，session56586完成。A037v2独立确认：D11两场景geo1.007608 CI[1.00059949,1.01466560]；D12geo1.01618386 CI[1.01173485,1.02065243]。确定域scene9/33/47/64/65，两API各24/24状态exact，aux scene9 render/rigid等exact。D12scene0 v2一组.00024855等于baseline自身，A82全部exact。
- 不得把quality_flags的三重复最大值当总体上界：A037v2在已禁用优化、保留原058的cloth23/25/27/28仍有波动，说明有限重复统计需要补独立原始基线，而非放宽候选容差。原params各快照exact，wind按g_dt推进，未发现不同输入。原有flags/拒绝结论原样保留。02_BASELINE_VARIABILITY_ADDENDUM.txt在新cohort前声明：只跑df/control-v0（各原始/同源码无变化版），两API scenes0/23/25/27/28/64、各8repeat×1200 capture1，all-pair自比；不含候选，不作性能排名、不引入近似许可。
- **当前session72347** run_baseline_negative_control.py，jobs/baseline-variability-pipeline.json；先检查PID/status。characterize_baseline.py输出独立各variant全部自比对的per-snapshot与all-frame包络，现有三重复结果不被覆盖。
- **当前session1352** run_final_validation.py，jobs/final-validation-pipeline.json，等待上述baseline pipeline PASS且专项门PASS后自动开始。最终脚本顺序：两API full67 production，df/control-v0/final三臂×4pairs×1200/warm120；整clock block补测和两种对照分析；之后每API full67质量 df/final×3pairs×1200 capture1；emit36/39/40/64/65/66四对1800生产+三对1800质量；long0/9/25/27/47/65三对6000 capture1；final CPU4八场景四对1200及clock补测/归因。所有GPU任务串行，不要另起重复队列/并发编译。脚本PASS仅代表执行完，数值flags/原有波动/退化/发布仍须审阅，不能自动complete。
- 新工具finalize_history_decisions.py已写但未运行，要求每candidate先accepted/rejected，再把16个family逐一连到真实实验、逐115版本关闭。8B spring palette未实测，必须如实注明OF RTX历史无可靠收益和DF缺host palette来源证明，不能用12B测试冒充8B覆盖。
- 后续主要工作：审阅独立基线与最终全部结果/失败/clock与diffuse输出；必要修复并新build重测；完善prototype/final变化归因、完整中文HTML/TXT报告和115版本391ideas表/CSV；交付DLL/source证据哈希；candidate最终决策与历史关闭；归档账本；git commit/tag/push并验证。Git HEAD仍51cac80，尚未commit或push。GO ACTIVE，不得提前final/complete。

## 最新终验进度：2026-10-11T05:27:53+08:00

- baseline-variability-pipeline已于04:59:37 PASS，session72347完成。独立原始/无改动控制各8repeat全自比结果在analysis/baseline-variability-*-independent-baseline.json，原三重复flags不覆盖。示例D11原df自比position RMS最大：scene0 .0075384、23 .9652145、25 .3212103、27 .8141474、28 .1240903、64 0；control-v0 scene27 1.0091735。D12 df12：0 .000248551、23 1.0341581、25 .3106683、27 1.0928463、28 .1141843、64 0。基线存在这些自然波动，仍不可混入候选噪声设阈值；最终输出须按每场景/快照/结构指标审阅。
- 当前唯一GPU总队列：**session1352 / PID22492 / jobs/final-validation-pipeline.json**，04:59:39开始。D11 primary全804进程PASS，无clock补测。D12 primary当前已过第一轮，继续自动执行后续质量/emit/long/CPU。不要再次启动脚本副本或与GPU编译/重分析并发。
- **最终D11 primary已出**：df/final geo1.0117263316 CI[1.0097619084,1.0136945765]；control-v0/final 1.0104983827 CI[1.0083186573,1.0126828201]；df/control 1.0012151913 CI[.9974912025,1.0049530831]。相对df Holm11更快/56不分离，没有Holm确认回退；相对control8更快/59不分离。所有输入契约、初始params、有限状态检查通过。只代表D11完整帧，目前不能给最终总体结论。
- A082 GPU归因已完整：SortCellIndices profile1 scene25/33/64，D11分别.135586→.115738/.135879→.125598/.202677→.173474ms；D12 .0843054→.0696003/.0860388→.0796173/.1280534→.1046645ms。因为profile每dispatch放query而新实现dispatch更少，这些阶段比率包含观测扰动，只归因，不冒称纯shader/游戏FPS收益。
- make_report.py已写且AST解析通过，**未运行**。它要求evidence/final-review.json statusPASS、unresolved_issues=[]、candidate/tag/outcome_notes/implementation_notes/performance_notes/quality_notes/limitations及对每个优化ID的中文candidate_notes；并要求全部versions review-complete与opts accepted/rejected。输出PROJECT/ALPHA_MIGRATION_REPORT_CN.html/.txt、PROJECT/reports/alpha-migration-20261011/CSV/JSON和ROOT/delivery/REPORT_CN.html/.txt，带67场景表、115版本逐项可筛选表、方法/新增shader映射、原失败边界、复现/原始数据链接。生成前必须真实审阅全部最终数据，不能填假PASS。报告生成后还要检查链接/结构/所有数字与中文，准备交付DLL/manifest/归档。
- state.current_candidate已改alpha-migration-final-v1，M3/M4进行中。M1/M2仍待统一决策关闭；所有原候选的accepted状态需最终验收后写，A042/fullrow等已rejected。正式代码已修改27文件，HEAD仍51cac80未commit/push。source DLL5e3a2f...与原Extc448c3...为当前唯一终验对象。GO ACTIVE，继续直到质量审阅、报告/完整性、账本归档和commit/tag/push远端核验全部完成。

## 最新结果与必须解决的疑点：2026-10-11T06:09:47+08:00

- final-primary两API均804进程PASS、clock标记0。D12 df12/final geo **1.0470068677 CI[1.0435008088,1.0505247066]**；control-v0-d3d12/final **1.0479774342 CI[1.0447754610,1.0511892206]**；df12/control .9990738670 CI[.9962708221,1.0018847984]。Holm相对df20更快/47不分离，相对control17更快/50不分离，无Holm确认变慢。D11此前1.0117263已记录。
- 但负向点估计必须复核：D11 scene31 .98930775 CI[.9848546,.9937810]、17 .9939299 CI[.9906049,.9972661]；D12 scene44 .94871775 CI[.9033800,.9963308]、33 .9821095 CI[.9681260,.9962949]、31 .95618区间很宽。不能用整体收益/未过Holm掩盖可能的局部退化。
- **追加串行session82428 / PID19796 / regression-confirmation-pipeline.json**：等待final-validation-pipeline PASS后，D11 scenes17/31，D12 31/33/44，8对2400/warm240，五臂df、a06combined、a37v2、a82、final；整clock block补测；df-final/a06-final/a06-a37/a06-a82分析；同场景2对360 profile1归因。当前WAITING。此选择已写predeclared event，原67场景数据保留。
- final-quality-D11已402进程PASS，201配对/2010快照对、全contract true、nonfinite0、ID/phase/inverse-mass全部相同，43/67场景24/24状态bytes exact。多数其余场景原版也有波动，但**scene3和56仍是未解决质量疑点**。scene3 Soft Rope：原3次自比0，只有候选repeat0自240frame起非零，最终posRMS约9.99455e-5，另两对exact。scene56 Rigid8：三对0..120frame均exact，自240frame跨版本RMS约.0080659，360约.372–.375，1200约.3958–.4062；原DF三重复自RMSmax .0720，候选self .1612。差异一致，不能直接归入随机噪声或宣布质量通过。
- **追加session73592 / quality-confirmation-pipeline.json**（PID需查当前文件）：等待regression-confirmation PASS后，固定D11 scenes3/56；两API再根据final-quality挑选“baseline位置/速度都完全自一致却candidate非零”，或“cross/候选self >4×baseline且绝对>1e-4”的场景。这只是调查选择，不是准入容差。6臂df/control-v0/a06/a37v2/a82/final，各8repeat×1200 capture1；分析原/无改动对照、原/final、a06/各分支，原和control全pairs自比。需据结果定位原因/移除责任优化，**不得自动接受**。
- 已重新人工读NeighborsDistanceFirst.smasm：仅交换current-distance/rest测试，r5.y保存rest条件，r9临时值不逃逸；450合成输入case已exact。但同DXBC算术指令仍不等于已经证明驱动生成的native浮点比较对任意真实边界完全一致。若ablation指向A037，宜用同一真实GPU输入比较原058/派生输出（可通过诊断FlexDemo callback/诊断build追加original-vs-derived row比较）或移除该浮点shader改动；不能靠猜测确认。该诊断**尚未实现**，先看六臂实证，别展开无用假设。
- 当前主session1352仍自动跑D11 emission/quality/6000long/CPU，随后D12全quality/emit/long/CPU，具体phase见state。三个pipeline严格依赖串行，禁止并发GPU或重复启动。所有候选状态仍provisional，final-review.json未创建。
- plot_primary.py已生成ROOT/report-figures/d11-primary.png/.svg、d12-primary.png/.svg与manifest；两图已view_image检查可读，最后将x刻度改成.05步长且API标题D3D11/12，重生成。报告make_report.py现在还强制regression-confirmation和quality-confirmation两pipeline PASS，且需显式final-review无未解决问题后才生成；加入负向独立复测表/可展开图/新增6shader映射。报告尚未生成，不能提前发布。
- 后续若证实退化/质量问题，需修源/剔除责任改动、新候选身份重建及相应整体验证，保留当前v1全部结果。勿把实验执行PASS当准入PASS。最后的中文报告、115版本391idea状态关闭、交付/归档/git commit tag push仍未完成。GO ACTIVE，不能final/complete。

## 关键新断点：2026-10-11T07:05:38+08:00，最终v2已启动

- **当前唯一GPU总队列session20494 / PID15972 / jobs/final-validation-v2-pipeline.json**，07:02:25开始。v1 final/regression/quality/affinity四pipeline都已PASS（执行完不等于v1准入）；不要再启动旧队列。v2当前final-primary-d11-v2，继续自动完成所有门。
- **A037最终撤回**：D11局部8pair与统一P核后仍有小幅退化；D12 Soft Rope原v1三次中repeat2有约.007003位置RMS尾差，8次六臂追加未重现该大尾部。多数其他质量疑点被原版/无改动控制复现，但这例原因未完全确认。保守放弃唯一修改过的浮点shader，不假称确定是A037 bug、不用数值例外。remove_neighbor_candidate.py已把正式ParticleStep恢复原058选择，registry删该入口；两个派生源移至tools/alpha_migration/retired_shaders，实验/旧DLL全保留。A037-01状态rejected-final-conservative。
- **最终v2 DLL SHA256 5ff395ca3e8b10cf2c3799000e31787c78550a572bda180274de82dd09befb7d**，Ext仍c448c3...。fresh --source current build，14继承回归、16spring/32args、162扩展radix、84原容器核验PASS；evidence/final-v2-active-shaders.json证明原84加5个纯整数辅助，0个active derived FP。没有跑450邻居作为v2门，因为该优化已撤回；原实验450记录保留。
- v2脚本run_final_validation_v2.py：两API全67三臂df/control-v0/final2×4对1200；全67 df/final2×3对1200质量；**真实增长的39/40/64/65/66**四对1800生产+三对质量；long0/3/9/25/27/47/56/65三对6000；最终CPU4八场景四对1200；final-affinity两API目标17/31、31/33/44各8对2400，只有测试子进程mask0xFFF；最后D12 Soft Rope **df12/control-v0/final2各32次1200 capture1**独立稀有尾部确认。此前数据和选择都保留。脚本PASS仍须显式审阅。
- 六臂质量追加v1结果：D11 Soft Rope原df、control、a06、a37、a82、final均出现同样9.99455e-5波动；Rigid8原df全自比maxRMS .521753、control .532293，final/self .5316，原-vs无改动cross .526836，说明旧3次低估波动。D12 MovingMesh原自比 .032112、候选.02174，cross .026149，原-vs控制 .02869，同量级；D12 SoftRope新8次original .000790、control .000915，candidate常见<.001，但旧v1唯一.007尾部尚未由原对照覆盖，所以采取回退。
- 局部性能确认v1：D11 17/31真实约-.65/-1.12%，A037带来一部分，A82没有确认退化。D12默认调度31/33约-5.1/-4.4%，44未复现回退。CPU-placement证明df大多CPU0，a06/final更常CPU14；GPU Total df/a06约.4943/.4950ms（31）、.47156/.47217（33），主要差异在CPU API提交。GetSystemCpuSetInformation（按本机SDK结构读）确认0..11 class1 P核、12..19 class0 E核；evidence/cpu-set-topology.json。统一0xFFF后v1 D12 31 ratio1.01049宽CI跨1，33=1.070864 CI[1.057932,1.083954]，44=1.127815 CI[1.055965,1.204555]；不替换原默认调度数据，不在DLL改进程亲和性。D11统一核心后17/31仍约-.84/-.82%，支持撤回A037。
- **工具修复并保留失败**：affinity的clock补测名共享suite前缀，旧统计glob多算5个replacement而assert失败。统计/quality/CPU/GPU readers及retest现在按receipt.suite精确过滤，原始controller数量仍核对。随后发现clock补测未继承原显式affinity；已保留错误5臂block及旧mapping为evidence/affinity-confirm-d11-v1-invalid-unpinned-replacements.json，重新跑affinity-clock-d11-v2并核实全部所用frame处理器mask。retest_clock_blocks现复制r.environment且验证affinity一致；输出路径里的原run替换为新run。失败日志/旧分析在evidence/tool-failures，最终affinity pipeline07:02:17 PASS。此前默认亲和性矩阵不受此遗漏影响；原67 primary没有clock flags。
- **发射标签校正**：冻结harness DEMO_EMIT实际InputKeyboardDown(space)切换g_emit，并非强制ON。Viscosity36/37/38 Initialize默认ON，原67 primary真实630→65536；额外emit36反而0→0，不能算增长。39/40为94→65536，64/65=3072→45372，66=30177→79235。characterize_emission.py按实际counts（非按性能）分类保留六场景原统计并给5增长子集：v1 D11 ratio1.008357 CI[1.003883,1.012851]，D12 1.009118 CI[.975178,1.044239]不确定。最终v2直接只跑5个真实增长场景，不改冻结harness。
- v1完整执行数据仍保留：D11 primary1.011726 CI[1.009762,1.013695]，D12primary1.047007 CI[1.043501,1.050525]；所有full/emit/long严格contracts/IDs/phases/mass和finite通过。CPU4 v1 Solve cycles speedupD11 1.52895 CI[1.42579,1.63958]、Whole1.02739；D12Solve1.22886 CI[1.19810,1.26040]、Whole1.18080。只能称仪器下线程周期，不当指令数/秒/游戏FPS，混合核心需注明。这些不是v2最终成绩。
- make_report.py已改为要求final-review.run_version=v2和final-validation-v2 PASS，使用*-v2数据；文字改为5个整数辅助、原84浮点程序未改，450为被拒候选历史。会展示final-affinity-v2补充数据、真实5场景增长；仍须实际填写final-review无未解决问题才运行。plot_primary.py默认--candidate alpha-migration-final-v2 --version v2，输出report-figures-v2，旧v1图留report-figures不覆盖。v2图尚未生成。
- 仍未做：v2全套完成与数值/公共输出/diffuse/少数回退/32rep稀有尾部显式审阅，必要修复；更新各opt最终accepted/rejected，finalize_history_decisions.py关闭115版本391ideas；详细中文报告/链接与数据核验/交付manifest/账本归档/git commit tag push。HEAD仍51cac80。GO ACTIVE，不得提前final/complete。

## v2双后端生产性能已完成：2026-10-11T07:47:09+08:00

- 当前仍只有session20494/PID15972的final-validation-v2-pipeline在运行；最新phase final-quality-d11-v2。请先看controller，不要重复启动。v2 primary每API804原进程全部PASS；D12有一个3臂clock block已按正确环境整组补测并映射，原记录保留。
- **v2 D11 df/final=1.0082300808 CI[1.0041947608,1.0122816167]**；control/final=1.0069828702 CI[1.0055629166,1.0084048289]。Holm相对df5更快/62不分离，相对control4更快/63不分离，无确认回退。df/control1.00123856，CI跨1。
- **v2 D12 df12/final=1.0448587219 CI[1.0381449976,1.0516158641]**；control/final=1.0436723249 CI[1.0342748768,1.0531551585]。Holm相对df18更快/49不分离，相对control9更快/58不分离，无确认回退。df/control1.00113675，CI跨1。不是游戏FPS，属于无窗口完整物理帧。
- 当前Git工作树16个原文件修改（CMake、恢复入口、API/Runtime/Solver）加新ledger、shaders/auxiliary（5整数）、3专项tests、tools/alpha_migration、build_aux_shaders.py；无意外文件。HEAD仍51cac80，未提交/推送。具体status已检查。正式程序不再启用A037，旧derived源在tools/alpha_migration/retired_shaders。
- diffuse_quality.py也已加receipt.suite精确过滤，避免同名前缀补测重复算。待v2所有quality/emit/long完成后，需要补跑diffuse_quality对实际有diffuse的最终面板，并检查公共输出非有限值/初始params/差异域；这是显式最终审阅的一部分，不要只读pipeline PASS。
- make_report.py已更新v2路径和5整数/无active FP说明、真实发射5场景、final-affinity-v2补充表；CMake复现命令补上必须的DISASSEMBLYFLEX_WORKSPACE和本机Ninja路径。plot_primary.py现在输出report-figures-v2，旧v1图仍保留。v2图/正式报告尚未生成。
- 下一阶段：等待v2全67质量、增长5场景、8场景6000帧、CPU4、受控P核目标复测、D12 SoftRope三臂各32重复全部完成；严格审阅异常、原始基线波动、各公共输出和最后稀有尾部；完成所有候选最终决策与115版本391条账目闭环；生成/核验中文报告和交付包，归档并commit/tag/push安全核验。不要以v1图/成绩冒充v2，GO仍ACTIVE，不能提前final/complete。
