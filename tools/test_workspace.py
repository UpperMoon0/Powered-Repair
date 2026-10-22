import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import generate
import native_sources
import release

class WorkspaceTests(unittest.TestCase):
    def test_only_requested_targets(self):
        self.assertEqual(set(release.TARGETS), {'forge-1.12.2','forge-1.16.5','forge-1.20.1',
            'neoforge-1.21.1','neoforge-26.1.2','neoforge-26.2'})

    def test_resource_and_identity_parity(self):
        props = generate.properties()
        recipes = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'gradle.properties').write_text((generate.ROOT/'gradle.properties').read_text())
            (root/'targets.json').write_text((generate.ROOT/'targets.json').read_text())
            with patch.object(generate,'ROOT',root):
                for target, cfg in release.TARGETS.items():
                    generate.generate(target)
                    output = root / target / 'build/generated/mod'
                    java = '\n'.join(f.read_text() for f in output.rglob('*.java'))
                    self.assertNotRegex(java, r'@[A-Z_]+@')
                    self.assertIn('RepairEngine', java)
                    self.assertIn(props['mod_id'],java)
                    files = list(output.rglob('repair_station.json'))
                    recipe = next(json.loads(f.read_text()) for f in files if '/data/' in f.as_posix() and '/tags/' not in f.as_posix() and '/blocks/' not in f.as_posix())
                    key = {k:v if isinstance(v,str) else v['item'] for k,v in recipe['key'].items()}
                    result = recipe['result']
                    recipes.append((recipe['pattern'],key,result.get('id',result.get('item')),result['count']))
        self.assertTrue(all(recipe == recipes[0] for recipe in recipes))

    def test_identity_change_reaches_every_adapter(self):
        for target, cfg in release.TARGETS.items():
            family = '112' if cfg['minecraft']=='1.12.2' else '116' if cfg['minecraft']=='1.16.5' else 'modern'
            text = '\n'.join(native_sources.sources(cfg,family).values())
            self.assertIn('@ID@',text)
            self.assertNotIn('powered_repair',text)

    def test_release_is_blocked_for_provisional_identity(self):
        with patch.object(release,'properties',return_value={'identity_final':'false'}):
            with self.assertRaisesRegex(ValueError,'final mod ID'):
                release.preflight()

    def test_no_production_dependencies_on_dev_mods(self):
        for target,cfg in release.TARGETS.items():
            plan = release.metadata(cfg,'alpha','notes')
            self.assertEqual(plan['relations'],{'projects':[]})
            self.assertEqual(plan['releaseType'],'alpha')

    def test_dev_lock_has_jei_and_records_powah_gaps(self):
        lock = json.loads((generate.ROOT/'dev-mods.lock.json').read_text())
        for target in release.TARGETS:
            self.assertTrue(any(d['project']=='jei' for d in lock[target]['dependencies']))
            if target in ('forge-1.12.2','neoforge-26.2'):
                self.assertTrue(lock[target]['unavailable'])
            else:
                self.assertTrue(any(d['project']=='powah' for d in lock[target]['dependencies']))

if __name__ == '__main__':
    unittest.main()
