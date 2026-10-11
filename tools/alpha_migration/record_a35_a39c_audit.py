from common import *
docs=read(ROOT/'history/documents-expanded.json');vs=read(LEDGER/'versions.json');rows=[]
def add(v,key,title,status,reason,file):
    evidence=[x['copy'] for x in docs if x['version']==v and Path(x['copy']).name==file];assert evidence
    rows.append(dict(id=v+'-'+key,version=v,title=title,disposition=status,reason=reason,donor_evidence=evidence,source_delta=str(ROOT/'history'/v/'OpenFleX-code.patch'),reviewed=now()))
add('alpha3.5','frame-coalescing','MovingFrame消费时合成与pre-render提交顺序','engine-specific-correctness','修KG一帧显示滞后与多次动画更新覆盖delta。DF按每次公开Update调用工作，不拥有游戏动画/render调度。','00_CURRENT.md')
add('alpha3.6','lazy-contacts','按GetContacts需求生成derived report','already-avoids-donor-cost','OF final DispatchContacts仅生成公开派生表；DF static contact counts/planes/velocities是实际SolveContactsSequential和SolveVelocities输入，不是可丢的报告副本。DF GetContacts已直接复制现存buffer。','30_optimization.md')
add('alpha3.6','rejected','packed dense prefix / scale8 buckets','historically-rejected','历史明确回退；DF仍是原radix grid，不按OF选项替换。','20_profile_root_cause.md')
for key,title,status,reason in [
 ('private-rows','sorted64-thread private rows','already-present-concept','DF已有空间排序后的positions/phases，单线程拥有邻居行并按原遍历序写出；具体group256不可按OF64尺寸直接改。'),
 ('distance-first','当前距离先于rest predicate','candidate-family','原DF058先phase→rest-space→current-distance。对被当前距离拒绝的pair可能省rest随机读，布尔判定可在不改行序/截断的前提下换序；必须保留各距离运算、直接邻居输出与全仿真验证。'),
 ('uniform-phase','uniform filtered phase特化','not-directly-applicable','需要精确host/GPU来源与callback失效证明；DF GPU phase可经device/native source输入，不接受仅凭旧CPU镜像的uniform假设。'),
 ('exact-cell','10-bit exact-cell open-address table','different-layout-and-order-contract','OF从自己的Counting Grid迁移；DF原21bit bucket/radix决定sorted maps及bounded行顺序。重新排序会影响callback映射/累加，保留原顺序的额外索引构造尚无收益证据，不直接替换。'),
 ('cadence','与旧cadence4组合的11.6x摊销数字','not-transplanted-semantic-change','其中收益来自少重建三帧，不能当等工作DF收益。'),
 ('rest-float4','完整sorted rest payload','historically-rejected','8.10→8.92ms；额外流量不合算。'),
 ('quant-rest','quantized rest code','historically-rejected','约9.58ms且量化改变边界，不采用。'),
 ('rest-hashes','128slot/4slot rest buckets','historically-rejected','40.73/16.99ms，均大回退。'),
 ('unroll','hard-unroll27cells / remove sphere cull','historically-rejected','4.49→4.59或4.52ms；DF已有直接27cell程序，不盲展开。'),
 ('bounded-tail','满邻居行之后不再做无用候选读取','candidate-family','DF058已有count<capacity条件但满行仍扫描其余候选。可在这个现有if的else写出最终count并return，不增非饱和路径判定、不改已存行顺序；这是DF有证据的适配机会，尚未实现。')]:add('alpha3.7',key,title,status,reason,'50_optimization.md')
add('alpha3.7b','toolchain','按VS/toolset隔离obj中间目录','build-correctness-only','防不同编译器共享旧PCH/obj导致C2011；本任务每候选独立Build并固定toolchain，已满足隔离原则。','20_FIX.md')
add('alpha3.8','standalone','Core/Ext独立CMake DLL、KG改import','already-present-organization','DF本来独立CMake DLL与原NvFlex ABI；此版本拆仓/SDK兼容子树不提供新的求解器算法。','00_CURRENT.md')
for key,title,status,reason in [
 ('dual-adjacency','full/half spring adjacency','not-transplanted-reduction-change','half只在显式优化模式使用，改变双向累计与顺序；DF每粒子8lane半弹簧归约已固定，不直接用另一种归约替代。'),
 ('normal-aero','同子步normal/aero融合，finalize应用','already-combined-concept','DF UpdateTriangles同时生成face normals/aero delta，Finalize消费；没有OF独立aero apply可省。'),
 ('final-aero','仅final-public-substep normal/aero','not-transplanted-semantic-change','改变采样与积分时间，不满足本轮约束。'),
 ('filtered-contact','精确filtered-contact快速消费','different-dataflow','OF packed/phase专用接触消费者和DF原SolveDensities数据流不同；只能从DF原判定做逐指令等价变换，不换其方程。'),
 ('tri-init','dense-prefix triangle result init elision','already-avoids-cost','DF无OF resolved position/velocity initialization副本；原static count clear仍是必须工作。'),
 ('rejected','rigid32 / contact16lane / mask-free / batch3 / first-substep deferral','historically-rejected','历史包括严重rigid/triangle回退及20m soft-chain爆炸，不能为速度恢复这些被拒方案。'),
 ('unused-stream','移除DF未使用的HalfSpringIndices流','candidate-family','源码只见分配及绑定t0；原032/075 shader均未声明/读取t0。可独立验证消除这一死资源的内存/设置成本，或与后续12byte packed spring流结合；未实现。')]:add('alpha3.9',key,title,status,reason,'00_CURRENT.md')
add('alpha3.9b','cadence2','reuse interval4→2','not-transplanted-semantic-change','减轻旧近似但仍保留一帧新邻居延迟；DF每子步更新，不导入该近似。','P10_IMPLEMENT.md')
add('alpha3.9c','flat-csr','flat bounded CSR替代持久nested membership vectors','already-avoids-donor-cost','DF没有OF host membership嵌套vector，也无其跨generation allocator指针；rigid数据按原offsets/indices直接上传。','P20_FIX.md')
add('alpha3.9c','transaction','拓扑候选原子发布/罕见路径mutex/范围验证','specific-correctness-not-performance-port','修OF/KG重载/销毁竞态与坏索引；DF采用另一资源/拓扑路径。验证思想保留在测试中，不把会改原API错误语义的wrapper当性能优化加入。','P20_FIX.md')
path=LEDGER/'history_decisions.json';old=read(path);ids={r['id'] for r in rows};write(path,[r for r in old if r['id'] not in ids]+rows)
for v in vs:
    ids=[r['id'] for r in rows if r['version']==v['version']]
    if ids:v.update(status='ideas-reviewed-candidates-pending' if v['version'] in ['alpha3.7','alpha3.9'] else 'reviewed-no-direct-port',review_ids=ids)
write(LEDGER/'versions.json',vs);event('history-reviewed',through='alpha3.9c',ideas=len(rows));state(history_review_cursor='alpha3.9c',history_next='alpha4.0');print('Recorded',len(rows),'ideas.')
