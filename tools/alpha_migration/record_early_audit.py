"""Reviewed historical ideas and DF-specific eligibility, distinct from measured acceptance."""
from common import *
rows=[]
def add(v,key,title,status,reason,df,donor):
    rows.append(dict(version=v,id=v+'-'+key,title=title,disposition=status,reason=reason,df_evidence=df,donor_evidence=donor,reviewed=now(),performance_claim='No DF speedup claimed without a separate candidate receipt.'))
v='alpha0.2';d='History/OpenFleXAlpha02PerformanceReleaseLedger-2026-08-04/OpenFlexExecutionLedger/phases/P11_D3D11_PERFORMANCE.md'
for key,title,status,reason,df in [
 ('grid','counting-grid 替换 radix grid','not-transplanted-semantic-risk','OF 原子 scatter 改变 bucket 内顺序；DF 的 24-bit radix 排序、有限邻居截断和浮点累计依赖原序。不能用同一邻居集合代替同一计算结果。','src/solver/ParticleStep.cpp: UpdateParticleSubstep; src/solver/RadixSort.cpp'),
 ('cooperative','32-lane cooperative neighbor gather','not-directly-applicable','OF counting-grid buckets 与 DF 有序网格不同。协作 append 将改变截断顺序；需独立保持顺序算法，不能直接替换 NV 内核。','shaders/recovered/*g_Flex_CollideParticles.hlsl'),
 ('uniform-fluid','uniform-fluid/zero-optional shader 特化','candidate-family','仅在完整参数/phase 证明下删恒假分支才可能等价；DF 原始内核的 phase 混合、optional feature 与 vendor intrinsic 必须逐指令保持，后续按实测热点评估。','src/solver/ParticleStep.cpp; shaders/recovered'),
 ('packed-fluid','16-bit packed-fluid neighbor rows','not-transplanted-layout-contract','DF neighbor row 的 stride、容量、public GetNeighbors 与 shader 索引格式已有固定布局；替换需全消费者同时改变并处理 >65535 与 sparse ID，收益不能外推。','src/api/ParticleTransferApi.cpp; shaders/recovered'),
 ('velocity-neighbor-reuse','fluid velocity 复用邻域','already-present','DF 每子步仅一次 CollideParticles 建邻域，SolveVelocities 已复用 mParticleNeighbors/mParticleNeighborCounts；没有 OF 旧版第二次 build 可删除。','src/solver/ParticleStep.cpp: UpdateParticleSubstep'),
 ('fluid-clear','PBF substep-only clear','different-architecture','OF Jacobi/force clear 流与 DF 不同；DF SolveDensities 每轮生成后续 spring/rigid 共用 deltas，没有可直接删除的 OF 两次独立 clear。','src/solver/ParticleStep.cpp: SolveDensities/ApplyDeltas'),
 ('static-ccd','analytic static triangle CCD','not-transplanted-semantic-risk','替代 OF 的采样/根搜索可改善 OF，但 DF 已使用原始 NV CCD kernel；其接触选择/TOI/边面顺序不同，不能保证同结果。','shaders/recovered/*CollideTriangles*; src/geometry'),
 ('shape-buffer','persistent shape buffers','already-present','DF Shapes/Geometry 具有容量与 ReserveBuffer/Storage 复用，SetShapes 不按 OF 旧方式每帧重新 Create 所有 structured buffers。仍可针对真实重复上传另做证明。','src/api/ShapeApi.cpp; src/geometry/GeometryStorage.cpp'),
 ('coplanar','coplanar triangle metadata / traversal shortcut','not-transplanted-semantic-risk','OF 自有 BVH/CCD 的平面 shortcut 不能替换 DF 节点编码与接触入选顺序。近共面/边界/移动网格还需回退，未达到例外准入。','src/geometry; shaders/recovered/*CollideTriangles*'),
 ('native-triangle-init','native GPU triangle init','historically-rejected','历史仅将 query wait 转移到另一个标签，完整帧没有获益；DF 不添加这一已知仅转移成本路径。','src/geometry'),
 ('contact-cache','跨帧/末轮 collision reuse','historically-rejected','历史曾出现 minY=-410.645；缩到无接触路径又慢 3.7%。失效条件不能仅用位置/phase 缓存判断。','src/solver/ParticleStep.cpp'),
 ('spring-fuse','spring CSR gather + apply fusion','different-architecture','DF 已单次 half-spring gather 累积到共享 deltas，后续还会有 inflatable/rigid 写入再统一 ApplyDeltas。直接改 in-place 会变 Jacobi 读快照和约束组合。','src/api/SpringApi.cpp; src/solver/ParticleStep.cpp'),
 ('iteration-snapshot','iteration snapshot + clear fusion','not-applicable','DF 无 OF 每轮独立 position snapshot + 两次 Jacobi clear 序列，不能移植一个不存在的开销消除。','src/solver/ParticleStep.cpp'),
 ('unique-rigid','unique rigid direct apply','different-architecture','DF 原始 rigid 内核已按 vendor/平均粒子数选择多种 shape-fit kernel 并写共享位置/deltas；OF 新 direct path 不是 DF 同构替代。','src/solver/ParticleStep.cpp: SolveShapes*'),
 ('fluid-fusion','fused viscosity / online fluid statistics / density snapshot / poly6','not-transplanted-semantic-risk','这些优化依赖 OF 不同的 fluid passes 和浮点求值顺序。DF SolveVelocities 已包含多项功能，重用 OF Poly6 或在线统计会改变舍入/归约/潜能；未有满足极微误差例外的证据。','shaders/recovered/*SolveVelocities*; shaders/recovered/*CalculateDensity*'),
 ('submission','减少 CPU 资源操作与提交次数','candidate-A002-01','保留 DF 原始 40 描述符内容、顺序、barrier 与生命周期，将 D3D12 的 40 次单描述符复制改为一次 ranged copy；这是 OF 思路适配，须独立实测。','src/runtime/D3D12Context.cpp: Context12State::bind'),
 ('profiler','异步 profiling 与分离观测开销','measurement-adopted','本任务 profile=0/capture=0 测完整帧，质量单独 capture。计时器 API 名称/语义仍保留，不把观测模式优化当生产收益。','tools/alpha_migration/run_matrix.py')]:add(v,key,title,status,reason,df,d)
v='alpha0.3';d='History/OpenFleXAlpha03ClothPerformanceReleaseLedger-2026-08-05/OpenFlexExecutionLedger/phases/P12_D3D11_CLOTH_ALPHA03.md'
for key,title,status,reason,df in [
 ('C01','空功能不发 detailed timestamp','not-adopted-api-contract','DF 已有计时诊断兼容门；本任务生产 profile=0。只为计时开销删除原始名称会改变接口，A001 已发现并修复这一差异。','src/api/DiagnosticApi.cpp; tests/diagnostic_oracle.py'),
 ('C02','contact-owned snapshot + direct spring merge','different-architecture','DF 没有 OF 每轮 copy snapshot；spring 与 density/rigid 共享 delta 已存在，不能再删两次不存在的派发。','src/solver/ParticleStep.cpp'),
 ('C03','indirect dispatch 缩短空尾部','candidate-family','OF 正式 cloth 全活跃故无收益，但 DF spring launch 按 maxParticles，可评估按最大 spring 端点缩短空尾；绝不能按 activeCount 裁剪 sparse 高 ID。需保留原内核并验证新增 args 成本。','src/api/SpringApi.cpp; src/solver/ParticleStep.cpp: mMaxParticles*8'),
 ('C04','packed authored-order adjacency','different-architecture','DF 已 sorted half-spring CSR，与 OF authored adjacency 顺序不同。合并读取流可能独立研究，但直接替换会改变累加次序。','src/api/SpringApi.cpp; shaders/machine/075_g_Flex_SolveSprings.smasm'),
 ('C05b','two-projection groupshared spring batch','not-transplanted-semantic-risk','跨两投影合批依赖 OF 局部图证明。DF 每轮有 density、spring、inflatable、rigid、contacts 和 callbacks；不能跳过这些全局交错边界。','src/solver/ParticleStep.cpp: iteration loop'),
 ('C06','colored GS / XPBD / Small Steps','historically-rejected-or-quality-only','会改变公开 iterations/substeps 与乘子/更新顺序，不满足本任务结果优先约束。','src/solver/ParticleStep.cpp'),
 ('C07','按需 public neighbor snapshot','already-present-equivalent','DF 的 GetNeighbors 路径在调用时执行复制，没有 OF 每子步无条件复制一份 host-visible public snapshot。','src/api/ContactOutputApi.cpp'),
 ('C08a','counting-grid reserve 4N→2N','historically-rejected','原 OF 三个 cloth screen 均回退，且 DF 使用 radix grid，不存在该 4N counting bucket reserve。','src/solver/RadixSort.cpp'),
 ('C08bc','prefix-delimited counting grid / host cell-count constant','not-applicable','针对 OF counting-grid 元数据与 scatter 尾部；DF 原 NV 起止 bucket/哈希布局不同，不能直接删 ends 或更换计数契约。','src/solver/ParticleStep.cpp: CreateGrid/ClearCellBuckets'),
 ('C09','plane-only shape shader','candidate-family','DF 仍保留 CollideShapes 的解析平面工作；只能在 shape.count==0 精确特化并保留浮点顺序，不能整体跳过。后续热点评估。','src/solver/ParticleStep.cpp: CollideShapes'),
 ('C10','static coplanar face CCD shortcut','not-transplanted-semantic-risk','同 alpha0.2 coplanar：OF 自有算法与 DF 原 NV CCD 不同；accepted OF pass speedup 不能证明 DF 同结果。','shaders/recovered/*CollideTriangles*'),
 ('C11','stateless contact specialization','historically-rejected','独立接口需要立即清零 persistent-force 行，生产门修复后仍多个 workload 回退，不能盲移植。','shaders/recovered/*SolveDensities*'),
 ('C12','dense uniform solid specialization','historically-rejected','历史 GPU +0.8% 而完整 wall 约 -3%，本任务同样以完整帧判断，不采纳该历史失败实现。','src/solver/ParticleStep.cpp'),
 ('C13a','zero dissipation velocity finalize fusion','different-architecture','OF 两次 velocity entry 可去除，但 DF UpdateVelocities 与 SolveVelocities 中间有 SubstepEnd/UpdateEnd callbacks 且前后状态语义不同；不能越过回调合并。','src/solver/ParticleStep.cpp: UpdateVelocities/ExecuteCallback/SolveVelocities'),
 ('C13b','dense plane report clear+generation fusion','different-architecture','OF 最终 report 是单独 pass；DF static-contact counts clear 在碰撞前且同数据由 triangle/shape 共同累积，无法直接使用 OF 稠密最终报告融合。','src/solver/ParticleStep.cpp'),
 ('C14a','ShapeResponse 64→128 threads','historically-rejected','历史六组全部回退；DF 原始 shader thread groups 与算法已不同，线程数修改不是可外推收益。','shaders/machine/*CollideShapes*'),
 ('C14b','groupshared normal atomic reduction','historically-rejected-and-order-risk','OF pass 快 13% 但 wall 慢 2.75%，且重新归约会改变浮点原子相加顺序。','shaders/recovered/*UpdateVertexNormals*'),
 ('C15a','packed-word neighbor decode','not-applicable','OF packed neighbor 路径的两个 uint16 解码；DF 当前 32-bit rows 没有此解码成本。','shaders/recovered/*CollideParticles*'),
 ('C17a','rigid fused in-place reduction tree','different-architecture','DF 原 NV rigid kernels 已单派发含归约并按 32/NV/128NV 分流，没有 OF 多个 reduction dispatch 可直接合并；改树会改变数值。','src/solver/ParticleStep.cpp: rigid block'),
 ('C18a','32-byte packed BVH node','different-layout-contract','DF 的原始三角 BVH 节点由 recovered shader/geometry 约定，不是 OF 原 unpacked node 布局。需全链重写才可评估，不能作为无损直接移植。','src/geometry; shaders/recovered/*CollideTriangles*'),
 ('C16','SM6 wave/async','unsupported-backend-contract','DF 目标是原 SM5 DXBC + NV/AMD 扩展；直接采用 SM6 需要新运行时/最低设备契约，不能替换保持兼容的公共路径。','CMakeLists.txt; src/runtime/ShaderLibrary.cpp')]:add(v,key,title,status,reason,df,d)
path=LEDGER/'history_decisions.json';previous=read(path) if path.exists() else []
ids={x['id'] for x in rows};write(path,[x for x in previous if x['id'] not in ids]+rows)
for r in rows:
    # Evidence path patterns identify source families, never fabricated lines.
    assert (WS/r['donor_evidence']).exists()
vs=read(LEDGER/'versions.json')
for v in vs:
    if v['version'] in ['alpha0.2','alpha0.3']:
        v.update(status='ideas-reviewed-candidates-pending',review_ids=[x['id'] for x in rows if x['version']==v['version']])
write(LEDGER/'versions.json',vs);event('early-history-reviewed',versions=['alpha0.2','alpha0.3'],ideas=len(rows))
print('Recorded',len(rows),'reviewed ideas; candidate families remain pending.')
