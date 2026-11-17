"""Separate output-cap and context-cap evidence in prior raw length responses."""
import collections
import csv
import json
from pathlib import Path

from optlib import DATA, ROOT, read, save


def main():
    metrics=DATA.parent/'eval-v2/batches/extended-24-v6-common/metrics.csv'
    counts=collections.Counter();details=[]
    for row in csv.DictReader(metrics.open(encoding='utf-8')):
        if row['model']!='qwen3.5:9b':continue
        path=Path(row['attempt']);result=read(path/'result.json');profile=result['profile_config']
        for index,response in enumerate(read(path/'ollama-responses.json')):
            if response.get('done_reason')!='length':continue
            generated=response.get('eval_count',0);prompt=response.get('prompt_eval_count',0)
            output_bound=generated>=profile['output_tokens']
            context_bound=prompt+generated>=profile['context']
            category='both' if output_bound and context_bound else 'output_cap' if output_bound else 'context_cap' if context_bound else 'other_length'
            counts[category]+=1
            details.append({'task_id':row['task_id'],'seed':int(row['seed']),'response':index,'prompt_tokens':prompt,
                            'generated_tokens':generated,'category':category})
    report={'source':str(metrics),'length_responses':len(details),'categories':dict(counts),
        'rule':'Ollama done_reason=length; output bound if eval_count >= configured num_predict; context bound if reported prompt+output >= num_ctx. Both may bind simultaneously. This is observable boundary evidence, not internal model reasoning diagnosis.',
        'responses':details}
    save(ROOT/'baseline_length_causes.json',report)
    print(json.dumps({'length_responses':len(details),'categories':dict(counts)}))


if __name__=='__main__':main()
