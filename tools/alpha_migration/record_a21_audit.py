"""All 35 alpha2.1 waves, including retained approximations and reversions."""
from common import *
root='History/OpenFlexAlpha21QModelEditorOptimizationLedger-2026-08-14/OpenFlexExecutionLedger/phases/'
data={
1:('compact dynamic spring source rows','historically-rejected','OF固定/尾部线程早退已便宜，新增随机indirection更慢；DF只考虑不改变实际粒子索引的整组空尾裁剪。'),
2:('final public frame rigid fit','not-transplanted-semantic-change','跳过非末轮/子步rigid fit，改变结果。'),
3:('final swept triangle only','different-schedule','OF有pre/post两次sweep才可讨论冗余；DF当前每子步只有一次原碰撞生成，不删除它。'),
4:('final public substep contacts/shapes','not-transplanted-semantic-change','粒子接触/解析形状降低频率改变真实工作，历史截图门不替代结果一致。'),
5:('rigid-aware two-projection spring batch','not-transplanted-dependency','依赖前面已跳过的rigid/contact epochs；DF这些epoch非空且有callback，不可直接合并。'),
6:('dense active-prefix structural extent','candidate-family','DF多数pass本来按active count，但spring仍capacity；需按最大引用ID证明空尾。公共readback默认容量不可偷缩。'),
7:('three-projection spring batch','not-transplanted-dependency','依赖已降频的constraint epochs，改变DF每轮全局交错与Jacobi快照。'),
8:('two-frame neighbor cadence','not-transplanted-semantic-change','允许新邻居晚一帧进入，不是无损。'),
9:('three-frame neighbor cadence','not-transplanted-semantic-change','允许新邻居晚两帧进入，不满足结果约束。'),
10:('final-substep cloth aerodynamics','not-transplanted-semantic-change','累积dt后只在末子步算风力，输入位置/速度不同，非等价。'),
11:('aero apply fused into finalize','already-present-concept','DF UpdateTriangles写mDeltas后Finalize直接消费，没有独立OF aero velocity-apply dispatch。'),
12:('aero accumulation fused with normal CSR gather','already-combined-different-layout','DF UpdateTriangles已同时生成face normal和气动力delta；后续vertex normal是原atomic累加布局，CSR改序需额外数值准入。'),
13:('three-frame aerodynamic diagnostics','no-historical-gain','每帧wind变化使缓存总失效，历史没有可计收益。'),
14:('pure-normal/aero specialization diagnostics','no-historical-gain','OF仍每帧eval，未获实测收益；DF原内核结构不同。'),
15:('temporal wind sampling','not-transplanted-semantic-change','忽略连续wind变化至采样帧，改变风力和结果。'),
16:('four-frame neighbor cadence','not-transplanted-semantic-change','新进入接触最多推迟三帧；2x GPU来自少做真实broadphase，不能作为DF同工作加速。'),
17:('per-frame deferred command list','historically-rejected','记录/Finish/Execute开销使生产scope回退，不移植。'),
18:('six-UAV Integrate snapshot fusion','historically-rejected','扩大UAV绑定和写流量超过省下copy，DF亦无OF的三个snapshot流。'),
19:('consume completed constraint epochs','not-transplanted-dependency','只有OF已经合批完成的逻辑epochs才可跳host调用；DF这些约束仍每轮真正执行。'),
20:('persistent timestamp query pool','already-present','DF QueryTimers按高水位reserve并复用queries，clear只重置used计数，不每帧重建对象。'),
21:('spring constant content cache','candidate-family','DF共享KernelParams每Update仅一次上传，不像OF每pass48-byte constants；可评估相邻重复substep constant map，但须保持callbacks/外部context和D3D12 CBV行为。'),
22:('rigid/shape/finalize/contact constant caches','already-avoids-most-cost','DF这些pass已共用根CB，不每operation重传单独payload。不能把OF省下的多次UpdateSubresource外推。'),
23:('solver/finalize/contact merge constants','already-avoids-most-cost','DF root params一次Update构建；没有OF额外contact-merge constants。'),
24:('latency sampling cadence4','not-transplanted-api-semantics','返回旧帧latency会改变原接口时效；本任务不靠少测量或延迟返回获得收益。'),
25:('resident notification elimination / pending queue count','engine-only','KG Scene/Body通知及mutex队列，不在DF DLL的求解器接口。'),
26:('capability-known substep no-op host calls','historically-rejected','OF总scope回退；DF空派发候选A001单独验证，不继承历史更改。'),
27:('hazard-aware sparse CS restore','historically-rejected','比保留控制慢5.3%，DF原native-state合同也不同。'),
28:('persistent control atlas','historically-rejected-engine-only','整atlas上传及shader unpack成本超过省API调用。'),
29:('restored CPU attribution','diagnostic-only','证明此前低点受漂移影响。本任务用独立进程配对与置信区间，不按最好单次。'),
30:('latency sampling cadence16','not-transplanted-api-semantics','同Wave24，不能用旧样本充当每帧原语义。'),
31:('skip reused-neighbor public snapshot','historically-rejected','历史明确改变public snapshot且完整scope回退；DF没有OF额外snapshot copies。'),
32:('reusable Integrate command list','historically-rejected','ExecuteCommandList仍更贵，完全回退。'),
33:('halve resident substeps','not-transplanted-semantic-change','直接少算子步；历史CPU减少反而GPU依赖等待更大，不允许。'),
34:('8-slot timestamp query ring','historically-rejected','未修复首Predict依赖间隔，增加查询/CPU压力；DF当前池化保持原语义。'),
35:('solve cadence3 + render extrapolation','historically-rejected-visual','原用户已观察严重抖动并回退，本任务不恢复这种整帧跳算路线。')}
rows=[]
for num,(title,status,reason) in data.items():
    donor=root+('P02_ALPHA21_ALGORITHM_MEMORY_WAVES.md' if num<=18 else 'P03_ALPHA21_SUBMISSION_AND_FUSION.md');assert (WS/donor).exists()
    rows.append(dict(id=f'alpha2.1-W{num:02d}',version='alpha2.1',wave=num,title=title,disposition=status,reason=reason,donor_evidence=donor,df_evidence=['src/solver/ParticleStep.cpp','src/api/UpdateApi.cpp','src/runtime/D3D11Context.cpp'],reviewed=now()))
path=LEDGER/'history_decisions.json';old=read(path);ids={r['id'] for r in rows};write(path,[r for r in old if r['id'] not in ids]+rows)
vs=read(LEDGER/'versions.json')
for v in vs:
    if v['version']=='alpha2.1':v.update(status='ideas-reviewed-candidates-pending',review_ids=sorted(ids))
write(LEDGER/'versions.json',vs);event('history-reviewed',version='alpha2.1',ideas=len(rows));state(history_review_cursor='alpha2.1',history_next='alpha2.2');print('Recorded',len(rows),'waves.')
