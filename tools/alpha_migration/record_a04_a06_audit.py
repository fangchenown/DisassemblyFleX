"""Human/model reviewed alpha0.4..0.6 decisions; prospective candidates stay open."""
from common import *
rows=[]
def group(v,donor,items):
    for key,title,status,reason,source in items:
        assert (WS/donor).exists()
        rows.append(dict(version=v,id=v+'-'+key,title=title,disposition=status,reason=reason,donor_evidence=donor,df_evidence=source,reviewed=now(),performance_claim='Historical OF figures are not DF measurements.'))
group('alpha0.4','History/OpenFleXAlpha04KG3DPerformanceLedger-2026-08-06/OpenFlexExecutionLedger/phases/P14_ALPHA04_KG3D_PERFORMANCE.md',[
 ('E01','串行替代 cooperative neighbor','historically-rejected','OF 大幅回退；DF 当前原始遍历/布局与 OF 不同，不能用 OF 开关制造 DF 优化。','shaders/recovered/058_g_Flex_CollideParticles.hlsl'),
 ('E02','空间连续 positions/phases/index payload','already-present','DF ReorderParticles 已生成 sorted positions/phases/velocities/normals 和 reverse lookup，后续邻域使用空间排序后的 payload。','src/solver/ParticleStep.cpp: ReorderParticles/CollideParticles'),
 ('E03','count-bounded rows / 延迟 sentinel','already-present-different-contract','DF 没有每次构建前 clear 整个 neighbor table 的独立调用；GetNeighbors 按原容量复制，不能引入 OF 的额外 public sentinel 约定。','src/solver/ParticleStep.cpp; src/api/ContactOutputApi.cpp'),
 ('E04','atomic-free prefix96 TGSM','historically-rejected','12 KiB TGSM 路径历史 GPU 显著回退；且会改变 DF 原始 bounded row 顺序。','shaders/recovered/058_g_Flex_CollideParticles.hlsl'),
 ('E05','spring raw sum 直接追加共享 accumulator','already-present-concept','DF SolveSprings 已写统一 mDeltas，再由后续模块与 ApplyDeltas 消费；没有 OF 原每边 float4 contribution + 第二次 merge。','src/solver/ParticleStep.cpp: SolveSprings/ApplyDeltas'),
 ('E06','packed uint16 solid neighbors','historically-rejected','OF -2.05% GPU；DF 无此压缩消费者，且容量/ID/公开行协议不同。','src/api/ContactOutputApi.cpp'),
 ('E07','scatter 额外缓存 30-bit cell code','historically-rejected','增加 payload 带宽超过省下 floor 的成本；DF hash/sorted-cell dataflow 已不同。','src/solver/ParticleStep.cpp: CalculateParticleHash/CreateGrid'),
 ('E08','phase-first candidate rejection','candidate-family','有可能无损改变拒绝前加载顺序，但必须保持 DF 每候选判定与溢出顺序及精确原指令。后续以 DF shader 热点和单步输出评估，不直接改 predicate。','shaders/recovered/058_g_Flex_CollideParticles.hlsl'),
 ('E09','symmetric unordered pair neighbor append','not-transplanted-semantic-risk','两个方向的原子 append 改变 neighbor 顺序/截断；浮点求和和 dense/sparse phase 合同不能只看集合相同。','shaders/recovered/058_g_Flex_CollideParticles.hlsl'),
 ('E10','32-thread rigid group','already-present-specialization','DF 已按平均成员数选择原 NV 32/NV/128NV kernels；OF 单一 warp32 历史回退，不替换现有分流。','src/solver/ParticleStep.cpp: rigid shader selection'),
 ('E11','unordered pair table 替代双向行','historically-deferred','需要新 pair payload、overflow 和非对称 phase 回退及 float CAS，既非直接等价也未有历史获益。','src/api/ContactOutputApi.cpp; src/solver/ParticleStep.cpp'),
 ('E12','half-rate rigid fit','not-transplanted-semantic-change','故意跳过迭代中的 rigid fit，直接改变计算图，不能作为无损优化。','src/solver/ParticleStep.cpp: iteration loop'),
 ('E13','final-only rigid fit','not-transplanted-semantic-change','删掉非最终 rigid fit，历史截图接近不等于极轻微数值差异；不满足本任务准入。','src/solver/ParticleStep.cpp'),
 ('E14','exact-cell leader 14-cell pair traversal','historically-rejected','历史 +65.5% GPU，hash alias/密集 cell cross-product 放大；不替换 DF 原定序访问。','shaders/recovered/058_g_Flex_CollideParticles.hlsl'),
 ('E15','candidate-parallel 32-lane gather','not-directly-applicable','依赖 E09 counting-grid 原子双向行，DF 原始定序截断不同；不能直接移植其速度。','shaders/recovered/058_g_Flex_CollideParticles.hlsl'),
 ('E16','sphere-cell AABB cull','candidate-family','可研究保守拒绝不可能命中的 cell，但须依据 DF 原始距离规则证明无 false negative、边界/NaN/overflow；不是沿用 OF epsilon 即可。','shaders/recovered/058_g_Flex_CollideParticles.hlsl'),
 ('E17','half-rate particle contacts','not-transplanted-semantic-change','降低 contact 生成/求解频率，改变约束工作，不满足不影响结果。','src/solver/ParticleStep.cpp'),
 ('E18','相邻 substep neighbor reuse','not-transplanted-semantic-change','跳过真实位置变化后的 broadphase refresh；有限 row 容量和移动接触不能保证不漏碰撞。','src/solver/ParticleStep.cpp'),
 ('E19','双 readback / 一帧显示延迟','outside-core-and-latency-change','KG 渲染流水优化；本任务 FlexDemo 每帧结果完成后比较，不能通过多一帧延迟当 DLL 同任务收益。','tests/demo/headless.cpp; src/api/ParticleTransferApi.cpp'),
 ('E20','每帧 latency query / 120帧校准','historically-rejected','观测开销回退；本任务生产计时与质量采集独立，不削弱原 latency API 的时效语义。','src/api/DiagnosticApi.cpp'),
 ('E21','final-only particle contacts','not-transplanted-semantic-change','省略真实约束迭代会改变结果，不凭历史可视门替代本次严格准入。','src/solver/ParticleStep.cpp'),
 ('E22','final-only shape responses','not-transplanted-semantic-change','降低形状响应频率直接改变穿透/收敛行为，不能移入结果优先底座。','src/solver/ParticleStep.cpp'),
 ('E23','position-only readback','already-present','NvFlexGetParticles 仅 ReadData positions，未请求 velocities 不会复制；DF 没有旧 OF 全状态 staging。','src/api/ParticleTransferApi.cpp'),
 ('E24','normal-only readback','already-present','NvFlexGetNormals 仅 ReadData normals，不复制其他 output；部分范围由 CopyDesc 控制。','src/api/ParticleTransferApi.cpp')])
group('alpha0.5','History/OpenFleXAlpha05EngineParityPerformanceLedger-2026-08-06/OpenFlexExecutionLedger/phases/P15_ALPHA05_ENGINE_PARITY_PERFORMANCE.md',[
 ('E01','rigid subset readback','already-present','ReadBytes 对空目标早退，各刚体域只复制调用者提供的目标，transform-only 不下载 rest。','src/api/RigidApi.cpp; src/solver/SolverStorage.cpp'),
 ('E02','velocity-only readback','already-present','NvFlexGetVelocities 只访问 mVelocities；DF 无 OF host aggregate validity 问题。','src/api/ParticleTransferApi.cpp'),
 ('E03','per-domain host ownership','historically-rejected-not-applicable','OF 没取得完整帧收益，DF host buffer 本身直接 staging，不需要 OF CPU镜像所有权层。','src/solver/SolverStorage.cpp; src/runtime/D3D11Resources.cpp'),
 ('E04','completion-query pool','historically-rejected-not-applicable','DF readback 不为每个 getter 创建 EVENT，Map 直接同步；OF 查询对象池无对应成本。','src/runtime/D3D11Resources.cpp: map/copyToHost'),
 ('E05','readback completion epoch 合并','already-avoids-cost','DF 连续 copyToHost 后阻塞 Map 即可消费，没有 OF 每域 completion 对象与重复 EVENT 标记。','src/runtime/D3D11Resources.cpp'),
 ('E06','normal CopyDesc 窄范围 staging','already-present','DF ReadData/ReadBytes 已按原 CopyDesc 字节范围复制，且不做额外 host vector 构造。不能再缩成 activeCount 破坏调用者所要容量。','src/api/ParticleTransferApi.cpp; src/solver/SolverStorage.cpp'),
 ('E08A','四个32-lane neighbor rows 每128-thread组','not-directly-applicable','改变 OF cooperative row launch；DF shader 每粒子独立访问、线程组256，不能替换除数而不改算法/资源顺序。','shaders/machine/058_g_Flex_CollideParticles.smasm'),
 ('E07-E09','temporal cache / counting grid / cell pair','historically-rejected-or-already-covered','零 skin 下跨帧缓存可漏邻居；bounded96 行会淘汰未来接触；cell pair 历史失败和 counting-grid 差异见 alpha0.4。','src/solver/ParticleStep.cpp'),
 ('E10','8-way cooperative spring accumulation','historically-rejected-already-present','OF 仅1.69% pass收益未达门；DF 原 spring 已8 lanes/particle、512线程组。不能把已有结构记为新移植。','shaders/machine/075_g_Flex_SolveSprings.smasm'),
 ('E11A','8 neighbor rows /256线程组','historically-rejected','历史 pass收益3.20%低于门，DF 亦非该行并行布局，未采用。','shaders/machine/058_g_Flex_CollideParticles.smasm'),
 ('E12','仅为请求的 rigid 域分配 host vectors','already-avoids-cost','DF getter 直接 GPU→调用者 buffer，不先构造 rest/normal/rotation/translation CPU vectors。','src/api/RigidApi.cpp')])
group('alpha0.6','Build/OpenFlexAlpha06/P18.07-candidates/P18.07A_LTCG_AND_CACHE_DECISION.md',[
 ('LTCG','Release IPO/LTCG + Gy/Gw','candidate-family','DF Release 使用 /O2，但未显式开启 IPO。可测试保持 /fp:precise 的全程序优化，必须核对导出/布局/KernelParams 和完整帧收益。','CMakeLists.txt'),
 ('PGO','profile guided optimization','historically-rejected','历史 median改善但p95回退/训练资产偏置，不直接采用这组训练profile。','CMakeLists.txt')])
group('alpha0.6','Build/OpenFlexAlpha06/P18.07-candidates/P18.07B_READBACK_SYNC_DECISION.md',[
 ('host-pool','positions/velocities/normals CPU vector pool','already-avoids-cost','DF 不在 Get/Map 每帧构造这些 CPU vectors；原生 staging 持久归属于 buffer。','src/runtime/D3D11Resources.cpp'),
 ('blocking-map','以 blocking Map 替代 query busy poll','already-present','DF ContextD3D11::map 直接 Map 并保留 DO_NOT_WAIT，getter 无前置 busy poll。显式 fenceWait 是另一公开合同，不能删除。','src/runtime/D3D11Resources.cpp; src/runtime/D3D11Context.cpp'),
 ('fluid-membership','callback-free fluid predicate 持久缓存','already-avoids-cost','DF 不每 Update 做 CPU O(N) fluid membership scan，phase 已在 GPU；不添加无用镜像。','src/api/UpdateApi.cpp; src/solver/ParticleStep.cpp'),
 ('unmapped-getter','跳过未消费 getter / staging ring','historically-deferred-semantic-risk','Get 后跨 Update 再 Map 仍应观察排队时快照，不能推迟到最新状态。DF 保留显式复制。','src/api/ParticleTransferApi.cpp; src/runtime/D3D11Resources.cpp')])
group('alpha0.6','Build/OpenFlexAlpha06/P18.07-candidates/P18.07C_STATE_BATCH_HAZARD.md',[
 ('state-batch','callback-free 整次 Update 保存恢复一次','already-avoids-cost','DF Update 不为每个 backend 操作抓取/恢复外部 CS 全状态。已有每次dispatch后 SRV/UAV unbind 保持hazard边界。','src/api/UpdateApi.cpp; src/runtime/D3D11Context.cpp'),
 ('hazard','删除重复绑定但必须保留SRV/UAV hazard 清空','candidate-family','DF 有每次 full32 SRV/8 UAV binding/clear，可研究受控域缓存。原 OF raw batching 曾导致 pinned error8.27m，任何缓存必须覆盖callback/native context、CB rename、ClearState与多solver。','src/runtime/D3D11Context.cpp'),
 ('resource-cache','减少 CPU 资源跟踪查询/重复插入','candidate-family','DF D3D12 每资源 transition 都 std::set retainedSet.insert，可研究等价无序集合或有界缓存；不得丢fence/native对象保活。','src/runtime/D3D12Resources.hpp: Context12State::keep')])
path=LEDGER/'history_decisions.json';old=read(path);ids={r['id'] for r in rows};write(path,[r for r in old if r['id'] not in ids]+rows)
vs=read(LEDGER/'versions.json')
for v in vs:
    if v['version'] in ['alpha0.4','alpha0.5','alpha0.6']:v.update(status='ideas-reviewed-candidates-pending',review_ids=[r['id'] for r in rows if r['version']==v['version']])
write(LEDGER/'versions.json',vs);event('early-history-reviewed',versions=['alpha0.4','alpha0.5','alpha0.6'],ideas=len(rows));print('Recorded',len(rows),'reviewed ideas.')
