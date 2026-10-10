# DisassemblyFleX 性能对比 — COMPLETE

1402 次 FlexDemo 成功运行。主协议执行1074次（含时钟质量标志整对替换），最终使用1072次，67场景×2后端×4对。其余为pilot、CPU/GPU诊断、3个发射场景和资源复用消融。

D3D11等权几何平均候选/原版耗时比0.9979609；D3D12为4.4412701。原始正式候选DLL哈希保持8e4a8f1bb479f129147855b9656caa0379ccc2a9c91838604d3cae63a1191090。

中文报告：Build/DisassemblyFleXPerformance-20261010/delivery/REPORT_CN.txt
最终审计：Build/DisassemblyFleXPerformance-20261010/evidence/FINAL_AUDIT.json
所有原始运行：Build/DisassemblyFleXPerformance-20261010/runs/
复现入口：DisassemblyFleX/PERFORMANCE_TESTING_CN.txt

本任务完成性能比较和归因，不将诊断优化DLL作为新的正式交付。D3D12常量缓冲区和描述符堆复用是主要性能机会；诊断变体未做完整API/外部Context生命周期回归。

保留异常证据：辅助时钟−1.0003ms的整对被保守替换；两个早期代理编译失败；两个诊断控制器在全部子测试成功后的事件写入TypeError已补记。详细事件和记录均保留。

此前源码重建归档与独立alpha8.2c任务保持原状。没有活动作业，无需恢复已完成测试。
