"""Export scientific plots from completed production matrices, not timing probes."""
import argparse
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager,ticker
from matplotlib.lines import Line2D
p=argparse.ArgumentParser();p.add_argument('--candidate',default='alpha-migration-final-v2');p.add_argument('--version',default='v2');a=p.parse_args()
font=Path(os.environ['WINDIR'])/'Fonts/msyh.ttc'
if font.exists():
    font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
plt.rcParams['axes.unicode_minus']=False
out=ROOT/('report-figures-'+a.version);out.mkdir(exist_ok=True)
colors={'right-faster':'#15835d','left-faster':'#c0443b','not-separated-after-Holm':'#788897'}
for api,left,suffix in [('d11','df',''),('d12','df12','-d3d12')]:
    stem=f'final-primary-{api}-{a.version}__{left}-vs-{a.candidate}{suffix}';summary=read(ROOT/'analysis'/(stem+'-summary.json'));rows=read(ROOT/'analysis'/(stem+'-scenes.json'))
    assert len(rows)==67 and summary['balanced_repeat_panels'] and summary['performance_only']
    fig,ax=plt.subplots(figsize=(10.5,20));fig.subplots_adjust(left=.35,right=.965,bottom=.055,top=.95)
    for y,r in enumerate(rows):
        value=r['paired_speedup_geomean'];lo,hi=r['paired_speedup_ci95'];color=colors[r['holm_decision']]
        if y%2==0:ax.axhspan(y-.5,y+.5,color='#f3f6f8',zorder=0)
        ax.errorbar(value,y,xerr=[[value-lo],[hi-value]],fmt='o',color=color,markersize=3.8,capsize=2,linewidth=1.1,zorder=3)
    ax.axvline(1,color='#283f56',linestyle='--',linewidth=1.2);ax.set_yticks(range(67),[f'{r["scene"]:02d}  {r["name"]}' for r in rows],fontsize=8.5);ax.set_ylim(66.7,-.7)
    ax.set_xscale('log');ax.xaxis.set_major_locator(ticker.FixedLocator([x/100 for x in range(80,131,5)]));ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'));ax.xaxis.set_minor_formatter(ticker.NullFormatter());ax.grid(axis='x',alpha=.25)
    ax.set_xlabel('速度比：原 DF 耗时 / 优化 DF 耗时（大于 1 更快）',fontsize=11)
    ratio=summary['equal_scene_geomean'];lo,hi=summary['equal_scene_geomean_ci95'];fig.suptitle(f'D3D{api[1:]} · FlexDemo 全 67 场景\n等权几何平均 {ratio:.5f}，95% CI [{lo:.5f}, {hi:.5f}]',fontsize=15,y=.986)
    ax.legend(handles=[Line2D([],[],marker='o',linestyle='none',color=colors[k],label=t) for k,t in [('right-faster','Holm校正后更快'),('not-separated-after-Holm','校正后未分离'),('left-faster','Holm校正后更慢')]],loc='upper center',bbox_to_anchor=(.5,-.025),ncol=3,fontsize=9,frameon=False)
    fig.text(.035,.008,'每场景4个独立进程对；线段为未校正95%区间，颜色按Holm校正。无窗口完整物理帧，不含Draw/Present。',fontsize=9)
    for extension in ['png','svg']:fig.savefig(out/(api+'-primary.'+extension),dpi=150)
    plt.close(fig)
write(out/'manifest.json',dict(candidate=a.candidate,time=now(),files={p.name:sha(p) for p in out.iterdir() if p.suffix in ['.png','.svg']}));print(out)
