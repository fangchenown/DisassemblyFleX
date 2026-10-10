"""Wait for owned benchmark completion, then audit and generate reviewable output."""
import os,json,time
import fix_task as task
import performance_benchmark as b
import fix_quality,fix_analyze,fix_profile_analyze,fix_audit,fix_report
def main():
    receipt=task.ROOT/'jobs/analysis-controller.json'
    b.write(receipt,dict(pid=os.getpid(),status='WAITING_MAIN',started=b.now()))
    with task.SystemRequired():
        while True:
            state=json.loads((task.ROOT/'jobs/main-v2-controller.json').read_text(encoding='utf-8'))
            if state['status']=='PASS':break
            assert state['status']=='RUNNING',state
            time.sleep(1)
        b.write(receipt,dict(pid=os.getpid(),status='RUNNING',started=b.now()))
        fix_quality.main()
        for suite in ['main-v2','emit-v2','long-v2','gpu-v2']:fix_analyze.analyze(suite)
        fix_profile_analyze.main();fix_audit.main();fix_report.main()
    b.write(receipt,dict(pid=os.getpid(),status='PASS',finished=b.now(),report=str(task.ROOT/'delivery/REPORT_CN.txt')))
if __name__=='__main__':main()
