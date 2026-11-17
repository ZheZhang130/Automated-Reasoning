"""Analyze the fixed four-task validation without generating or correcting solutions."""
import csv
import statistics
from pilot_common import ROOT,DATA,A2_PROFILE,read,save,digest,old_module
from measure import delivery


def main():
    manifest=read(DATA/'manifest.json');execution=read(DATA/'execution.json');status=read(DATA/'status.json')
    previous=old_module('report');previous.DATA=DATA
    rows=[];details={}
    for task in manifest['tasks']:
        for condition in ('A','A2','B'):
            row=previous.collect(task,condition)
            if row is None:continue
            folder=DATA/'runs'/('osa-'+task['task_id']+'-'+condition)
            timing=delivery(folder,execution);details[task['task_id']+'-'+condition]=timing
            first=timing['first_executable_action'];success=timing['first_successful_action']
            row.update(first_action_seconds=first['end_seconds'] if first else None,
                tokens_to_first_action=first['tokens_before_action'] if first else None,
                first_successful_action_seconds=success['end_seconds'] if success else None,
                first_reply_tokens=timing['responses'][0]['tokens'] if timing['responses'] else None,
                first_reply_comment_lines=timing['responses'][0]['comment_lines'] if timing['responses'] else None)
            rows.append(row)
    totals={}
    for c in ('A','A2','B'):
        group=[r for r in rows if r['condition']==c];first=[r['first_action_seconds'] for r in group if r['first_action_seconds'] is not None]
        totals[c]={'completed':len(group),'correct':sum(r['correct'] for r in group),
            **{k:sum(r[k] for r in group) for k in ('generation_tokens_observed','unobserved_tokens_upper','model_calls','inference_wall_seconds','judge_wall_seconds','format_errors','missing_submission','length_replies','public_recovery')},
            'first_actions_delivered':len(first),'median_seconds_to_first_action':statistics.median(first) if first else None}
    result={'status':status,'totals':totals,'rows':rows,'delivery':details,'analysis_source_sha256':digest(__file__),
            'single_intervention':'A2 prompt replacement only; no inference parameters or execution policies changed'}
    save(ROOT/'results.json',result);save(DATA/'summary.json',result)
    with (ROOT/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['task_id']);w.writeheader();w.writerows(rows)
    def row(key,c):return next((r for r in rows if r['task_id']==key and r['condition']==c),None)
    lines=['# mini-SWE-agent delivery-prompt diagnostic','',
        f"Experimental execution: **{status['status']}, {status['experimental_wall_seconds']:.1f} / 2,100 seconds**, including CPU controls, both A2 synthetic fixtures, all inference, official judging and cleanup. No repeated benchmark attempts or post-validation tuning.",'',
        '[Phase 1 failure analysis and source citations](FORENSICS.md) was completed before new inference. The old first replies started immediately with a source-writing command, but long planning comments prevented closing the command before the 4,096-token cap. On leetcode-3677, public failures were recognized and subsequent writes were byte-identical; this was not a repair-counter bug.','',
        f"**One intervention:** A2 (`{A2_PROFILE}`) replaces only the system prompt with shorter delivery-focused instructions: compact source without planning commentary, one closed command, then write → visible test → changed repair → submit. Genuine mini-SWE-agent, persistent workspace, parser, strict rejection of malformed commands, feedback, repair accounting and sandbox are unchanged. The prompt is tested as a unit, not as separate independently identified wording effects.",'',
        'All conditions: local qwen3.5:9b Q4_K_M; nonthinking; 16,384 context; 4,096 output tokens; T=0.2, top-p=0.9, top-k=40, min-p=0, repeat penalty=1/window64, presence/frequency=0; seed2108; endpoint127.0.0.1:11435. A/A2 have the same 120-second outer cap, 10 actions, 3 repair groups and five-second finalization reserve. B is the unchanged original one-shot protocol with one call and no feedback. Both agent conditions are shortened-budget variants, not the 600-second baseline. Model/image/source/package pins and protocol hashes are retained.','',
        'Four fresh tasks were deterministically selected before inference: one easy and three medium, excluding all 71 prior IDs. Rank by prior-contest avoidance, within-pilot contest reuse, platform balance, then salted SHA256 (`CSC2108-delivery-pilot-v1:`+ID). Only metadata/public-interface eligibility was examined. [Manifest](manifest.json); [future exclusion union](future_exclusions.json).','',
        '| Task | Difficulty | A original agent | A2 shorter prompt | B original one-shot |','| --- | --- | --- | --- | --- |']
    for task in manifest['tasks']:
        values=[row(task['task_id'],c) for c in ('A','A2','B')]
        lines.append('| '+task['task_id']+' | '+task['difficulty']+' | '+' | '.join(x['official'] if x else 'unfinished' for x in values)+' |')
    lines+=['','| Condition | Correct/completed (4 planned) | Captured output tokens | Uncaptured upper bound | Calls | Inference wall s | Judge wall s | Format errors | Length replies | Missing | Public recoveries |',
            '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for c,t in totals.items():
        lines.append(f"| {c} | {t['correct']}/{t['completed']} | {t['generation_tokens_observed']:,} | ≤{t['unobserved_tokens_upper']:,} | {t['model_calls']} | {t['inference_wall_seconds']:.1f} | {t['judge_wall_seconds']:.1f} | {t['format_errors']} | {t['length_replies']} | {t['missing_submission']} | {t['public_recovery']} |")
    lines+=['','Captured token totals include every returned reply; interrupted replies have explicitly unknown counts bounded by 4,096 each. No missing telemetry is treated as zero actual work. Inference wall includes cold loading, startup, tools and finalization; grading is separately timed. Formatting counts mean rejected agent replies or one-shot extraction failures. Public recovery uses the original recognized checker accounting.','',
        '## Time and tokens to first executable action','',
        '| Task | A seconds / cumulative tokens | A2 seconds / cumulative tokens |','| --- | ---: | ---: |']
    for task in manifest['tasks']:
        values=[]
        for c in ('A','A2'):
            r=row(task['task_id'],c)
            values.append(f"{r['first_action_seconds']:.1f} / {r['tokens_to_first_action']:,}" if r and r['first_action_seconds'] is not None else 'not delivered')
        lines.append('| '+task['task_id']+' | '+' | '.join(values)+' |')
    lines+=['','Times are approximate supervisor-start-to-tool-observation timestamps; cumulative tokens include previously rejected replies. Individual successful-action times, first-response comment counts, response indices and trajectory message indices are in results.json. B has no actions by design.','',
        '## Outcome and mechanism inspection','']
    changes=[]
    for task in manifest['tasks']:
        a,a2,b=[row(task['task_id'],c) for c in ('A','A2','B')]
        if not a or not a2:continue
        changed=a['correct']!=a2['correct'];changes.append((task['task_id'],changed))
        da=details[task['task_id']+'-A'];d2=details[task['task_id']+'-A2']
        lines.append(f"- **{task['task_id']}** ({'changed official outcome' if changed else 'same official outcome'}): A/A2 first-reply comment lines {a['first_reply_comment_lines']}/{a2['first_reply_comment_lines']}; formatting rejections {a['format_errors']}/{a2['format_errors']}; recognized recoveries {a['public_recovery']}/{a2['public_recovery']}. A: {a['official']} ({a['agent_or_generation_status']}); A2: {a2['official']} ({a2['agent_or_generation_status']}). See [A replies]({a['artifact'].replace(chr(92),'/')}/ollama-responses.json), [A2 replies]({a2['artifact'].replace(chr(92),'/')}/ollama-responses.json) and their adjacent trajectory.json files; exact action/response mapping is in results.json.")
    net=totals['A2']['correct']-totals['A']['correct']
    lines+=['',f"A2 minus A: **{net:+d} correct**. This is a diagnostic observation on four tasks, not a statistically definitive result. Delivery improvements are not automatically implementation or algorithm improvements; official correctness, public feedback/recovery, and the saved trajectories must support those stronger claims separately. The original one-shot condition remains a comparator, not a source of agent solutions.",'',
        'No private cases or official solutions were used to construct the prompt. No one-shot-generated program was placed in an agent prompt or workspace. No weights, quantization, thinking, sampler, context/output caps or security settings changed. The source was never auto-repaired and malformed commands were never executed. Tests use only existing synthetic fixtures before the frozen validation.','',
        'All original source/results and directories are preserved. Raw artifacts: `E:\\CSC2108Local\\agent-delivery-pilot`. Future experiments must exclude the recorded 75-ID union; these four tasks will not be used for another tuning iteration. No push or merge.']
    (ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print({'totals':totals,'experimental_wall_seconds':status['experimental_wall_seconds']})


if __name__=='__main__':main()
