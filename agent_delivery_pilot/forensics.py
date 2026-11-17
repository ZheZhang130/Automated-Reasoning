"""Phase 1: saved artifacts only; no model API calls, execution or private-test decoding."""
import hashlib
from pilot_common import ROOT,DATA,OLD,read,save,digest
from measure import delivery


def link(path,label):return '['+label+']('+str(path).replace('\\','/')+')'


def main():
    execution=read(OLD/'execution.json');evidence={};rows=[]
    for key in ('leetcode-3677','atcoder-abc390_d','atcoder-arc193_d'):
        a=OLD/'runs'/('osa-'+key+'-A');b=OLD/'runs'/('osa-'+key+'-B')
        m=delivery(a,execution);br=read(b/'ollama-responses.json')[0];bc=br['message']['content']
        assert all(x['prefix_before_fence_characters']==0 and x['thinking_field_characters']==0 for x in m['responses'])
        if key=='leetcode-3677':assert len({m['responses'][i]['content_sha256'] for i in (2,4,6,7)})==1
        m['one_shot']={'tokens':br['eval_count'],'done_reason':br['done_reason'],'fence_count':bc.count('```'),
                      'comment_lines':sum(x.lstrip().startswith('#') for x in bc.splitlines())}
        for folder in (a,b):
            for name in ('ollama-responses.json','ollama-requests.json','trajectory.json','result.json','solution.py','complete.json'):
                path=folder/name
                if path.exists():evidence[str(path)]=digest(path)
        m['source_files']={'agent_responses':str(a/'ollama-responses.json'),'agent_trajectory':str(a/'trajectory.json'),'one_shot_responses':str(b/'ollama-responses.json')}
        rows.append({'task_id':key,**m})
    save(ROOT/'forensics.json',{'phase':'before_new_inference','response_indices':'zero-based','tasks':rows,'original_artifact_sha256':evidence})
    save(DATA/'phase1/forensics.json',read(ROOT/'forensics.json'))
    lines=['# Phase 1 — saved-trajectory forensics (no new inference)','',
        'All response/message indices below are zero-based. This analysis used saved model output and public feedback only; no private test contents or official solutions were inspected. Timing is from the supervisor process start (including startup/cold loading) to the recorded tool observation, aligned using the saved wall/monotonic clock pair; values are approximate to 0.1 s. Tokens include rejected replies preceding the first action.','',
        '| Failed task | First response and truncation | First successful shell action | Public feedback / subsequent behavior |','| --- | --- | --- | --- |']
    descriptions={
        'leetcode-3677':'Reply[0] starts a literal-heredoc source write immediately; 156 Python-comment lines consume much of the 4,096-token reply. Only the opening command fence appears; no command executes.',
        'atcoder-abc390_d':'Replies[0,1] are 4,096-token incomplete source writes with 284/274 comment lines. Both lack closing fences and are rejected. Reply[2] finally delivers a complete write.',
        'atcoder-arc193_d':'Replies[0,1] each hit 4,096 tokens with 204/308 comment lines and no closing fence. Both are rejected. A third request times out; its exact output is unknown.'}
    behaviors={
        'leetcode-3677':'Replies[3,5] run recognized public tests and both fail. Replies[2,4,6,7] are byte-identical generated commands; executed rewrites[4,6] do not change the source. Zero recorded repairs is correct: there was no actual source change after failure. Reply[7] is generated but not executed before the deadline.',
        'atcoder-abc390_d':'Only one action executes: the write from reply[2]. Reply[3] requests the public checker but arrives too late to execute. No test feedback/recovery. The saved candidate was later independently recorded as exceeding 1 GB; delivery alone did not establish correctness.',
        'atcoder-arc193_d':'Zero actions, tests or repairs. No candidate exists; algorithmic correctness cannot be judged. The typed read-timeout sidecar distinguishes this from an unexplained infrastructure error.'}
    for row in rows:
        key=row['task_id'];a=OLD/'runs'/('osa-'+key+'-A');first=row['first_successful_action']
        timing=(f"{first['end_seconds']:.1f} s; {first['tokens_before_action']:,} tokens; response[{first['response_index']}], trajectory messages[{first['assistant_message_index']},{first['observation_message_index']}]" if first else 'None within the shortened budget; ≥8,192 captured tokens, one unanswered request (≤4,096 more).')
        refs=link(a/'ollama-responses.json','replies')+'; '+link(a/'trajectory.json','trajectory')
        lines.append(f"| {key} ({refs}) | {descriptions[key]} | {timing} | {behaviors[key]} |")
    lines+=['','## What the evidence supports','',
        '**Not an external pre-command preamble:** all first replies start with the command fence (prefix length zero), and the dedicated thinking field is empty. The excess reasoning appears as long planning/reconsideration comments *inside the proposed Python source*. The command is not executable until both heredoc and fence close. All five captured format errors in these failures align with full 4,096-token output caps, not an identified parser bug or context cutoff.','',
        '**Mixed causes:** `leetcode-3677` combines about 48 s lost on the first unexecutable draft, a later incorrect implementation, and repeated unchanged rewrites despite recognized feedback. `abc390_d` spends almost the whole budget reaching its first write and never executes its generated test command; its eventual resource failure also needs a better implementation. `arc193_d` never reaches execution at all.','',
        'The single one-shot reply on `leetcode-3677` is a closed 929-token solution (28 comment lines), versus the agent first reply’s 4,096 tokens/156 comment lines and missing fence. This establishes that a compact deliverable was possible in that condition; no one-shot source or algorithm is supplied to the new agent. On `abc390_d` and `arc193_d`, one-shot also hits 4,096 tokens with unclosed output (219/198 comment lines), so the verbosity problem is not unique to the agent interface. The paired one-shot files are linked below.','']
    for row in rows:lines.append('- '+row['task_id']+': '+link(row['source_files']['one_shot_responses'],'one-shot replies[0]'))
    lines+=['','## Would 600 seconds help?','',
        'Possibly, but not demonstrated. On `leetcode-3677`, more time permits more feedback/edits, yet the existing identical-rewrite loop gives no evidence it would repair itself. On `abc390_d`, more time could permit actual visible testing and repairs after the late write; it does not automatically fix the resource-heavy program. On `arc193_d`, more time could complete the third reply, but the same 4,096-token cap and three-consecutive-format-error guard remain. No 600-second run is performed or inferred as a success.','',
        '## Single intervention selected before validation','',
        'Replace only the agent **system prompt** with a shorter delivery-focused instruction: compact executable source, no planning/alternative/commentary blocks, one fully closed shell action, then the existing write → visible test → changed repair → submit workflow. This tests the prompt replacement as one unit; individual wording effects are not isolated. Keep sampler/thinking/context/output caps, parser, malformed-command rejection, workspace, tools, visible feedback, repair accounting, evaluator and budgets unchanged. There is no evidence here requiring a parser/accounting fix. No algorithm-specific instructions or one-shot solutions are added.']
    (ROOT/'FORENSICS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print([{'task':r['task_id'],'first_successful_action':r['first_successful_action']} for r in rows])


if __name__=='__main__':main()
