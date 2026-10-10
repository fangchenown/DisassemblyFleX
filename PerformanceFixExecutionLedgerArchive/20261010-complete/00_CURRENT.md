# DisassemblyFleX 正式性能修复 — COMPLETE

正式源码已修复，最终构建 final-v2。
DLL SHA256：0407fe58026c9d8dc93c36d5adf42d554bb3e660fe1f79eafd666d9a3e81e357
交付：Build/DisassemblyFleXPerformanceFix-20261010/delivery/
中文报告：该目录 REPORT_CN.txt。

有效 FlexDemo 1533 次、484440 帧；全部67场景/两后端、三项发射负载、五项1800帧长时间测试、CPU/GPU诊断。13项既有回归、33确定性粒子案例、84 shader程序一致、专用资源池/多solver/外部Direct+Compute队列生命周期门禁均通过。

D3D12 新/旧重建版耗时比 0.248760；新/原版 1.102559。仍有残余派发与状态管理差距，详见报告；不宣称所有输入逐字节或性能等价。

正式运行不含早期final-v1预验main-v1（SUPERSEDED）。旧构建、旧交付、两次先前归档与alpha8.2c任务保留。无活动作业；不需要恢复已完成的测试。
