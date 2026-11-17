"""Aggregate the single pilot without reading or rewriting candidate algorithms."""
import csv
import json
from shared import ROOT,REPO,DATA,MODEL,MODEL_DIGEST,PROFILE,CONFIG,SEED,read,save,digest


def collect(task,condition):
    folder=DATA/'runs'/('osa-'+task['task_id']+'-'+condition)
    if not (folder/'complete.json').exists():return None
    completion=read(folder/'complete.json');r=read(folder/'result.json') if (folder/'result.json').exists() else {}
    raw=read(folder/'ollama-responses.json') if (folder/'ollama-responses.json').exists() else []
    wire=read(folder/'ollama-requests.json') if (folder/'ollama-requests.json').exists() else []
    calls=r.get('model_calls',len(wire));missing=max(0,calls-len(raw))
    tests=r.get('public_tests',[]);failed=False;recovered=False
    for event in tests:
        if event['returncode']!=0:failed=True
        elif failed:recovered=True
    judge=read(folder/'judge/evaluation.json');source=folder/'solution.py'
    if source.exists():assert digest(source)==digest(folder/'judge/solution.py')
    assessment=read(folder/'timeout-assessment.json') if (folder/'timeout-assessment.json').exists() else {}
    codes=[m.get('error_code') for m in judge.get('metadata',[]) if m.get('error_code') is not None]
    return {'task_id':task['task_id'],'difficulty':task['difficulty'],'condition':condition,'seed':SEED,
        'official':completion['evaluation'],'correct':int(completion['evaluation']=='pass'),
        'generation_tokens_observed':sum(x.get('eval_count',0) for x in raw),'unobserved_tokens_upper':4096*missing,
        'model_calls':calls,'uncaptured_replies':missing,'inference_wall_seconds':completion['inference_wall_seconds'],
        'judge_wall_seconds':completion['judge_wall_seconds'],'format_errors':r.get('format_errors',0),
        'missing_submission':not source.exists(),'public_recovery':recovered,'public_pass':any(t['returncode']==0 for t in tests),
        'actions':r.get('actions',0),'repairs':r.get('repairs',0),'agent_or_generation_status':assessment.get('effective_status',r.get('status','SupervisedStop')),
        'length_replies':sum(x.get('done_reason')=='length' for x in raw),'official_error_codes':','.join(map(str,codes)),
        'judge_resource_failure':judge.get('resource'),
        'sampler_wire_verified':r.get('sampler_wire_verified',False),'artifact':str(folder)}


def main():
    manifest=read(DATA/'manifest.json');status=read(DATA/'status.json')
    rows=[r for task in manifest['tasks'] for condition in ('A','B') if (r:=collect(task,condition))]
    total={}
    for c in ('A','B'):
        group=[r for r in rows if r['condition']==c]
        total[c]={'completed':len(group),'correct':sum(r['correct'] for r in group),
            **{k:sum(r[k] for r in group) for k in ('generation_tokens_observed','unobserved_tokens_upper','model_calls',
                'inference_wall_seconds','judge_wall_seconds','format_errors','missing_submission','public_recovery')},
            'official_failures':sum(not r['correct'] and not r['missing_submission'] for r in group)}
    groups={name:[] for name in ('both','neither','agent_only','one_shot_only','unpaired_incomplete')}
    def find(key,c):return next((r for r in rows if r['task_id']==key and r['condition']==c),None)
    for t in manifest['tasks']:
        a,b=find(t['task_id'],'A'),find(t['task_id'],'B')
        name='unpaired_incomplete' if a is None or b is None else ('both' if a['correct'] and b['correct'] else
            'agent_only' if a['correct'] else 'one_shot_only' if b['correct'] else 'neither')
        groups[name].append(t['task_id'])
    save(DATA/'summary.json',{'manifest_sha256':digest(DATA/'manifest.json'),'analysis_source_sha256':digest(__file__),'status':status,'totals':total,'groups':groups,'rows':rows})
    save(ROOT/'results.json',{'analysis_source_sha256':digest(__file__),'status':status,'totals':total,'groups':groups,'rows':rows})
    with (ROOT/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['task_id']);writer.writeheader();writer.writerows(rows)
    lines=['# Quick Qwen one-shot vs mini-SWE-agent pilot','',
        f"Status: **{status['status']}**; total experimental wall including synthetic sanity, inference, grading and cleanup: **{status['experimental_wall_seconds']:.1f}s / 2,100s**. Hard ceiling respected: {status['within_hard_ceiling']}. No parameter tuning or extra benchmark attempts.",'',
        f"Model: `{MODEL}`, Q4_K_M; digest `{MODEL_DIGEST}`. mini-SWE-agent2.4.6 / LiteLLM1.81.16 / Ollama0.40.16, endpoint127.0.0.1:11435. Shared sampler: context16,384, output4,096, thinking off, T=.2, top-p=.9, top-k40, min-p0, repeat penalty1, repeat window64, presence/frequency0, seed{SEED}.",'',
        f"A uses the unchanged `{PROFILE}` agent prompt and runner: **shortened-budget variant**, not the original600s baseline. Outer per-attempt inference wall cap120s, at most10 actions/3 repair groups. Startup and a5s finalization reserve come out of this cap; the saved pilot_budget.json gives each active agent budget. B makes exactly one direct LiteLLM completion call with a120s outer cap, no tools, tests or repairs. Both start cold and receive byte-identical initial problem/starter/interface text. A additionally has the existing visible checker and execution feedback. Private judging occurs only after inference terminates.",'',
        'Selection was frozen before sanity or benchmark inference: exclude all65 scored IDs, prefer unevaluated contests, distinct new contests, platform round robin within difficulty, then SHA256(`CSC2108-one-shot-pilot-v1:`+ID). Existing supported-interface/image exclusions apply; no private tests or solutions were inspected for selection. See [manifest](manifest.json).','',
        '| Problem | Difficulty | Prior contest fallback | A: agent | B: one-shot |','| --- | --- | --- | --- | --- |']
    for t in manifest['tasks']:
        a,b=find(t['task_id'],'A'),find(t['task_id'],'B')
        lines.append(f"| {t['task_id']} | {t['difficulty']} | {t['previous_contest_fallback']} | {a['official'] if a else 'unfinished'} | {b['official'] if b else 'unfinished'} |")
    lines+=['','| Condition | Correct / completed (6 planned) | Generated tokens captured | Additional uncaptured-token bound | Calls | Inference wall s | Judge wall s | Formatting errors | Missing | Public recoveries | Official failures with source |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for c,label in [('A','A: shortened mini-SWE'),('B','B: one-shot')]:
        t=total[c];lines.append(f"| {label} | {t['correct']}/{t['completed']} | {t['generation_tokens_observed']:,} | ≤{t['unobserved_tokens_upper']:,} | {t['model_calls']} | {t['inference_wall_seconds']:.1f} | {t['judge_wall_seconds']:.1f} | {t['format_errors']} | {t['missing_submission']} | {t['public_recovery']} | {t['official_failures']} |")
    lines+=['','Tokens are summed across **all** calls per attempt. If an HTTP reply is interrupted by the120s deadline, its exact token count is unavailable: captured counts are lower bounds and each missing reply adds at most4,096 tokens. No guessed token count is reported as measured. Inference wall includes interpreter/startup, model loading, generation, agent tools and finalization; independent judging is separately timed. Formatting counts are rejected agent replies versus one-shot extraction failures. One-shot has no public recovery by design.','']
    lines.append(f"Total wall including independent grading: **A {total['A']['inference_wall_seconds']+total['A']['judge_wall_seconds']:.1f}s; B {total['B']['inference_wall_seconds']+total['B']['judge_wall_seconds']:.1f}s**. Synthetic checks and supervisor overhead account for the rest of the experimental clock. Public recovery counts use the unchanged runner's recognized direct checks.")
    lines.append('')
    for name,keys in groups.items():lines.append(f"- **{name.replace('_',' ')}:** "+(', '.join(keys) or 'none'))
    lines+=['','## Failed agent trajectories','']
    for r in rows:
        if r['condition']!='A' or r['correct']:continue
        if r['missing_submission']:why='No candidate delivered; formatting/time/tool delivery failure, not an evaluated algorithm.'
        elif r['judge_resource_failure']=='memory_1g':why='The written candidate exceeded the unchanged 1 GB judge memory limit (owned Docker OOM evidence). This is a resource/performance failure as well as formatting/budget trouble; no public check ran.'
        elif '-2' in r['official_error_codes'].split(','):why='The official evaluator reports Wrong Answer. Visible checks also failed; the saved implementation was incorrect, alongside a length/format failure. Tools and repairs did not resolve it within this shortened budget.'
        elif r['public_pass']:why='A candidate passed visible checks but failed official tests: correctness/generalization failure remains.'
        else:why='A saved candidate failed official tests; no visible-test pass establishes correctness. Format/tool issues and incorrect implementation may coexist.'
        lines.append(f"- **{r['task_id']}:** {r['agent_or_generation_status']}; calls: {r['model_calls']}, actions: {r['actions']}, formatting errors: {r['format_errors']}, captured length-limited replies: {r['length_replies']}. {why}")
    net=len(groups['agent_only'])-len(groups['one_shot_only'])
    verdict=('The observed paired outcomes favor mini-SWE-agent' if net>0 else 'The observed paired outcomes favor one-shot generation' if net<0 else 'The observed paired outcomes show no correctness advantage for either condition')
    lines+=['','## Interpretation','',verdict+f" ({len(groups['agent_only'])} agent-only versus {len(groups['one_shot_only'])} one-shot-only successes). This is an exploratory directional observation, not a general effectiveness claim.",'',
        '**Only six problems and one seed per problem were used. Inference opportunities are unequal:** the agent may make multiple model calls, execute tests and repair; one-shot makes one call. The120s caps do not match generated tokens, prompts or inference compute. The system prompts also differ to request shell actions versus Python source. This pilot is **not a causal estimate under matched compute**, does not evaluate the full600-second agent baseline, and does not test unrestricted repository-level bug fixing. No settings were changed in response to outcomes.','',
        'Both conditions use the same existing official private-test evaluator and pinned Docker images. Generated code executes only in the existing isolated Docker agent/judge containers. One-shot extraction removes a single code fence (or accepts raw output); it never corrects or joins source. Model-authored candidates are never edited by Codex.','',
        'Full prompts, raw Ollama requests/responses, candidates, trajectories, exception provenance and official results: `E:\\CSC2108Local\\one-shot-ablation`. Code/source/image/package pins are in execution.json and frozen-source/. [Per-attempt metrics](metrics.csv), [aggregate results](results.json). Existing source trees and results are preserved. No push or merge.']
    recoveries=[r['task_id'] for r in rows if r['condition']=='A' and r['public_recovery']]
    if recoveries:
        lines.insert(lines.index('## Interpretation')+4,
            'Visible-test recovery occurred on '+', '.join(recoveries)+'. It produced no agent-only success here. These outcomes are already included above; they are not extra benchmark attempts.\n')
    text='\n'.join(lines)+'\n'
    # Prose spacing only; literal identifiers and URLs remain intact.
    import re
    parts=re.split(r'(`[^`]+`|https?://[^\s)]+)',text)
    for i in range(0,len(parts),2):
        value=parts[i]
        value=re.sub(r'\b(mini-SWE-agent|LiteLLM|Ollama|endpoint|context|output|seed|top-k|repeat penalty|repeat window|frequency|all|original|full|cap|most|at most|the|a)(?=\d)',r'\1 ',value)
        value=re.sub(r'(?<=\d)(?=(?:s|seconds?|tokens?|actions?|repair|GB)\b)',' ',value)
        value=value.replace('min-p0','min-p 0').replace('presence/frequency0','presence/frequency 0').replace('The120','The 120')
        parts[i]=value
    (ROOT/'REPORT.md').write_text(''.join(parts),encoding='utf-8')
    print(json.dumps({'totals':total,'groups':groups,'experimental_wall_seconds':status['experimental_wall_seconds']}))


if __name__=='__main__':main()
