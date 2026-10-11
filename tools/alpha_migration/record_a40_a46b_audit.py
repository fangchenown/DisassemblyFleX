from common import *
docs=read(ROOT/'history/documents-expanded.json');vs=read(LEDGER/'versions.json');rows=[]
def add(v,key,title,status,reason,file):
    e=[x['copy'] for x in docs if x['version']==v and Path(x['copy']).name==file];assert e
    rows.append(dict(id=v+'-'+key,version=v,title=title,disposition=status,reason=reason,donor_evidence=e,reviewed=now()))
add('alpha4.0','policy','每solver优化flags/reuse interval/NO_LIMIT策略','application-policy-not-port','用于隔离OF近似路径；DF保留NvFlex ABI与原每子步计算，没有这些近似开关。不能为移植配置而引入改变结果的路径。','P20_IMPLEMENTATION.md')
for key,title,reason,file in [
 ('rolling','集显rolling-quarter rows/交替grid snapshot','跨epoch数据与延迟刷新，不满足本任务输入时效；历史dGPU mean还回退19.5%。','P30_NEIGHBORS.md'),
 ('rigid','每public update仅一次full rigid fit','跳过真实shape fit，保留Jacobi apply仍不等同原DF每轮rigid；cached rotation仅1.6% pass收益也被拒。','P40_RIGIDS.md'),
 ('triangle','省首子步final response/末步discrete','OF pre/post混合碰撞流程与DF原唯一生成流程不同；不能删DF实际swept collision。','P50_TRIANGLES.md'),
 ('submission','以降频省dispatch/copy及拒绝跨模块fusion','被省的调用依赖上述近似；剩余存在真实资源依赖。本任务仅A002批量提交相同barrier、A006受控绑定，不删除同步。','P60_SUBMISSION.md')]:add('alpha4.1',key,title,'not-transplanted-semantic-or-dependency-change',reason,file)
add('alpha4.2','contacts','一次contact projection/update与packed消费','not-transplanted-semantic-change','降低接触求解频率；64邻居cap还被历史拒绝，DF不减原maxNeighbors或投影轮次。','P30_COLLIDE_PARTICLES.md')
add('alpha4.2','spring-rsqrt','dense packed CSR +单rsqrt替代sqrt/div','split-candidate-family','打包布局可单独研究，但rsqrt改变原DF浮点计算。历史16.6% spring pass收益不是>=10%完整帧收益；保留原sqrt/div。可能只将DF三条有效4byte流合并成12byte记录，并移除死流，另做严格字节验证。','P40_SOLVE_SPRINGS.md')
add('alpha4.2','triangles','一/二pass离散碰撞替代','historically-rejected-physics','高速薄网格严重tunnelling，历史恢复两次integration CCD+final discrete；DF保留自身原调度。','P50_COLLIDE_TRIANGLES.md')
add('alpha4.2','grid','packed persistent rows/cap/rest/table/cull候选','historically-rejected','没有额外CreateGrid项通过收益/风险门；不移植失败选项。','P60_CREATE_GRID.md')
add('alpha4.3','terrain','terrain remove/add改原地再生','engine-only','KG主terrain身份与拓扑命令生命周期优化，DF标准UpdateTriangleMesh已在既有mesh ID上更新，调用者不必Destroy/Create；不改变其公开显式更新语义。','P20_CAUSALITY.md')
add('alpha4.3','palette','骨骼palette容量与activation脏标记反馈环','engine-only','主要50ms周期stall由KG middleware反复误报topologyDirty引起，DF无该palette/activation系统。','P20_CAUSALITY.md')
add('alpha4.3','abi','新virtual追加到既有ABI尾部','compatibility-lesson','首方案插入ABI前缀导致slot mismatch而拒绝；本任务不改NvFlex::Context原虚表槽，新增内部方法均非virtual。','P30_FIX.md')
add('alpha4.3b','terrain-first','首次有效terrain Generate注册，其后in-place更新','engine-only','KG Scene命令策略及仅profile启用诊断，不是DF核心新数学核。','P30_FIX.md')
add('alpha4.4','transition','cloth OFF/ON生命周期及GPU transition-wait','engine-specific-correctness','修Scene graph/command ownership，避免合法异步过渡误报1210；DF不拥有游戏设置或异步对象创建队列。','P30_FIX.md')
add('alpha4.4b','capsule-lifetime','solver出现前保持capsule host topology一致','engine-specific-correctness','限于KG Scene；另一个KGCommon队列竞态未纳入当时修复。DF无此拓扑容器/队列，保持自身资源lifetime门。','00_CURRENT.md')
add('alpha4.5','dynamic-dt','clamped dynamic dt、重力/阻尼/刚度time-power归一化','not-transplanted-semantic-change','有意改变输入dt、积分、stiffness和MoveLimit/MovingFrame；本任务按同dt/substeps计算，不能用另一时间模型充当优化。','P20_DESIGN.md')
add('alpha4.5b','smoother','1200样本预分配running-mean dt','application-policy-not-port','O(1)平滑器是KG动态dt输入策略；DF内部不改变调用者传入的dt，不加入隐含平滑。','P20_IMPLEMENTATION.md')
add('alpha4.5c','cap60','60Hz solver cap + render外推','not-transplanted-semantic-change','高刷新帧跳solve/Body准备，按残余dt外推渲染；改变时间与显示合同，不满足本轮。','P20_P30_IMPLEMENTATION.md')
add('alpha4.5c','srv-bound','新增SRV后ClearBindings数组21/22修复','validation-lesson','越界由minidump定位。本任务D11 cache保留32SRV/8UAV容量，native-state validator逐派发验证实际槽位，不能照搬旧数组长度。','P20_P30_IMPLEMENTATION.md')
add('alpha4.6','neighbor-publication','spare table staged neighbor publication','not-applicable-specific-cache-fix','修OF rolling mixed-generation数据；DF每子步完整建网格/邻域，无该跨generation拼接。历史用户随后仍报告地面抖动，不能当视觉通过基线。','00_CURRENT.md')
add('alpha4.6','terrain-support','每update两次optimized final discrete support','not-transplanted-semantic-change','为OF近似调度补支撑响应；DF保留原CCD/contacts规则，不叠加补偿计算。','00_CURRENT.md')
add('alpha4.6b','restore-cadence','有triangle mesh时恢复稳定opt-out接触cadence','already-preserves-cadence','后续证据确认exact-radius temporal reuse/mixed-generation导致静止抖动。DF没有这类复用，保留原每子步输入与碰撞工作。','00_CURRENT.md')
path=LEDGER/'history_decisions.json';old=read(path);ids={r['id'] for r in rows};write(path,[r for r in old if r['id'] not in ids]+rows)
for v in vs:
    ids=[r['id'] for r in rows if r['version']==v['version']]
    if ids:v.update(status='ideas-reviewed-candidates-pending' if v['version']=='alpha4.2' else 'reviewed-no-direct-port',review_ids=ids)
write(LEDGER/'versions.json',vs);event('history-reviewed',through='alpha4.6b',ideas=len(rows));state(history_review_cursor='alpha4.6b',history_next='alpha4.6c');print('Recorded',len(rows),'ideas.')
