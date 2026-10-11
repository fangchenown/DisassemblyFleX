from common import *
docs=read(ROOT/'history/documents-expanded.json');vs=read(LEDGER/'versions.json');rows=[]
def add(v,key,title,status,reason,filename):
    matches=[d['copy'] for d in docs if d['version']==v and Path(d['copy']).name==filename and '/phases/' in d['copy'].replace('\\','/')];assert matches,(v,filename)
    record=next(x for x in vs if x['version']==v)
    rows.append(dict(id=v+'-'+key,version=v,title=title,disposition=status,reason=reason,donor_evidence=matches,source_delta=[str(ROOT/'history'/v/(repo+'-code.patch')) for repo in ['OpenFleX','KG3D_OpenFleX']],source_identity={repo:aliases[-1]['commit'] for repo,aliases in record['git'].items()},reviewed=now()))
add('alpha2.6','inverse-map','线性粒子→authored vertex反向桶','engine-only','把KG graph commit的O(P*V)扫描改成O(P+V)并保留first/last owner语义；DF标准API没有authored render vertex映射层。','P03_FIX_DESIGN.md')
add('alpha2.6','soft-owner','first-match vertex→soft cluster表','engine-only','避免KG construction的O(V*S)查找；DF NvFlexSetRigids接收调用者已给定的成员索引，不构建渲染顶点soft绑定。','P03_FIX_DESIGN.md')
add('alpha2.6','offline-dxbc','11个Body程序FXC移至构建期','already-present','DF原84shader及本轮辅助程序均在构建期生成/嵌入，运行时只CreateComputeShader/PSO；没有重复FXC编译可删。历史也明确拒绝为数毫秒引入跨device/DLL COM对象永久cache。','P03_FIX_DESIGN.md')
add('alpha2.7','bootstrap','新对象一次性GPU pose bootstrap与发布顺序','engine-specific-correctness','用graph-local initialize-to-skin标记只初始化新对象，先生成动画target/Frame数据再发布；修KG第一帧姿态，不改变DF solver输入规则或省略首步。','P03_FIX_DESIGN.md')
add('alpha2.7b','history-handoff','新图继承存活对象GPU runtime history','engine-only','精确range匹配后GPU copy MoveLimit/render历史，保留retired buffers，不等待/回读；DF没有可替换KG FrameGraph，不能把拓扑提交收益算到求解器。','P04_IMPLEMENT.md')
add('alpha2.7c','moving-centers','MovingFrame同时变换rigid centers','engine-specific-input-correction','KG曾只把粒子从asset-local变到world，未变rigidTranslations；通过interop可写UAV修输入。DF按调用者给定坐标计算，没有该Body MovingFrame生产者，不新增变换方程。','P01_REPRO.md')
add('alpha2.7d','uav-alias','RigidTranslations复用entry-local u2并恢复','already-compatible-different-layer','修KG shader超出FL11.0的u7上限；DF各原shader及Context都遵守8UAV，新增helper亦如此；新D11绑定优化明确保留全8槽处理。','P03_FIX.md')
add('alpha2.8','singleton','孤立单粒子soft island的初始化/phase来源修复','engine-specific-correctness','仅无spring、单rigid成员、单粒子cluster且全部skin权重同属它时，复用MoveLimit/parent animation target。DF没有soft render vertex的这个初始化缺口；更改phase来源会改变其用户输入。','P03_DESIGN.md')
add('alpha2.9','native-vs','原生VS项目/props/targets/依赖图迁移','build-organization-only','移除KG NMake包壳、显式Core C++17和wrapper C++14、构建期shader依赖；DF已经是直接CMake/MSVC工程。source pragma中kFinalShapePasses==1的if constexpr修复仅针对OF额外strain/convergence循环，DF不存在该除零式。','20_native_project_design.md')
add('alpha2.9b','prefix','KG_OPENFLEX类型/函数/宏前缀迁移','naming-only','代码级更名与工程集成，不是求解器算法优化；DF必须保留NvFlex导出ABI，不能移植这些重命名。','20_prefix_migration.md')
add('alpha3.0','initial-wake','按graph pending列表消费初始化marker','engine-specific-correctness','不再用object warm标志代替graph-local marker，首次真实solver提交后释放；DF没有该标记和动作切换生命周期。','20_root_cause.md')
add('alpha3.0b','zero-delta','host-specific zero-delta固定步提交策略','engine-specific-scheduling','游戏端未暂停时即使presentation dt=0仍提交固定步；editor/console/movie维持跳过。是调用者策略修正，DF内部不改变传入dt/substeps或擅自跳步。','40_fix_tests.md')
add('alpha3.0c','standby','保持STANDBY时控制标志触发MoveLimit restore','engine-specific-correctness','HLSL新增controlRequestsRestore谓词，避免只等runtime bit的永久pin；DF原solver只遵守质量/约束，没有此动画状态机。','40_fix_and_tests.md')
path=LEDGER/'history_decisions.json';old=read(path);ids={r['id'] for r in rows};write(path,[r for r in old if r['id'] not in ids]+rows)
for v in vs:
    ids=[r['id'] for r in rows if r['version']==v['version']]
    if ids:v.update(status='reviewed-no-direct-port',review_ids=ids)
write(LEDGER/'versions.json',vs);event('history-reviewed',through='alpha3.0c',ideas=len(rows));state(history_review_cursor='alpha3.0c',history_next='alpha3.1');print('Recorded',len(rows),'ideas.')
