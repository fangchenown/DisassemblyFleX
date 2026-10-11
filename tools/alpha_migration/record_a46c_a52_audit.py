from common import *
docs=read(ROOT/'history/documents-expanded.json');vs=read(LEDGER/'versions.json');rows=[]
def add(v,key,title,status,reason,selector=None):
    e=[x['copy'] for x in docs if x['version']==v and Path(x['copy']).name=='00_CURRENT.md' and (selector is None or selector in x['copy'])];assert e
    rows.append(dict(id=v+'-'+key,version=v,title=title,disposition=status,reason=reason,donor_evidence=e,source_delta=str(ROOT/'history'/v/'OpenFleX-code.patch'),reviewed=now()))
add('alpha4.6c','terrain-refresh','terrain完整邻域刷新与full-precision spring回退','already-preserves-behavior','4.6b仍抖，4.6c证明temporal rows增加contact churn；DF原每子步建邻域并保留原float spring，不引入再补偿。')
add('alpha4.6d','wide-verlet','768宽候选+1.25radius、每update过滤96物理行','not-transplanted-unproven-equivalence','源码以cache age/reuse interval判定复用，未见当前位移证书；宽skin改善已测场景，但不能保证任意新pair及时进入，也改变候选/截断状态与内存。DF保留当前输入完整重建。')
add('alpha4.7','cooperative-filter','两32-thread subgroup过滤两个候选行','different-dataflow','精确保持OF已有768候选顺序，但DF无这份跨帧候选表。不能先引入未经准入的Verlet缓存来获得该局部加速。')
add('alpha4.8','switches','七个独立item flags与NO_LIMIT优先级','application-policy-not-port','是OF近似配置治理；本轮不增加这些改变结果的API与默认路径。')
add('alpha4.8b','terrain-selective','contact age + candidate one-ring选择刷新','not-transplanted-stale-data','近terrain新行、远处复用，仍涉及陈旧候选/新接触时效；两pass mask还被拒。DF没有此近似基础，不移入。')
add('alpha4.9','normal-stabilizer','持续交替小法向扰动检测与修正','not-transplanted-new-physics','修改contact-normal位置/速度以补偿OF抖动，是新物理响应/历史状态，不是DF等结果提速。')
add('alpha4.9b','rest-lock','三帧获取、同帧释放的表面相对静止锁','not-transplanted-new-physics','虽然融合在原dispatch内，但改变锁定与速度/位置规则，并增加约0.02ms/solver；用户后续仍报告抖动，不移植。')
add('alpha4.9c','hard-lock','hard rest lock及强制精确邻域','not-transplanted-new-physics','修前版失败并增加约0.449ms成本；DF既无这些rest锁方程，也未引入temporal rows抖动源。')
add('alpha5.0','importance','particle importance分级与滞回','historically-disabled-and-semantic-risk','实际KG中位耗时回退2%-4%，单项默认0；按重要性改变部分工作还需行为证明，本轮不引入。')
add('alpha5.1','exact-grid','mixed-phase exact-cell counting grid、2x table/完整probe/sentinel','different-grid-and-order-contract','消除OF较小hash表的alias成本；DF原radix/21bit bucket/sorted mapping不同，直接替换会改变内部排列/行顺序。保留DF原数据契约，仅研究不改顺序的局部遍历。','LosslessPerformance')
add('alpha5.1','source-rest','source rest行复用','already-present','DF058在每源粒子开始仅一次载入source rest到r4，内层候选不会反复加载它。','LosslessPerformance')
add('alpha5.1','triangle-inplace','dense/static triangle in-place response','already-avoids-donor-cost','OF要复制resolved positions/velocities副本；DF CollideTriangles只生成counts/planes/contact velocities，由后续原约束消费，没有这些全容量副本。直接提前改位置会改变解算顺序。','LosslessPerformance')
add('alpha5.1','reference-fps','可配置dynamic reference FPS15-240','application-policy-not-port','同名alpha5.1的第二任务调整KG动态dt/capped tick与渲染外推基准，必须单独记录；DF原API由调用者传dt，无此策略。','DynamicReferenceFPS')
add('alpha5.1b','offline-fifth-shader','补预编译StaticPoseInPlace以消除15秒FXC','already-present','DF所有原84及新增aux均构建期生成/嵌入，运行时没有D3DCompile；保持这一原则，不能漏掉新增helper。')
add('alpha5.2','moving-frame-cadence','capped solver与高刷新MovingFrame/render修复','engine-specific-correctness','属于KG固定/动态tick和动画渲染协调，不增加solver次数；DF未引入capped/extrapolated调度，无对应改动。')
path=LEDGER/'history_decisions.json';old=read(path);ids={r['id'] for r in rows};write(path,[r for r in old if r['id'] not in ids]+rows)
for v in vs:
    ids=[r['id'] for r in rows if r['version']==v['version']]
    if ids:v.update(status='reviewed-no-direct-port',review_ids=ids)
write(LEDGER/'versions.json',vs);event('history-reviewed',through='alpha5.2',ideas=len(rows));state(history_review_cursor='alpha5.2',history_next='alpha5.3');print('Recorded',len(rows),'ideas.')
