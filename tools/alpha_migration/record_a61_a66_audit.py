from common import *
docs=read(ROOT/'history/documents-expanded.json');vs=read(LEDGER/'versions.json');rows=[]
def add(v,key,title,status,reason,file='00_CURRENT.md'):
    e=[x['copy'] for x in docs if x['version']==v and Path(x['copy']).name==file];assert e
    rows.append(dict(id=v+'-'+key,version=v,title=title,disposition=status,reason=reason,donor_evidence=e,reviewed=now()))
add('alpha6.1','rigid-parity','overlap/line continuity、64byte ABI/128thread Apply、去重复Apply','specific-vulkan-correctness','OF Vulkan SPIR-V落后于其DX11，且unique direct Accumulate后又Apply覆盖结果；DF原rigid单kernel/共享delta顺序不同，不添加OF continuity方程。')
add('alpha6.2','shader-parity','60通用模块/28特化入口及ABI/pass时序对齐','specific-backend-parity','将OF自身DX11数学提升到Vulkan，不是DF原NV算法新的无损性能项；DF原84与辅助程序独立核验。','P10_PARITY_IMPLEMENTATION.md')
add('alpha6.3','line-repair','首个被跳过rigid epoch增加16lane sparse translation','not-transplanted-dependency','修OF final-only cadence漏掉alpha2.5c补偿；DF未跳过fit，不需要这份新translation修正。')
for key,title,status,reason in [
 ('cadence','contact/shape final-only与resident调度对齐','not-transplanted-semantic-change','对齐的是OF已有降频策略，不是原NV每轮工作。'),
 ('spring-rigid','full/short spring CSR及complete-line repair/fused apply','different-math-and-layout','DF原半弹簧/rigid数据流不含OF额外repair与strain规则。'),
 ('normals','authored CSR normal/aero替代float atomic','not-transplanted-reduction-change','改变DF原法线累加次序；本任务已量化原子法线自身约1.8e-7波动，不能只因更确定就换数学。'),
 ('neighbors','每substep复用同一immutable neighbor generation','already-present','DF当前只构建一次子步邻域，后续density/velocity消费者复用；没有OF Vulkan曾有的额外velocity后重建。'),
 ('fluid','uniform/zero-optional Poly6与online covariance','different-float-operations','OF跨API公式对齐；DF保留原密度/各向异性运算，不能替换成公开重建公式。'),
 ('grid','改用DX11同源count/scatter/cooperative bounded append','different-grid-order','修OF两后端邻居布局/顺序分歧；DF使用另一套原始radix/bucket序列，不能直接移植。')]:add('alpha6.4',key,title,status,reason,'P20_PARITY_IMPLEMENTATION.md')
add('alpha6.5','gravity-damping','补Vulkan漏传gravity并对齐dynamic damping','specific-backend-correctness','OF动态dt链路错误，DF原KernelParams已经传gravity/原阻尼规则，并有原版参数字节oracle。','P20_ROOT_CAUSE_AND_FIX.md')
add('alpha6.5b','no-limit','NO_LIMIT停硬跳帧并按presentation时间平滑render','application-policy-not-port','修KG 450/900近零运动帧与平滑时标差；DF不做硬跳帧或渲染平滑。')
add('alpha6.5c','hash-prefix','去LOCKED有界自旋与重复prefix，恢复99.8%漏邻居','specific-vulkan-correctness','OF哈希重复cell和scatter前缀双加导致漏候选；DF原radix+start/end没有该LOCKED哈希/双cursor实现。完整有序邻居验证仍应借鉴。')
add('alpha6.5c','ccd-flags','single-plane mesh flag/MovingFrame重复消费/short-rest metadata','specific-vulkan-interop-correctness','补OF analytic sweep可达性和repair元数据，DF原NV三角CCD及无Body MovingFrame不具这些分歧。')
add('alpha6.6','intel-sharing','compatible typed texture取消第二device/4K bridge','outside-current-interop','优化Vulkan-DX11 Intel共享桥，DF没有这段跨API双device中转；不改变DF原NativeInterop同步以套用其数字。')
path=LEDGER/'history_decisions.json';old=read(path);ids={r['id'] for r in rows};write(path,[r for r in old if r['id'] not in ids]+rows)
for v in vs:
    ids=[r['id'] for r in rows if r['version']==v['version']]
    if ids:v.update(status='reviewed-no-direct-port',review_ids=ids)
write(LEDGER/'versions.json',vs);event('history-reviewed',through='alpha6.6',ideas=len(rows));state(history_review_cursor='alpha6.6',history_next='alpha6.7');print('Recorded',len(rows),'ideas.')
