"""Export standalone scientific accuracy/cost plots using an isolated matplotlib install."""
import argparse
import sys
from pathlib import Path

from optlib import DATA, ROOT, read


def plot(batches, destination):
    # Plotting dependencies live outside the inference environment.
    sys.path.insert(0,str(DATA/'plotting-packages'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'svg.fonttype':'none','figure.dpi':150})
    destination.mkdir(parents=True,exist_ok=True)
    for batch in batches:
        summary=read(batch/'analysis.json')
        profiles=list(summary['profiles'])
        fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
        for index,profile in enumerate(profiles):
            row=summary['profiles'][profile];n=row['n']
            label=profile.replace('native-fixed-','native-').replace('heredoc-','text-')
            y=100*row['passed']/n
            axes[0].scatter(row['totals']['seconds']/n,y,s=65,label=label)
            axes[1].scatter(row['totals']['output_tokens']/n,y,s=65,label=label)
            for ax,x in [(axes[0],row['totals']['seconds']/n),(axes[1],row['totals']['output_tokens']/n)]:
                ax.annotate(str(index+1),(x,y),xytext=(5,6),textcoords='offset points')
        for ax in axes:
            ax.set_ylim(-5,105);ax.set_ylabel('Official correctness (%)');ax.grid(alpha=.2)
        axes[0].set_xlabel('Mean agent elapsed time (seconds)')
        axes[1].set_xlabel('Mean generated tokens (thinking included)')
        axes[1].legend(loc='upper left',bbox_to_anchor=(1.02,1),fontsize=8)
        fig.suptitle(batch.name+' — paired tasks/seeds; descriptive results')
        for suffix in ('svg','png','pdf'):
            fig.savefig(destination/(batch.name+'-pareto.'+suffix),bbox_inches='tight')
        plt.close(fig)
        # Runtime distributions retain the success/failure distinction.
        import csv
        rows=list(csv.DictReader((batch/'metrics.csv').open(encoding='utf-8')))
        fig,ax=plt.subplots(figsize=(10,5),layout='constrained')
        values=[];labels=[]
        for i,profile in enumerate(profiles):
            for correct,label in [('1','correct'),('0','failed')]:
                v=[float(r['seconds']) for r in rows if r['profile']==profile and r['correct']==correct]
                if v:
                    values.append(v);labels.append(str(i+1)+' '+label)
        if values:
            ax.boxplot(values,tick_labels=labels,showmeans=True)
        ax.set_ylabel('Agent elapsed time (seconds)');ax.grid(axis='y',alpha=.2)
        ax.set_title(batch.name+' — successful and failed attempt costs')
        for suffix in ('svg','png','pdf'):
            fig.savefig(destination/(batch.name+'-runtime.'+suffix),bbox_inches='tight')
        plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('batches',type=Path,nargs='+')
    p.add_argument('--output',type=Path,default=ROOT/'figures')
    args=p.parse_args();plot(args.batches,args.output)
