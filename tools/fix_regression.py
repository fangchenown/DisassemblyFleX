"""Run the established 13 API gates in the repair task's evidence directory."""
import shutil
import fix_task as task
import regression_suite as suite
fixture=task.ROOT/'demo-runs/reference-scene47-30-v1/params.bin'
fixture.parent.mkdir(parents=True,exist_ok=True)
if not fixture.exists():shutil.copy2(task.WS/'Build/DisassemblyFleX-20261009/demo-runs/reference-scene47-30-v1/params.bin',fixture)
suite.ROOT=task.ROOT
if __name__=='__main__':suite.main()
