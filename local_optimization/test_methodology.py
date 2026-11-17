"""Guard frozen control identity and evaluation separation."""
import unittest
from pathlib import Path

from optlib import DATA, ROOT, V2, digest, read


class Methodology(unittest.TestCase):
    def test_original_control_is_exact(self):
        key = 'heredoc-v6-16k-common'
        self.assertEqual(read(ROOT/'profiles.json')[key], read(V2/'profiles.json')[key])

    def test_frozen_splits_and_exclusions(self):
        manifests = [read(ROOT/(name+'_manifest.json')) for name in ('development','selection','heldout')]
        old = set(read(DATA/'exclusion-audit.json')['excluded'])
        seen_ids, seen_contests = set(), set()
        for manifest in manifests:
            ids = {t['task_id'] for t in manifest['tasks']}
            contests = {(t['platform'],t['contest_id']) for t in manifest['tasks']}
            self.assertFalse(ids & old)
            self.assertFalse(ids & seen_ids)
            self.assertFalse(contests & seen_contests)
            seen_ids |= ids; seen_contests |= contests
            self.assertEqual(manifest,read(DATA/'dataset'/manifest['split']/'manifest.json'))
        self.assertEqual([len(m['tasks']) for m in manifests],[6,12,20])

    def test_public_bundles_contain_no_private_rows(self):
        for name in ('development','selection','heldout'):
            manifest=read(ROOT/(name+'_manifest.json'))
            for task in manifest['tasks']:
                folder=DATA/'dataset'/name/'public'/task['task_id']
                self.assertLessEqual({p.name for p in folder.iterdir()},{'task.json','public_tests.json','check.py','solution.py'})
                self.assertFalse(any(p.is_symlink() or not p.is_file() for p in folder.iterdir()))
                self.assertEqual({p.name:digest(p) for p in folder.iterdir()},task['public_sha256'])
                self.assertEqual(set(read(folder/'task.json')),{'task_id','version','statement','submission_path'})


if __name__=='__main__':
    unittest.main(verbosity=2)
