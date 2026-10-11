from common import *
rows=[]
def add(v,key,title,status,reason,donor,df):
    assert (WS/donor).exists()
    rows.append(dict(id=v+'-'+key,version=v,title=title,disposition=status,reason=reason,donor_evidence=donor,df_evidence=df,reviewed=now()))
d='History/OpenFlexAlpha22GpuStabilityLedger-2026-08-14/OpenFlexExecutionLedger/phases/P02_RECOVERY_AND_INPUT_HARDENING.md'
for key,title,reason in [
 ('capsule','capsule generation事务发布/mutex/range rollback','KG Scene原三次raw-pointer读的竞态修复；DF没有该发布接口或异步通知队列，不增加每帧锁。'),
 ('lifetime','异步Scene保活与强GPU-state所有权','KG Scene/Body对象生命周期，不是DF buffers/contexts。DF资源保活用现有D3D12 fence/multi-context oracle验收。'),
 ('gpu-latch','GPUrequested latch与可恢复错误fail-closed','KG Commit/Framemove/Fetch/Render路由修复，禁止回落CPU；DF本来是D3D求解器，无对应CPU fallback分支。'),
 ('registration','六个shape arrays验证及stale registration修复','针对OF interop v2注册图，与DF标准NvFlexSetShapes直接buffer复制不同。')]:add('alpha2.2',key,title,'engine-specific-correctness',reason,d,'src/api/ShapeApi.cpp; src/runtime/D3D12Resources.hpp')
d='History/OpenFlexAlpha23BehaviorExactPerformanceLedger-2026-08-15/OpenFlexExecutionLedger/phases/P02_CPU_D3D11_EXACT_OPTIMIZATION.md'
for key,title,status,reason in [
 ('W20','persistent timestamp query objects','already-present','DF QueryTimers已有高水位reserve和clear只重置计数，D3D12亦复用query heap。'),
 ('W21','spring48-byte精确内容CB缓存','already-avoids-most-cost','DF弹簧每轮共用KernelParams，不每pass构造上传48-byte独立CB。根CB每Update只上传一次；重复substep CB另列可实验家族。'),
 ('W22','rigid/shape/finalize/contact CB缓存','historically-rejected','增加28个常驻CB而总scope慢0.4%；不把所有参数缓存当普适收益。'),
 ('W23a','solver-state192-byte CB缓存','historically-rejected','OF总scope慢4.1%，lookup/buffer切换超过省上传。DF现有一次根CB共享更少开销。'),
 ('W23b','contact-merge16-byte CB缓存','historically-rejected','OF总scope慢4.9%；DF无独立contact-merge CB。'),
 ('W6','证明dense active prefix后缩短structural extent','candidate-A003-01','DF多数pass已按active数量；spring余量由A003用真正max referenced ID裁剪，保留sparse高ID。不会把public Get默认容量改小。'),
 ('W19','logical epoch消费','historically-rejected-static','有效配置依赖降频/多轮合批，安全配置恒返回1，不可能省真实DF工作。')]:add('alpha2.3',key,title,status,reason,d,'src/solver/ParticleStep.cpp; src/runtime/D3D11Context.cpp; src/api/UpdateApi.cpp')
d='History/OpenFlexAlpha23BehaviorExactPerformanceLedger-2026-08-15/OpenFlexExecutionLedger/phases/P03_GPU_EXACT_OPTIMIZATION.md'
add('alpha2.3','W24','dense transient Float4 prefix copies','already-avoids-cost','DF Predict直接写NewPositions，Reorder直接生成Sorted*；没有OF post-Integrate velocity/pre-CCD/collision-result完整快照copy三条流。原公开transfer保持容量合同。',d,'src/solver/ParticleStep.cpp; src/api/ParticleTransferApi.cpp')
add('alpha2.3','W25','neighbor64-byte精确CB缓存','already-avoids-most-cost','DF邻域pass共用原根CB，不每subpass重复同一OF64-byte payload。radix小CB每轮pass字段变化，不能直接跳过上传。',d,'src/solver/ParticleStep.cpp; src/solver/RadixSort.cpp')
d='History/OpenFlexAlpha24LightApproxPerformanceLedger-2026-08-15/OpenFlexExecutionLedger/phases/P02_EXACT_OPTIMIZATION.md'
for key,title,status,reason in [
 ('W30','8 packed-solid rows/256threads','historically-rejected','无CreateGrid/完整收益，撤回调度差异；DF非OF packed cooperative布局。'),
 ('W32','native contact-init ClearUAV+Copy','historically-rejected','OF triangle0.157→0.198ms；且public全域resolved buffers不能按active偷缩。DF无OF该结果初始化副本。'),
 ('W33','spring独立输出64→128threads','candidate-family','DF是每粒子8lane、512thread groups，共享区仅8lane块内。可针对256thread派生辅助kernel实测，但需同步host/indirect组大小且原live数学指令不变；不能直接套OF128除数。'),
 ('W34','capture+clear64→128threads','not-applicable-historical-reject','OF ClearDeltas回退1.23%；DF无该snapshot+clear融合kernel。'),
 ('W35','Integrate64→128threads','historically-rejected','OF无收益；DF Predict已有256threads，不能将OF尺寸当最佳值。'),
 ('W36','analytic shape64→128threads','already-sized-historical-reject','OF微退，DF原CollideShapes本来128threads；A003 plane specialization保持该尺寸。'),
 ('W37','rigid apply64→128threads','different-architecture','DF原rigid fit/apply/accumulation在单个原NV kernel内，无OF独立ApplyRigidShapeMatching pass。'),
 ('W38','CSR normals64→128threads','different-architecture','DF采用原face+atomic vertex normals，非OF CSR gather；改归约会影响顺序，不能当线程参数直接迁移。'),
 ('W39','Body Deform256threads','historically-rejected-engine-only','高寄存器路径慢1.2~1.8%，不在DF。'),
 ('W40','packed candidate-parallel neighbors','historically-rejected','OF没有重复可测收益且存在调度差异，未采用。'),
 ('W41','packed cell code cache','historically-rejected','增加code生成/带宽且neighbor/grid更慢；DF原hash数据布局不同。'),
 ('W42','Body MoveLimit64threads','engine-only','KG Body专用输出kernel，冻结FlexDemo/DF没有MoveLimit pass。'),
 ('W43','Body Deform64threads','engine-only','KG renderer变形kernel，不能把引擎渲染收益归于DF DLL。'),
 ('W44','SkinTargets64threads','historically-rejected-engine-only','重复测量无收益，已恢复128；DF无此蒙皮生产者。')]:add('alpha2.4',key,title,status,reason,d,'src/solver/ParticleStep.cpp; shaders/machine/032_g_Flex_SolveSpringsNV.smasm; shaders/machine/075_g_Flex_SolveSprings.smasm')
d='History/OpenFlexAlpha24LightApproxPerformanceLedger-2026-08-15/OpenFlexExecutionLedger/phases/P03_LIGHT_APPROX_OPTIMIZATION.md'
add('alpha2.4','approx','轻微近似静态审计','historically-no-admissible-approximation','此版本最终未保留任何近似；既有跨帧缓存/减迭代/减碰撞可能导致旧数据穿透或抖动。本轮同样不复活。',d,'src/solver/ParticleStep.cpp')
for v,title,reason,donor in [
 ('alpha2.5','重叠rigid恢复完整cadence','修OF final-only rigid/contact造成软顶点抖动；DF本来每轮求解全部rigid/contact，不存在这项降频缺陷。','History/OpenFlexAlpha25SoftVertexStabilityLedger-2026-08-15/OpenFlexExecutionLedger/phases/P02_ROOT_CAUSE_AND_FIX.md'),
 ('alpha2.5b','overlap quaternion/COM continuity permutation','R03额外overlap派发因性能失败；R09改模糊fit的极分解细化/旋转跳变/COM限幅，R10压缩元数据因崩溃撤回。DF原shape-matching数学不同，移植限幅会改变NV结果且无额外性能收益。','History/OpenFlexAlpha25bSoftVertexStableFastLedger-2026-08-15/OpenFlexExecutionLedger/phases/P03_IMPLEMENTATION.md'),
 ('alpha2.5c','line-like component covariance classifier + CSR修正','upload阶段分类40/1042 clusters，并在spring shader追加保持前旋转的平移修正。为OF的特定软链稳定性添加新方程，不是DF等结果性能优化。','History/OpenFlexAlpha25cRearChainRepairLedger-2026-08-15/OpenFlexExecutionLedger/phases/P03_IMPLEMENTATION.md'),
 ('alpha2.5d','主轴transport保持twist连续性','新增rest-axis SRV并以shortest swing运输上一旋转；有意改变目标链旋转解，性能只在噪声内。DF保留原NV刚体解。','History/OpenFlexAlpha25dRearChainCompletionLedger-2026-08-15/OpenFlexExecutionLedger/phases/P03_CANDIDATES.md')]:add(v,'correction',title,'not-transplanted-different-physics',reason,donor,'src/solver/ParticleStep.cpp: original SolveShapes* kernels')
path=LEDGER/'history_decisions.json';old=read(path);ids={r['id'] for r in rows};write(path,[r for r in old if r['id'] not in ids]+rows)
vs=read(LEDGER/'versions.json')
for v in vs:
    ids=[r['id'] for r in rows if r['version']==v['version']]
    if ids:v.update(status='ideas-reviewed-candidates-pending' if v['version'] in ['alpha2.3','alpha2.4'] else 'reviewed-no-direct-port',review_ids=ids)
write(LEDGER/'versions.json',vs);event('history-reviewed',through='alpha2.5d',ideas=len(rows));state(history_review_cursor='alpha2.5d',history_next='alpha2.6');print('Recorded',len(rows),'ideas.')
