from common import *
docs=read(ROOT/'history/documents-expanded.json');vs=read(LEDGER/'versions.json');rows=[]
def add(v,key,title,status,reason,file):
    evidence=[x['copy'] for x in docs if x['version']==v and Path(x['copy']).name==file];assert evidence
    rows.append(dict(id=v+'-'+key,version=v,title=title,disposition=status,reason=reason,donor_evidence=evidence,source_delta=str(ROOT/'history'/v/'OpenFleX-code.patch'),reviewed=now()))
for key,title,reason in [
 ('owner','单调遍历代替quadratic rigid owner lookup','KG authored vertex到rigid owner的构造成本；DF NvFlexSetRigids直接接收offsets/indices，没有该嵌套查询。'),
 ('capacity','保留per-particle membership小vector容量','DF刚体拓扑直接GPU buffer并已按容量ReserveBuffer；没有OF每次assign(capacity,{})销毁嵌套CPU vectors。'),
 ('prefix-csr','count/prefix/fill构造sparse rigid CSR','用于OF额外sparse cadence/continuity路径；DF原rigid kernel直接读传入offsets/indices，不构造这个中间CPU CSR。')]:add('alpha3.1',key,title,'already-avoids-donor-cost',reason,'40_conservative_optimization_a.md')
add('alpha3.1','rejected','状态消除/永久shader对象cache/组大小试验','historically-rejected','源码差异确认CB unbind行只是格式噪声，保留实现只有拓扑构造优化；本任务A006另按DF自身成本验证绑定/分配，不继承历史失败项。','50_conservative_optimization_b.md')
add('alpha3.2','verlet','精确相对位移AABB Verlet证书','historically-not-effective','设计取消公共平移并使用256/512候选容量，但真实布料几乎每帧耗尽证书；额外判定/存储不能摊薄。本轮DF不添加没有已证明收益的跨帧状态机。','30_verlet_design.md')
add('alpha3.2','cell-pair','compact occupied-cell + deterministic Count/Prefix/Scatter','historically-rejected','45,194粒子重建约0.55ms，旧packed Counting Grid约0.354ms，生产开关OFF；DF radix grid/有序bounded邻居行又不同，不移植。','60_compact_cell_pair_implementation.md')
for key,title,status,reason in [
 ('o3-spring-contact','Intel集显spring/contact O3','different-compiled-program-contract','OF在Intel集显26.56→26.28ms；DF保留原DXBC数学/调度，已经离线编译，不把其他架构/不同算法FXC O3数字外推到RTX5080。'),
 ('o3-remaining','其余runtime shader O3','different-compiled-program-contract','OF集显小幅收益，不构成DF原指令重新优化后的逐结果一致证明。'),
 ('skin64','Body SkinTargets128→64','engine-only','KG蒙皮kernel不属于DF；其Intel占用率收益不能移给原NV solver线程组。'),
 ('bucket8','bucket规模4→8','historically-rejected','CreateGrid13.82→13.98ms回退；DF使用radix网格。'),
 ('cell-code','packed cell codes','historically-rejected','13.82→13.84ms，无收益且额外内存流。'),
 ('rows2','两packed rows合一64-thread group','historically-rejected-correctness','cross-row barrier不平衡导致超过2分钟无法完成warmup；DF任何组变更必须先证明同步范围，不能照搬。'),
 ('parallel','packed candidate-parallel traversal','historically-rejected','13.822→13.815ms在噪声内，尚有顺序风险。'),
 ('hash-filter','sorted full-hash prefilter','historically-rejected','13.822→13.816ms在噪声内且新增load/branch。'),
 ('spring64','fused spring128→64','historically-rejected','3.524→3.518ms在噪声内；DF8lane spring另按原指令评估。')]:add('alpha3.3',key,title,status,reason,'30_candidate_design.md')
for key,title,status,reason in [
 ('serial64','exact64-thread serial neighbors','historically-rejected','CreateGrid13.79→20.75ms，精确也不代表更快。'),
 ('cadence2','cadence2 neighbor reuse','not-transplanted-semantic-change','允许新pair延迟一帧；本任务不降低碰撞发现频率。'),
 ('cadence4','cadence4 neighbor reuse','not-transplanted-semantic-change','最多三帧新pair延迟，即使集显收益大也无通用极轻微影响上界，不能启用例外。'),
 ('skin25','25% Verlet skin','historically-rejected','solver mean16.24→20.59ms，较安全候选反而更慢。'),
 ('aero','改为per-frame normals/aero','historically-rejected-semantic-change','16.24→16.17ms噪声级且改变气动力积分时刻。'),
 ('quarter','交错quarter-row刷新','historically-rejected-semantic-change','破坏高效symmetric pair ownership，solver约22.99ms；DF也不接受陈旧行。')]:add('alpha3.4',key,title,status,reason,'40_implementation_and_ab.md')
path=LEDGER/'history_decisions.json';old=read(path);ids={r['id'] for r in rows};write(path,[r for r in old if r['id'] not in ids]+rows)
for v in vs:
    ids=[r['id'] for r in rows if r['version']==v['version']]
    if ids:v.update(status='reviewed-no-direct-port',review_ids=ids)
write(LEDGER/'versions.json',vs);event('history-reviewed',through='alpha3.4',ideas=len(rows));state(history_review_cursor='alpha3.4',history_next='alpha3.5');print('Recorded',len(rows),'ideas.')
