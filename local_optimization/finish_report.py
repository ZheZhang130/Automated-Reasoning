"""Publish aggregate-only study artifacts after the frozen validation finishes."""
import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from optlib import DATA, MODEL, MODEL_DIGEST, REPO, ROOT, digest, read, save

CONTROL='heredoc-v6-16k-common'
CHALLENGER='heredoc-opt-16k-4k-p15-r1024'


def number(value):return f'{value:,.1f}'


def readable_prose(text):
    # Keep identifiers, URLs, versions and literal paths intact.
    pieces=re.split(r'(`[^`]+`|https?://[^\s)]+)',text)
    for index in range(0,len(pieces),2):
        value=pieces[index]
        value=re.sub(r'\b(all|on|of|after|at|from|versus|over|under|than|with|before|prior|original|held-out|seeds|control|thinking|native|window|presence|output|easy|medium|hard|Qwen|Coder)(?=\d)',r'\1 ',value)
        value=re.sub(r'(?<=\d)(?=(?:seconds?|tokens?|hours?|actions?|problems?|tasks?|attempts?|MiB|GB|CPU|PIDs|passes|easy|medium|hard|million|word|second|output|context|bytes?|seconds|token|v?2\.4\.6)\b)',' ',value)
        value=re.sub(r'\b(RTX|SUPER|Pydantic|LiteLLM|Ollama|Python|mini-SWE-agent)(?=\d)',r'\1 ',value)
        pieces[index]=value
    return ''.join(pieces)


def table(summary):
    lines=['| Configuration | Passes | Agent seconds | Full wall seconds | Output tokens | Format errors |',
           '| --- | ---: | ---: | ---: | ---: | ---: |']
    for name,p in summary['profiles'].items():
        t=p['totals'];unknown=p['output_tokens_unobserved_upper_bound']
        tokens=f"{t['output_tokens']:,}"+(f" + ≤{unknown:,} unobserved" if unknown else '')
        wall=number(p['invocation_wall_total']) if p['invocation_wall_observations']==p['n'] else 'unavailable'
        lines.append(f"| `{name}` | {p['passed']}/{p['n']} | {number(t['seconds'])} | {wall} | {tokens} | {t['format_errors']} |")
    return '\n'.join(lines)


def main():
    summaries={}
    for folder in sorted((DATA/'batches').iterdir()):
        if not (folder/'plan.json').exists():continue
        subprocess.run([sys.executable,str(ROOT/'analyze.py'),str(folder)],check=True)
        summaries[folder.name]=read(folder/'analysis.json')
    for name in ('selection-four-s2108','selection-repeated'):
        folder=DATA/'analysis'/name
        subprocess.run([sys.executable,str(ROOT/'analyze.py'),str(folder)],check=True)
        summaries[name]=read(folder/'analysis.json')
    held=summaries['heldout-final'];repeated=summaries['selection-repeated']
    if held['completed']!=80 or repeated['completed']!=48:
        raise RuntimeError('Required paired validation/repetition is incomplete')
    selection=read(ROOT/'final_selection.json')
    a,b=held['profiles'][CONTROL],held['profiles'][CHALLENGER]
    pair=next(p for p in held['paired'] if p['a']==CONTROL and p['b']==CHALLENGER)
    lower=pair['problem_bootstrap_95'][0]
    wall_ratio=b['invocation_wall_total']/a['invocation_wall_total']
    token_ratio=(b['totals']['output_tokens']+b['output_tokens_unobserved_upper_bound'])/a['totals']['output_tokens']
    missing_a=a['official_statuses'].get('missing_submission',0)
    missing_b=b['official_statuses'].get('missing_submission',0)
    promote=(lower>0 and b['passed']>a['passed'] and wall_ratio<=1.5 and token_ratio<=1.5 and missing_b<=missing_a)
    recommended=CHALLENGER if promote else CONTROL
    recommendation={'selection_sha256':digest(ROOT/'final_selection.json'),'recommended_profile':recommended,
        'configuration':selection['frozen_configurations'][recommended],
        'challenger_promoted':promote,'heldout_paired':pair,'wall_ratio':wall_ratio,'token_ratio_upper':token_ratio,
        'policy':'Confirm a positive paired problem-bootstrap lower bound, more passes, <=1.5x wall/tokens, and no more missing submissions; otherwise retain original control.',
        'high_reasoning_alternative':None,'validation_plan_sha256':digest(DATA/'batches/heldout-final/plan.json')}
    save(ROOT/'final_recommendation.json',recommendation)
    for name,summary in summaries.items():save(ROOT/'results'/(name+'.json'),summary)
    for name,folder in [('heldout-final',DATA/'batches/heldout-final'),('selection-repeated',DATA/'analysis/selection-repeated')]:
        shutil.copyfile(folder/'metrics.csv',ROOT/'results'/(name+'.csv'))
    inventory=[]
    for name,s in summaries.items():
        if name in ('selection-four-s2108','selection-repeated'):continue
        inventory.append({'batch':name,'completed':s['completed'],'planned':s['planned'],
            'intentionally_unstarted':s['planned']-s['completed'],
            'plan_sha256':digest(DATA/'batches'/name/'plan.json'),'analysis_sha256':digest(DATA/'batches'/name/'analysis.json')})
    save(ROOT/'results/experiment_inventory.json',inventory)
    charged_tokens=charged_nanoseconds=0
    for result_path in DATA.rglob('result.json'):
        result=read(result_path);inf=result.get('inference',{})
        charged_tokens+=inf.get('eval_count',0)+result.get('unobserved_output_token_upper_bound',0)
        charged_nanoseconds+=sum(inf.get(k,0) for k in ('eval_duration','prompt_eval_duration','load_duration'))
        charged_nanoseconds+=result.get('unobserved_model_calls',0)*result.get('profile_config',{}).get('query_seconds',180)*1e9
    compute={'conservatively_charged_output_tokens':charged_tokens,'conservatively_charged_inference_hours':charged_nanoseconds/3.6e12,
             'ceiling_output_tokens':3000000,'ceiling_inference_hours':10,'includes':'all recorded diagnostics/development/selection/repetition/validation attempts, including explicit missing-reply upper bounds'}
    save(ROOT/'results/compute_budget.json',compute)
    plan=read(DATA/'batches/heldout-final/plan.json')
    provenance={k:plan[k] for k in ('git_commit','python','packages','all_packages','ollama','gpu_hardware',
        'model_digest','images','evaluator_revision','manifest_sha256','installed_ollama_adapter_sha256')}
    provenance['dataset']={k:plan['manifest'][k] for k in ('dataset','revision','source_sha256','evaluator_revision')}
    save(ROOT/'results/provenance.json',provenance)
    log=subprocess.check_output(['git','log','--reverse','--format=%h %s','d0fb8756a54e7d7fb1f136b6a5de4a2257b3a4b9..HEAD'],cwd=REPO,text=True)
    (ROOT/'results/commits-before-report.txt').write_text(log,encoding='utf-8')
    development='\n\n'.join('### '+name+'\n\n'+table(s) for name,s in summaries.items() if name.startswith('dev-'))
    batch_lines='\n'.join(f"| `{x['batch']}` | {x['completed']}/{x['planned']} | {x['intentionally_unstarted']} |" for x in inventory)
    reliability=[];distributions=[]
    for profile,p in held['profiles'].items():
        t=p['totals'];failed=p['failed_cost'];success=p['successful_seconds'];failure=p['failed_seconds']
        distributions.append(f"| `{profile}` | {number(success['median'])} / {number(success['p90'])} | {number(failure['median'])} / {number(failure['p90'])} | {number(p['invocation_wall_seconds']['median'])} / {number(p['invocation_wall_seconds']['p90'])} |")
        reliability.append(f"| `{profile}` | {t['model_calls']} / {t['actions']} | {t['format_errors']} | {p['official_statuses'].get('missing_submission',0)} | {t['public_recovery']} / {t['recovery_official_pass']} | {t['public_pass_official_fail']} | {failed['output_tokens']:,} ({100*failed['output_tokens']/t['output_tokens']:.1f}%) |")
    efficiency=[]
    for profile,p in held['profiles'].items():
        t=p['totals']
        efficiency.append(f"| `{profile}` | {t['prompt_tokens']:,} | {number(t['generation_seconds'])} | {number(t['prefill_seconds'])} | {number(t['load_seconds'])} | {number(p['observed_generation_tokens_per_second'])} | {p['offloaded_runs']}/{p['n']} |")
    ci=pair['problem_bootstrap_95']
    decision=('The challenger meets the preregistered confirmation rule and becomes the practical default.' if promote else
        'The challenger does not meet the preregistered confirmation rule. Retain the simpler original control as the practical default; no accuracy improvement is claimed.')
    text=f'''# Qwen3.5 9B local coding-agent optimization

Completed on 2026-11-17. **Recommended default: `{recommended}`.** {decision} All inference was local, all benchmark candidates were authored by Qwen, and official hidden outcomes were never returned to the agent. No frontier integration, model download, push or merge was performed.

## Final result

The fixed held-out evaluation contains 20 fresh problems and two seeds (2108/2109), 40 attempts per arm. The challenger changes presence penalty from 0 to 1.5 and its effective repetition window from 64 to 1024, retaining the original text protocol, nonthinking mode, 16K context, 4K output, T=.2, top_p=.9 and top_k=40. It also uses the documented checker-redirection accounting fix in the new runtime. This is an explicitly tested combined configuration, not an isolated causal estimate of either sampler change.

{table(held)}

Challenger minus control: **{100*pair['problem_mean_accuracy_difference']:+.1f} percentage points**, descriptive 95% problem-cluster bootstrap interval **[{100*ci[0]:+.1f}, {100*ci[1]:+.1f}]**; control-only passes {pair['a_only_pass']}, challenger-only passes {pair['b_only_pass']}. Runtime ratio {wall_ratio:.3f}; output-token ratio upper bound {token_ratio:.3f}. Repetitions from the same problem remain together in 10,000 bootstrap resamples, RNG seed2108. These are small-sample descriptive intervals, not proof of equivalence or general superiority. Held-out outcomes were used only for the frozen confirmation/fallback rule, never for further tuning.

![Held-out accuracy/cost](figures/heldout-final-pareto.png)

## Original baseline and observed limitations

The prior frozen evaluation reported Qwen3.5 9B 23/48 (47.9%), Qwen2.5-Coder14B 18/48 and7B 15/48 on24 problems/two attempts. Only Qwen3.5 9B was used in this new study. Its prior breakdown was easy14/16, medium9/20, hard0/12. Prior performance must not be compared as a causal before/after percentage against the new, different task set.

The original control uses mini-SWE-agent2.4.6 → LiteLLM1.81.16 → project Ollama0.40.16 at127.0.0.1:11435 → Qwen3.5:9b Q4_K_M. It permits20 actions, three recognized public-failure repair groups,600 seconds per task and180 seconds per request. It executes the original archived `local_eval_v2/runtime.py`; all old source files and frozen results remain untouched.

Auditing all48 prior Qwen9 attempts found56 format errors, all on length-limited replies with an unclosed command fence. Exact boundary reconstruction separates **50 output-cap events from six context-cap events**; treating all as 4K output truncations would be incorrect. Twenty runs had format errors,14 terminated with repeated-format failure and12 executed no actions. Eight lacked a submission and four retained an unchanged starter. Six candidates passed public examples but failed official tests. Public recovery produced only one official success. Failed attempts consumed288,284/299,459 generated tokens (96.3%) and most of3,727.5 agent seconds. These observations distinguish interface/capacity failures from incorrect algorithms.

Repeated identical-source public tests occurred only five times. None of29 runs ever passing public examples modified source after its first pass;30 subsequent actions were mostly submission. This did not justify checkpointing, automatic acceptance of public tests, more actions, history summarization or a larger rewrite. They were not silently added.

## Methodology and isolation

The frozen dataset uses LiveCodeBench v6 Jan–Apr2025, cached source SHA256 `{plan['manifest']['source_sha256']}`, revision `{plan['manifest']['revision']}`. Development6 (2easy/2medium/2hard), selection12 (4/4/4), held-out20 (6/8/6) were selected before new inference by deterministic hash ordering and platform balancing. All splits exclude all27 previously scored IDs; splits have disjoint contests, at most two tasks per contest, and held-out excludes prior primary-evaluation contests. Existing interface eligibility excludes custom-node functional interfaces and image statements. Manifests contain exact hashes and exclusions. Task outcomes did not select the held-out sample.

Each batch freezes source bytes, exact profiles, software packages, weights digest, dataset hashes, Docker image IDs and evaluator revision. Execution uses archived code, rotates arm order and interleaves difficulty; GPU runs are sequential under the shared lock. Captured HTTP requests verify all sampler/thinking/model settings. Raw requests, responses, trajectories, public events, GPU samples, candidates and independent judge attempts remain on E:. Stopped arms keep every measured attempt and explicitly unstarted slots. Defined but unexecuted profiles in the catalog are not counted as experiments.

Agent containers use network:none, read-only root, nonroot65534,512MB memory/no extra swap,1CPU,64PIDs, all capabilities dropped, no-new-privileges and capped tmpfs. They mount only the trusted public bundle. Private cases are supplied only to the separate official judge (1GB/1CPU,6seconds per test,175second container guard/180second host timeout). Source extraction is byte-based with size/symlink guards; candidate code never executes on the Windows host. Only owned containers are cleaned; unrelated Docker/Ollama workloads are preserved.

## Engineering findings

**Native history:** the installed LiteLLM serializer omits native assistant tool calls and tool-result names. A mocked real HTTP transport test reproduces it. The versioned override in `transport.py` preserves assistant calls, arguments, linked results and reasoning without modifying installed packages, following [Ollama's protocol](https://docs.ollama.com/capabilities/tool-calling). Two synthetic fixtures reduce actions9→5 and15→8, output679→297 and910→450, all passing. Those are mechanism checks, not benchmark gains. Corrected native tools did not earn a default recommendation.

**Public-test accounting:** direct checker commands ending in `2>&1` are recognized in the new runtime; compound commands or pipelines masking exit status are not. Historical posthoc recognition is exported separately and does not rewrite original repair accounting. Public passes still do not establish private correctness.

**Timeouts:** LiteLLM can wrap httpx read timeouts as APIConnectionError. Typed cause/context traversal distinguishes timeout from connection refusal. Missing replies retain unknown token/duration bounds, conservatively charged at caps. An early raw InfrastructureError remains unchanged with a hash-linked timeout assessment rather than an invented complete response.

**Judge resource failures:** an official evaluator error was traced to an owned worker OOM under1GB. `judge_watch.py` preserves the raw official result and owned Docker OOM event, and classifies a confirmed resource violation as zero-pass candidate failure. A known Qwen toy and deliberate OOM fixture validate this. An older plan pins an explicit bookkeeping addendum; no candidate was edited and no inference repeated. Unknown infrastructure errors stop the batch.

**Long commands:** a227,558-byte generic fixture reproduced WinError206 in Windows argv delivery. Optional binary-stdin transport preserves UTF8 bytes/SHA256, quoting and closed candidate stdin within the same sandbox; both final output-probe arms share it. It does not edit generated source. Short-output/default arms retain their original transport. The fixture is a transport test, never a benchmark solution.

## Adaptive development experiments

These small experiments use different development subsets; their success fractions are not pooled into a head-to-head leaderboard. All successes use the official evaluator. Output includes thinking. Unknown timeout work is marked explicitly.

{development}

The first paired protocol screen found native nonthinking2/3 versus control2/3 at roughly twice the time; native thinking4K fell to1/3 and failed to deliver actions on medium/hard. Simply raising output to32K prolonged repetition or timeouts. Presence1.5 helped one development case, but default window64 limited its reach. Window1024 shortened a hard nonthinking failure from134.4seconds/12,288tokens/no candidate to51.3seconds/3,985tokens/a wrong candidate. That fixes delivery, not hidden correctness.

The documented vendor thinking preset with window1024 solved one development medium at305.7seconds/26,233tokens after window64 failed at602seconds; it was too expensive and did not generalize in selection. A vendor nonthinking preset (T1/top_p1/top_k40/presence2/window1024) won2/2 development cases over0/2 for the current sampler, then lost that advantage on fresh selection. These reversals justify separate development and selection sets.

A native context16K→32K trial removed four real context cutoffs (generations1098/199/161/123 tokens each exactly filling16,384 combined tokens), reached over18K prompt tokens and20 actions, but remained incorrect. Capacity and reasoning are separate limitations. The final output-only probe fixes64K context and480second request/600second task budgets across4K/32K outputs; its exact measured outcomes appear below. No further parameter/prompt exploration followed it.

{table(summaries['selection-final-output-probe'])}

The [Qwen model card](https://huggingface.co/Qwen/Qwen3.5-9B) motivated thinking and sampling hypotheses, including32K output. Recommendations were tested rather than assumed optimal. Presence is affected by its effective token window, as exposed by [Ollama's options](https://docs.ollama.com/modelfile) and [llama.cpp's sampler construction](https://github.com/ggml-org/llama.cpp/blob/master/common/sampling.cpp). A historical37-attempt match found equal23 passes under two older samplers, with three unique passes each; other provenance differences make that exploratory only.

## Fresh configuration selection and repeat

On the identical12 tasks/seed2108, the four completed short-output arms give:

{table(summaries['selection-four-s2108'])}

Presence-only, its tag-default counterpart and expensive thinking stopped after a balanced six-task prefix;18 original-plan jobs remain explicitly unstarted. All six output-message sequences under presence-only/tag match, so rerunning their remaining cases offered little information. Costly thinking had1/6 versus control1/6 at over twice the time. Larger-context vendor nonthinking did not improve correctness.

The control and best practical challenger were repeated on the same12 tasks with seed2109. Combined seed2108/2109 results:

{table(repeated)}

Selection Pareto frontier (accuracy, full wall and output tokens): {', '.join('`'+p+'`' for p in repeated['descriptive_three_metric_frontier'])}. This is descriptive point dominance on identical coverage, not a significance claim. Full selection evidence was frozen before validation. No more expensive high-reasoning default is justified by the measured selection tradeoffs.

The seed2109 comparison itself is preserved separately:

{table(summaries['selection-repeat-s2109'])}

![Repeated selection comparison](figures/selection-repeated-pareto.png)

## Held-out efficiency, reliability and recovery

| Configuration | Prompt tokens | Generation seconds | Prefill seconds | Load seconds | Generated tokens/s | Offloaded runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(efficiency)}

| Configuration | Successful agent median / p90 s | Failed agent median / p90 s | Full-wall median / p90 s |
| --- | ---: | ---: | ---: |
{chr(10).join(distributions)}

Agent elapsed covers preflight/cold loading/container setup through termination, excluding extraction/cleanup/judge. Full wall additionally includes interpreter startup, extraction, cleanup and telemetry; private judging stays separate. CSV/JSON retain min/p25/median/p75/p90/max and individual attempts, not just means. Prefill/load/generation come from actual completed Ollama responses; timeout totals explicitly expose missing work.

| Configuration | Model calls / actions | Format errors | Missing | Public recovery / official success after failure | Public pass, official fail | Output spent on failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(reliability)}

These results distinguish better delivery from stronger algorithmic reasoning. Fewer format errors or more submitted candidates alone do not establish correctness. Public recovery counts recognized direct checks, with historical posthoc events separately identified. Wrong candidates can pass examples; additional actions can spend substantial work without improving official outcomes. Full normalized metrics retain termination reasons, output/context boundary counts, unchanged starters and resource failures.

![Held-out runtime distributions](figures/heldout-final-runtime.png)

Held-out descriptive Pareto frontier: {', '.join('`'+p+'`' for p in held['descriptive_three_metric_frontier'])}. Dominance requires identical task/seed coverage and a dominating arm's token upper bound no greater than the other's observed lower bound. No arbitrary composite score was used.

## GPU, storage and inference behavior

RTX4080SUPER16,376MiB, driver610.88. Small-prompt allocation probes measured32K6.718GB,64K7.683GB and128K9.897GB model allocations, fully resident on GPU. The128K probe used13,262MiB total including desktop/background. Allocation feasibility is not evidence of long-prefill throughput or an accuracy advantage. Sustained captured generation was typically90–105tokens/s; exact final-arm rates appear above. GPU samples include unrelated desktop allocations, so are not process-exclusive memory measurements.

Every benchmark intentionally cold-loads the project model for consistency. Loads normally take3.2–3.5seconds; the first diagnostic20.6second outlier is retained. Keeping a model warm could help deployment latency, but no unmeasured warm-start saving is credited. Weights stay in `E:\\OllamaModels`, raw artifacts in `E:\\CSC2108Local\\optimization`, Docker in `E:\\DockerDesktop`; no new model was downloaded. Ollama Desktop11434 is distinct from the project11435 server, and foreign loaded models halt new runs.

## Reproduction and exact provenance

See [README](README.md), [frozen selection](final_selection.json), [recommendation](final_recommendation.json), [profiles](profiles.json), and [full machine/package/image provenance](results/provenance.json). Python3.11.9; mini-SWE-agent2.4.6; LiteLLM1.81.16; Pydantic2.12.5; Ollama0.40.16. Model `{MODEL}`, Q4_K_M digest `{MODEL_DIGEST}`. Official LiveCodeBench evaluator `{plan['evaluator_revision']}`. Docker image IDs, installed adapter hash and all package versions are machine-readable. Native DLL pins remain intact; plotting packages are isolated under E: and do not modify inference dependencies.

From `local_optimization` in PowerShell, dot-source `..\\local_baseline\\env.ps1`, use `E:\\CSC2108Local\\.venv\\Scripts\\python.exe`, then `selected.py --task <trusted-public-bundle> --output <fresh-E-directory> --seed 2108`. `--challenger` explicitly selects the evaluated alternative. The entrypoint checks the selection/recommendation linkage, exact profile and source hashes; its default follows the frozen confirmation rule.

`batch.py --batch E:\\CSC2108Local\\optimization\\batches\\heldout-final --resume` skips completed inference/judging. `analyze.py`, `verify.py`, `cohort.py`, `plot.py` and `finish_report.py` regenerate aggregate artifacts without solving tasks or editing candidates. Repeating the study from scratch requires new E: experiment directories with the committed manifests, source/cache/image pins and identical seeds/constraints. Never overwrite frozen batches or use judged tasks as fresh held-out data.

## Experiment inventory and remaining limits

| Frozen batch | Completed / planned | Intentionally unstarted |
| --- | ---: | ---: |
{batch_lines}

Total conservative inference charge is {compute['conservatively_charged_inference_hours']:.3f} hours and {charged_tokens:,} output tokens, under the initial10-hour/3-million-token ceiling. This includes diagnostics and failed/missing-reply upper bounds; it is not presented as fully observed generation. Discovery stopped after3.396 charged hours, reserving compute for repetition and independent validation.

Complete trajectories, failed attempts and independent judge evidence remain on E:. Aggregate-only JSON/CSV and PNG/SVG/PDF charts are versioned here. [Experiment hashes](results/experiment_inventory.json) identify frozen plans and analyses. [Commit inventory before this final report](results/commits-before-report.txt) records scoped progress; `git log --reverse d0fb8756..HEAD` also includes the final report commit. All changed project files are confined to `local_optimization/`; no baseline/eval-v2 files were changed. Branch: `feat/csc2108-qwen-local-optimization`. Nothing was pushed or merged.

The authorized study stages are complete. Remaining research questions include larger independent validation, model/dataset training contamination, sensitivity to seeds/contest mix, longer-input throughput, warm-start deployment latency and stronger algorithmic reasoning without excessive inference. Small samples, adaptive selection, one quantization/hardware combination and desktop/container noise limit generalization. Held-out20 problems improve separation of tuning and validation but do not establish a population-wide model ranking. No new configuration may be tuned on these held-out outcomes; any follow-up needs fresh tasks. No expensive high-reasoning alternative is recommended from this evidence.
'''
    (ROOT/'REPORT.md').write_text(readable_prose(text),encoding='utf-8')
    print(json.dumps({'recommended':recommended,'heldout_control':a['passed'],'heldout_challenger':b['passed'],
                      'attempts_per_arm':a['n'],'paired_difference_interval':ci,'measured_new_attempts':sum(x['completed'] for x in inventory)}))


if __name__=='__main__':main()
