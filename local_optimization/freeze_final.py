"""Freeze the already selected comparison before any held-out inference."""
from optlib import DATA, MODEL, MODEL_DIGEST, ROOT, digest, read, save, sources


def main():
    target=ROOT/'final_selection.json'
    if target.exists():raise RuntimeError('Final selection is immutable; refusing replacement')
    repeated=read(DATA/'analysis/selection-repeated/analysis.json')
    probe=read(DATA/'batches/selection-final-output-probe/analysis.json')
    if repeated['completed']!=48 or probe['completed']!=2:
        raise RuntimeError('Selection repetitions/output probe are incomplete')
    if any((DATA/'batches/heldout-final/runs').glob('*/complete.json')):
        raise RuntimeError('Held-out outcomes already exist')
    control='heredoc-v6-16k-common';challenger='heredoc-opt-16k-4k-p15-r1024'
    profiles=read(ROOT/'profiles.json')
    plan=read(DATA/'batches/selection-repeat-s2109/plan.json')
    selection={'model':MODEL,'model_digest':MODEL_DIGEST,'control':control,'challenger':challenger,
        'frozen_configurations':{p:profiles[p] for p in (control,challenger)},
        'runtime_sha256':sources(),'images':plan['images'],
        'selection_repeated_sha256':digest(DATA/'analysis/selection-repeated/analysis.json'),
        'selection_results':repeated,'validation_manifest_sha256':digest(ROOT/'heldout_manifest.json'),
        'heldout_tasks':20,'seeds':[2108,2109],'planned_attempts':80,'actions':20,'repairs':3,'seconds':600,
        'confirmation_rule':{'paired_problem_bootstrap_lower_strictly_positive':True,'more_official_passes':True,
            'maximum_full_wall_ratio':1.5,'maximum_conservative_output_token_ratio':1.5,
            'missing_submissions_must_not_increase':True,'fallback_profile':control},
        'policy':'No tuning after held-out starts. Evaluate only the frozen practical challenger/control; retain original control unless all confirmation criteria hold. No expensive reasoning arm earned selection.',
        'selection_note':'Best practical seed2108 challenger repeated on identical tasks at2109. All other discovery stopped. Negative/equivocal results are retained.'}
    save(target,selection)
    print('Frozen final selection; commit final_selection.json before starting held-out.')


if __name__=='__main__':main()
