"""Metadata-only delivery/feedback measurements; never repairs generated code."""
import datetime
import hashlib
import json
import re
from pilot_common import read


def visible_feedback(result):
    """Posthoc only: distinguish genuine compound checker calls from budget recognition."""
    checks=[];last_hash=None;failed_hash=None;repairing=False;repairs=0;ambiguous=False
    for event in result.get('events',[]):
        source=event.get('source_sha256',last_hash)
        if failed_hash is not None and source!=last_hash and not repairing:
            repairs+=1;repairing=True
        actual_checker=bool(re.search(r'^[ \t]*python(?:3)?[ \t]+(?:-I[ \t]+)?/public/check\.py(?:[ \t]+2>&1)?[ \t]*$',event.get('command',''),re.M))
        values=[]
        if actual_checker:
            for line in event.get('output','').splitlines():
                if line.startswith('CSC2108_PUBLIC_RESULT='):
                    try:values.append(json.loads(line.split('=',1)[1]))
                    except ValueError:pass
        if not values and event.get('recognized_public_test'):
            values=[{'status':'pass' if event['returncode']==0 else 'candidate_failure'}]
        ambiguous|=len(values)>1
        for value in values:
            success=value.get('status')=='pass'
            checks.append({'action':event['action'],'pass':success,'source_sha256':source,
                           'recognized_by_budget':bool(event.get('recognized_public_test'))})
            if source!=failed_hash:repairing=False
            failed_hash=None if success else source
        last_hash=source
    failed=False;recovered=False
    for check in checks:
        if not check['pass']:failed=True
        elif failed:recovered=True
    return {'checks':checks,'public_recovery':recovered,'unrecognized_checks':sum(not x['recognized_by_budget'] for x in checks),
            'reconstructed_changed_repair_groups':repairs,'multiple_checks_in_one_action':ambiguous}


def delivery(folder,execution):
    raw=read(folder/'ollama-responses.json') if (folder/'ollama-responses.json').exists() else []
    result=read(folder/'result.json') if (folder/'result.json').exists() else {}
    process=read(folder.with_suffix('.process.json'))
    epoch=execution['started_unix']+process['started_monotonic']-execution['started_monotonic']
    responses=[]
    for i,r in enumerate(raw):
        content=r.get('message',{}).get('content','');lines=content.splitlines()
        responses.append({'index':i,'tokens':r.get('eval_count',0),'done_reason':r.get('done_reason'),
            'content_sha256':hashlib.sha256(content.encode()).hexdigest(),'characters':len(content),
            'comment_lines':sum(x.lstrip().startswith('#') for x in lines),'lines':len(lines),
            'prefix_before_fence_characters':content.find('```'),'fence_count':content.count('```'),
            'thinking_field_characters':len(r.get('message',{}).get('thinking','')),
            'reply_end_seconds':datetime.datetime.fromisoformat(r['created_at'].replace('Z','+00:00')).timestamp()-epoch})
    actions=[];cursor=0
    trajectory=read(folder/'trajectory.json') if (folder/'trajectory.json').exists() else {'messages':[]}
    for index,message in enumerate(trajectory['messages'][:-1]):
        following=trajectory['messages'][index+1]
        if message['role']!='assistant' or 'actions' not in message.get('extra',{}) or 'returncode' not in following.get('extra',{}):continue
        match=next((i for i in range(cursor,len(raw)) if raw[i].get('message',{}).get('content')==message['content']),None)
        if match is None:continue
        cursor=match+1
        actions.append({'response_index':match,'assistant_message_index':index,'observation_message_index':index+1,
            'start_seconds':message['extra']['timestamp']-epoch,'end_seconds':following['extra']['timestamp']-epoch,
            'tokens_before_action':sum(r.get('eval_count',0) for r in raw[:match+1]),'returncode':following['extra']['returncode']})
    first=actions[0] if actions else None
    success=next((x for x in actions if x['returncode']==0),None)
    return {'responses':responses,'executed_actions':actions,'first_executable_action':first,'first_successful_action':success,
        'recognized_public_checks':[{'action':e['action'],'returncode':e['returncode'],'source_sha256':e['source_sha256']} for e in result.get('public_tests',[])],
        'recorded_repairs':result.get('repairs',0),'raw_status':result.get('status'),
        'context_events':len(result.get('context_events',[]))}
