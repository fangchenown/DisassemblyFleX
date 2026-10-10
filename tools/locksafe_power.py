"""Thread-scoped idle-sleep prevention and suspend detection for headless runs.

No display request, input simulation, power-plan mutation, or away mode.
Manual suspend remains under user control; contaminated timing is identified.
"""
import ctypes as ct
import atexit,time,subprocess,json
_kernel=ct.WinDLL('kernel32',use_last_error=True)
_kernel.SetThreadExecutionState.argtypes=[ct.c_uint32]
_kernel.SetThreadExecutionState.restype=ct.c_uint32
_realtime=ct.WinDLL('api-ms-win-core-realtime-l1-1-1.dll',use_last_error=True)
_realtime.QueryInterruptTime.argtypes=[ct.POINTER(ct.c_uint64)]
_realtime.QueryInterruptTime.restype=None
_kernel.QueryUnbiasedInterruptTime.argtypes=[ct.POINTER(ct.c_uint64)]
_kernel.QueryUnbiasedInterruptTime.restype=ct.c_int
def suspend_clock():
 biased=ct.c_uint64();unbiased=ct.c_uint64()
 _realtime.QueryInterruptTime(ct.byref(biased))
 if not _kernel.QueryUnbiasedInterruptTime(ct.byref(unbiased)):raise ct.WinError(ct.get_last_error())
 return dict(interrupt_100ns=biased.value,unbiased_100ns=unbiased.value)
def suspended_ms(first,last):
 return ((last['interrupt_100ns']-first['interrupt_100ns'])-(last['unbiased_100ns']-first['unbiased_100ns']))/10000.
class SystemRequired:
 def __init__(self):
  self.previous=_kernel.SetThreadExecutionState(0x80000001)
  if not self.previous:raise ct.WinError(ct.get_last_error())
  self.active=True;atexit.register(self.close)
 def close(self):
  if self.active:
   if not _kernel.SetThreadExecutionState(self.previous|0x80000000):raise ct.WinError(ct.get_last_error())
   self.active=False
 def __enter__(self):return self
 def __exit__(self,*args):self.close()
if __name__=='__main__':
 with SystemRequired() as request:
  first=suspend_clock()
  result=subprocess.run(['powercfg','/requests'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
  time.sleep(.25);last=suspend_clock()
  print(json.dumps(dict(previous=request.previous,requested='ES_CONTINUOUS|ES_SYSTEM_REQUIRED',display_required=False,
   powercfg_exit=result.returncode,powercfg=result.stdout.decode('gbk',errors='replace'),powercfg_stderr=result.stderr.decode('gbk',errors='replace'),first=first,last=last,suspended_ms=suspended_ms(first,last)),ensure_ascii=True))
 assert not request.active
