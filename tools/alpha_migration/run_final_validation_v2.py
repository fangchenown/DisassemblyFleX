"""Fresh release validation after removing all derived floating-point programs."""
from common import *
here=Path(__file__).parent;candidate='alpha-migration-final-v2';job=ROOT/'jobs/final-validation-v2-pipeline.json';write(job,dict(status='WAITING',pid=os.getpid(),candidate=candidate,started=now()))
try:
    dependency=ROOT/'jobs/affinity-confirmation-pipeline.json'
    while read(dependency)['status'] in ['WAITING','RUNNING']:time.sleep(10)
    assert read(dependency)['status']=='PASS','Inspect affinity follow-up before compiling'
    write(job,dict(status='RUNNING',pid=os.getpid(),candidate=candidate,started=now()))
    def run(tool,args,name):
        p=ROOT/'jobs'/f'{name}.json'
        if p.exists() and read(p)['status']=='PASS':return
        command([sys.executable,'-B',here/(tool+'.py'),*args],name,cwd=WS,timeout=14400)
    run('build_candidate',['--name',candidate,'--source','current'],candidate+'-build-command')
    run('run_regressions',['--build',candidate,'--name','final-v2-regressions'],'final-v2-regression-command')
    run('run_spring_extent_oracle',['--base','control-v0','--candidate',candidate,'--name','final-v2-spring-oracle'],'final-v2-spring-command')
    run('run_extended_radix_oracle',['--base','control-v0','--candidate',candidate,'--name','final-v2-radix-oracle'],'final-v2-radix-command')
    run('audit_shaders',[candidate],'final-v2-shader-audit-command')
    auxiliary=read(ROOT/'builds'/candidate/'generated/aux_shader_manifest.json');assert len(auxiliary)==5 and all(x['kind']=='authored-integer-helper' and not x.get('instructions') for x in auxiliary)
    write(ROOT/'evidence/final-v2-active-shaders.json',dict(status='PASS',original_containers=84,integer_auxiliary=5,derived_floating_point_programs=0,entries=auxiliary))
    def perf(suite,variants,scenes=None,frames=1200,warmup=120,repeats=4,emit=False,extra=None):
        args=['--suite',suite,'--variants',','.join(variants),'--frames',str(frames),'--warmup',str(warmup),'--repeats',str(repeats)]
        if scenes:args+=['--scenes',scenes]
        if emit:args+=['--emit']
        for key,value in (extra or {}).items():args+=['--env',key+'='+value]
        run('run_matrix',args,suite+'-command');run('retest_clock_blocks',['--suite',suite,'--name',suite+'-clock'],suite+'-clock-command')
        for left in variants[:-1]:run('analyze_primary',['--suite',suite,'--left',left,'--right',variants[-1]],suite+'-'+left+'-analysis')
    def quality(suite,left,right,scenes=None,frames=1200,emit=False):
        args=['--suite',suite,'--variants',left+','+right,'--frames',str(frames),'--warmup','120','--repeats','3','--capture','1']
        if scenes:args+=['--scenes',scenes]
        if emit:args+=['--emit']
        run('run_matrix',args,suite+'-command')
        for tool in ['quality_analysis','assess_quality','compare_aux_outputs','quality_flags']:run(tool,['--suite',suite,'--left',left,'--right',right],suite+'-'+tool)
    for api,left,control,suffix in [('d11','df','control-v0',''),('d12','df12','control-v0-d3d12','-d3d12')]:
        right=candidate+suffix;suite='final-primary-'+api+'-v2';perf(suite,[left,control,right]);run('analyze_primary',['--suite',suite,'--left',left,'--right',control],suite+'-no-change-analysis')
    for api,left,suffix in [('d11','df',''),('d12','df12','-d3d12')]:
        right=candidate+suffix;quality('final-quality-'+api+'-v2',left,right)
        suite='final-emission-'+api+'-v2';perf(suite,[left,right],scenes='39,40,64,65,66',frames=1800,warmup=180,emit=True)
        run('characterize_emission',['--suite',suite,'--left',left,'--right',right],suite+'-semantics')
        quality('final-emission-quality-'+api+'-v2',left,right,scenes='39,40,64,65,66',frames=1800,emit=True)
        quality('final-long-'+api+'-v2',left,right,scenes='0,3,9,25,27,47,56,65',frames=6000)
        suite='final-cpu-'+api+'-v2';run('run_matrix',['--suite',suite,'--variants',left+','+right,'--scenes','0,9,25,27,33,47,64,65','--frames','1200','--warmup','120','--repeats','4','--profile','4'],suite+'-command')
        run('retest_clock_blocks',['--suite',suite,'--name',suite+'-clock'],suite+'-clock-command');run('analyze_cpu_counters',['--suite',suite,'--left',left,'--right',right],suite+'-analysis')
        scenes='17,31' if api=='d11' else '31,33,44';perf('final-affinity-'+api+'-v2',[left,right],scenes=scenes,frames=2400,warmup=240,repeats=8,extra={'FLEXPERF_PROCESS_AFFINITY':'0xfff'})
    suite='final-rare-rope-d12-v2';left='df12';control='control-v0-d3d12';right=candidate+'-d3d12'
    run('run_matrix',['--suite',suite,'--variants',','.join([left,control,right]),'--scenes','3','--frames','1200','--warmup','120','--repeats','32','--capture','1'],suite+'-command')
    for a,b in [(left,control),(left,right)]:
        for tool in ['quality_analysis','assess_quality','compare_aux_outputs','quality_flags']:run(tool,['--suite',suite,'--left',a,'--right',b],suite+'-'+a+'-'+b+'-'+tool)
    for variant in [left,control]:run('characterize_baseline',['--suite',suite,'--variant',variant],suite+'-'+variant+'-baseline')
    write(job,dict(status='PASS',pid=os.getpid(),candidate=candidate,finished=now(),scope='All measurements complete; explicit final numerical/performance review and publication remain required.'))
except BaseException as e:write(job,dict(status='FAIL',pid=os.getpid(),candidate=candidate,finished=now(),error=str(e)));raise
