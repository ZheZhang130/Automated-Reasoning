"""Real isolated judge checks: existing Qwen toy candidate and deliberate resource abuse."""
import json
import shutil

from optlib import DATA, JUDGE, VENDOR, read, save
from judge_watch import score


def main():
    root=DATA/'diagnostics/judge-monitor-controls'
    root.mkdir(exist_ok=False)
    row=DATA.parent/'eval-v2/development-v5/private/dev-negative-squares.json'
    correct=root/'existing-qwen-toy'
    correct.mkdir()
    shutil.copyfile(DATA/'diagnostics/dev-negative-squares--native-fixed-16k-4k/solution.py',correct/'solution.py')
    evaluation=score(correct,row,VENDOR,JUDGE)
    save(correct/'evaluation.json',evaluation)
    if evaluation['status']!='pass':raise RuntimeError('Known synthetic Qwen candidate did not pass')
    oom=root/'deliberate-oom'
    oom.mkdir()
    # Resource fixture only; this does not implement a benchmark algorithm.
    (oom/'solution.py').write_text('payload = bytearray(2 * 1024 ** 3)\n',encoding='utf-8')
    evaluation=score(oom,row,VENDOR,JUDGE)
    save(oom/'evaluation.json',evaluation)
    if evaluation.get('resource')!='memory_1g' or evaluation['status']!='candidate_resource_failure':
        raise RuntimeError('Deliberate OOM was not identified from owned Docker evidence')
    summary={'known_qwen_toy_pass':True,'deliberate_oom_identified':True,'evidence':str(root)}
    save(root/'summary.json',summary)
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
