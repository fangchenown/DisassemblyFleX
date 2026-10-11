"""Source/release-grounded closure of the final twenty historical versions."""
from common import *
docs=read(ROOT/'history/documents-expanded.json');versions=read(LEDGER/'versions.json');rows=[]
def add(v,key,title,status,reason):
    available=[d['copy'] for d in docs if d['version']==v]
    evidence=[p for p in available if Path(p).name in ['README.md','README_CN.md','FINAL_CANDIDATES.md','ALGORITHM_CN.md','FIX_CN.md','PORTABILITY_AUDIT.md','alpha6.7-vulkan-performance.md','P165_REVIEW.md']]
    assert evidence,(v,available)
    rows.append(dict(id=v+'-'+key,version=v,title=title,disposition=status,reason=reason,donor_evidence=evidence,source_delta=str(ROOT/'history'/v/'OpenFleX-code.patch'),reviewed=now()))
data={
'alpha6.7':[
('snapshot','延迟邻居快照、allocation rotation与private dense snapshot','already-avoids-donor-cost','DF没有OF多份位置/邻居快照复制链，不能重复计算省掉的成本。'),
('neighbor','NV quad4/fixed27/多subgroup精确邻域','different-layout-and-order','OF exact-cell布局与DF原radix桶和bounded行序不同；DF SM5也无直接Vulkan subgroup接口。保留行序的A037单独验证。'),
('triangles','static triangle inplace/32B BVH/compact prefilter','different-collision-dataflow','DF原三角kernel只写接触，未先复制OF resolved position/velocity；原CCD/层次结构不同，不能移植公开重建公式。'),
('fusion','spring/common apply、normal/aero/finalize融合','dependency-or-already-combined','OF spring融合依赖跳过full rigid fit；DF每轮真实fit。DF已有triangle normal/aero合并和finalize消费。'),
('cpu','descriptor/uniform/packet/query/transfer缓存','adapted-tested-family','Vulkan lease/handle不能直接使用；DF侧A002 descriptor/barrier批量与A006 lookup/retained/binding优化分别验证。'),
('queue','output-inclusive fence/early wait/queue family','backend-specific','Vulkan提交所有权，不是DF D3D11/12新增无损算法。'),
('reject','Oct8/cell cache/rigid LDS/worker/PGO/P165合并输出','historically-rejected','OF完整scope未获收益，P165真实FPS反而下降0.627%，不恢复。')],
'alpha6.8':[
('fusion','DX11 common Jacobi apply融合','not-transplanted-dependency','依赖OF跳过full rigid fit；DF不能用少做fit换取相同数字。'),
('identity','精确identity triangle specialization','requires-new-eligibility-proof','OF有host pose/previous pose/scale的逐位证明与失败回退；DF支持device/native源且无同等CPU镜像。未加入额外GPU读回或未经证明的恒等假设；原DF三角数学亦不同。')],
'alpha6.9':[('integration','Windows Vulkan KEngine device/command所有权与零额外Map等待','engine-backend-specific','DF原生D3D external context/interop已有单独oracle；不存在该Vulkan引擎接入层。')],
'alpha7.0':[('android','Android ARM64 ABI/backend移植','platform-specific','目标为现有Windows x64 D3D DLL，不扩展Android后端。')],
'alpha7.0-mix4':[('driver','Adreno660 CCD保留SPIR-V noinline函数边界','driver-specific-correctness','修手机驱动pipeline编译失败，不适用于本机SM5 DXBC/RTX5080。')],
'alpha7.1':[
('integrate','restitution0省bounce计算与subgroup整数bounds','already-different-kernels','DF Predict/Bounds独立且已有NV/AMD/generic归约，OF fused global-atomic bounds不存在。'),
('qualcomm','Qualcomm compacted triangle自动选择','device-dataflow-specific','移动端静态/inplace形状门控，DF原CCD和输出合同不同；不迁移厂商启用策略。')],
'alpha7.1b':[
('kept','compact grid、SDF保留8lane contact、ELL32、>=256 rigid三级归约','different-order-or-reduction','DF原neighbor radix顺序、spring八lane归约、rigid树均不同；改布局必须独立证明。原行序截断保留的A037满行返回不是OF丢完整overflow统计的early-stop。'),
('reject','scalar grid、无SDF、earlystop、degree排序、rsqrt/FMA、rigid shuffle/temporal/ranked cache','historically-rejected','历史已发生质量失败、丢overflow统计、无净收益或LDS hang，不将这些近似/失败项复活。')],
'alpha7.2':[('clock','动画时钟/solver dt分离与已发布变形的有界外推','engine-correctness-only','最终README明确核心OpenFleX/DX11算法未变；修KG虚假惯性和跳帧显示，DF不拥有动画求导/显示外推。')],
'alpha7.3':[
('sdf','live GPU负SDF scan与间接contact选择','different-contact-architecture','OF两个接触内核间选择，DF原接触流水线无相同二选一结构，不按缓存分类修改原条件。'),
('aero','两lane气动保持incident序','different-reduction','DF triangle原子贡献路径不是OF按particle CSR incident串行归约。'),
('grid','symmetric compact grid/4lane rows/bitmask批量reserve/原ID行allocation exchange','different-public-order','OF可接受非确定append，DF bounded行序/内部排序映射可观察；不能只比邻居集合。'),
('rigid','pack4 rigid/64threads、particle-owned correction CSR','different-reduction-tree','沿用的是OF原树和membership序，不能声称等价原NV fit/accumulate。'),
('packing','12B spring ELL及16bit index+32项stiff palette的8B精确编码','candidate-family','数值位模式可保留，但DF八lane访问及原split流不同；评估DF死流移除和独立内存布局收益，禁止自动照搬ELL。'),
('unroll','spring四项展开保持加法序','compiler-dependent-no-direct-port','DF原程序八lane树，机械套入OF单lane顺序将改数学；未把历史编译器的收益当本机证据。'),
('identity','identity triangle prefilter','requires-new-eligibility-proof','同6.8，DF没有可复用的host精确证明与同源triangle程序。'),
('render','52/64B vertex、BL64、mode loads、cooperative pack、tess parent reuse','engine-render-only','本任务Core DLL不拥有KG mesh skin/tess/render binding。'),
('fusion','snapshot+clear/contact accumulation融合与active-prefix mask省略','already-avoids-or-adapted','DF没有OF snapshot副本；DF spring空尾派发采用A003最大真实endpoint证明而非activeCount猜测。'),
('android','64KiB非零Fill修复与拒绝rigid shuffle/identity full collision','platform-fix-or-rejected','保留历史失败和厂商边界，不作为PC算法收益。')],
'alpha7.4':[
('device','PC Vulkan/DX11按RTX/Intel选择contact/grid/rigid/8B spring','device-dataflow-specific','不能把Intel收益外推5080。OF本身DX11 RTX 8B spring置信区间跨零，保持original。'),
('ell','PC ELL长测微小ULP放大到可见差异','historically-rejected-quality','禁止因为手机短测曾通过而重启相同改变归约顺序路线。'),
('render','BL64/minread/RTX关闭tess reuse','engine-render-only','DF不含该引擎渲染路径。')],
'alpha7.5':[
('capacity','应用cloth真实capacity对齐128且含约束引用inactive','application-capacity-policy','不能缩小用户NvFlexSolverDesc.maxParticles；A003只减少由真实spring endpoint证明无输出的工作。'),
('grid','DX11 compact grid、大范围hash/exhaustive fallback','different-layout-and-order','重排原DF空间映射/有界行，无法保证原累加次序，未采用。'),
('contact','8lane contact/GPU SDF frozen snapshot/Intel packed rigid与aero','different-reduction-or-device','DF原contact与rigid树不同；禁止改树后仅凭短测断言无影响。')],
'alpha7.6':[('lod','可选所有主模型强制LOD0','application-feature','增加适用模型范围，不是DF Core求解性能优化。')],
'alpha7.7':[('ccd','同一几何接触评估复用于response/report并证明可省CCD','different-collision-contract','DF没有OF独立response/report双评估；OF严格离散plane/无影响证明依赖其CCD方程，不能无证明移植到原NV程序。')],
'alpha7.8':[('ccd-pc','7.7 PC静态/identity/compacted特化与设备白名单','requires-new-eligibility-proof','保留原程序加派生模块思想已用于本任务；具体triangle数学/host identity证明不同，5080白名单不等于DF可直接启用。')],
'alpha7.9':[('placeholder','KG占位3vertex显式清零保留退化triangle/shape槽','engine-input-correctness','修应用未初始化默认构造，DF只消费调用方提供的几何，不含该占位构造。')],
'alpha8.0':[
('identity','精确identity TransformMeshPoint省略与1mesh/1shape/6contact参数特化','requires-new-eligibility-proof','要求逐位参数、previous pose、scale、uniform phase证明；DF device输入和callback失效关系未满足，不能假定历史测试场景恒真。'),
('reject','rigid wave/pack8/shared shape/bary reuse/analytic projection/rest-first/descriptor cache','historically-rejected','包含刚体最大0.624m差异和CPU回退，不采用。A037 current-distance-first按DF原指令独立试验。')],
'alpha8.1':[('pc','8.0 PC迁移，RTX Vulkan无益关闭，DX11/Intel部分2–3%','device-dependent-eligibility','OF旧DX浮点特化失败，v4才接受；uniform phase遥测未命中不可算收益。DF缺同源数学和门控证明，保留原程序。')],
'alpha8.2':[
('frequency','恢复full frequency约束与去近似','already-present','DF本来每轮原约束，不先降低质量再把恢复作为优化。'),
('upload','重复upload缓存与normal readback合并','different-observable-state','DF无OF float4/float3 CPU镜像；SetSprings重写共享radix/public maps、SetRigids重置mutable poses，不能仅凭输入相同跳过。'),
('radix','Vulkan稳定8bit radix','candidate-family','整数稳定排序可适配DF；须保留公开front/back、尾元素、低有效位和混合长度调用。独立两8bit+原余pass方案待直接差分及FlexDemo。'),
('pressure','inflatable并行reduction默认关闭','historically-rejected-quality','长测浮点树差异累积，保留DF原压力归约。')],
'alpha8.2b':[
('force','精确IEEE GPU forcefield替代CPU往返','already-avoids-donor-cost','本任务固定原NV Ext GPU forcefield，没有OF CPU往返；不扩展Ext范围。'),
('scratch','Vulkan scratch复用及release/invalidation','already-present-concept','DF按maxParticles预分配接触scratch，没有OF逐active增长重建。'),
('register','accumulator寄存器压力保持加法序与离线shader','backend-specific-or-already-present','历史保留Vulkan，DX11无益或旧rounding分歧；DF原84已离线生成，不能套用不同程序的编译收益。'),
('reject','Predict snapshot融合/调度捷径/普通浮点force/pressure重排','historically-rejected','不允许少算或改变精确运算获取本轮收益。')],
'alpha8.2c':[
('tearing','tearing SIMD','outside-core-frozen-ext','这是Ext优化，当前性能归因固定原NV Ext；单独替换Ext会改变范围和基准。'),
('host','三输入比较batch线程、float3未变prefix','already-avoids-donor-cost','DF没有OF canonical host vectors和相关线程池比较，输入缓存还需考虑原API可观察重置副作用。'),
('scratch','contact scratch reserve','already-present','DF原maxParticles容量预分配，无相同重复扩容成本。'),
('reject','mixed-contact merge/active SIMD/wideTriNormals/joint readback','historically-rejected','完整scope回退，不纳入；历史67场景约0.14%增量也不当可靠总体收益。')]
}
for v in versions:
    for args in data.get(v['version'],[]):add(v['version'],*args)
old=read(LEDGER/'history_decisions.json');ids={r['id'] for r in rows};write(LEDGER/'history_decisions.json',[r for r in old if r['id'] not in ids]+rows)
for v in versions:
    rs=[r for r in rows if r['version']==v['version']]
    if rs:v.update(status='ideas-reviewed-candidates-pending' if any(r['disposition']=='candidate-family' for r in rs) else 'reviewed-no-direct-port',review_ids=[r['id'] for r in rs])
write(LEDGER/'versions.json',versions);state(history_review_cursor='alpha8.2c',history_next=None);event('history-reviewed',through='alpha8.2c',ideas=len(rows));print('Recorded',len(rows),'ideas in',len(data),'versions.')
