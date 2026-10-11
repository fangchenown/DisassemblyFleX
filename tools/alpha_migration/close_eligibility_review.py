"""Close ideas whose necessary equivalence proofs do not hold for DF's ABI."""
from common import *
decisions={
'alpha0.2-uniform-fluid':('not-transplanted-unproven-input-invariant','OF uniform-fluid特化需要所有活跃phase和可选参数的完整不变量。DF支持设备buffer/外部context和回调改写，当前没有等价的host canonical phase镜像。只用场景初值判定会让后续Set/回调误用特化；额外GPU归约/间接选择属于另一个未验证设计。本次不使用未经证明的uniform假设。'),
'alpha0.4-E16':('not-transplanted-unproven-float-bound','sphere-cell AABB拒绝需要同时涵盖DF原浮点坐标量化、128周期hash别名、半径边界和大坐标的严格保守界。OF epsilon建立在另一套exact-cell网格上，不能当DF无false-negative证明。保留原27桶遍历；已验证的A037仅变换原有布尔谓词/满行无后效分支。'),
'alpha1.7-capsule-static':('not-transplanted-unproven-dirty-contract','DF SetShapes各geometry/pose/previousPose/flags输入可来自设备和注册外部buffer。没有OF同源、可证明完整的静态capsule generation标记；仅缓存地址或CPU旧副本不能识别外部修改。增加强制同步读回违反低开销适配目标，也没有可用收益证据。本次保持原显式更新。')
}
rows=read(LEDGER/'history_decisions.json')
for row in rows:
    if row['id'] in decisions:
        status,reason=decisions[row['id']];row.update(disposition=status,closure_reason=reason,closed=now())
write(LEDGER/'history_decisions.json',rows);event('eligibility-review-closed',ids=list(decisions),scope='No unsupported equality assumptions introduced; no claim these ideas are universally impossible.')
