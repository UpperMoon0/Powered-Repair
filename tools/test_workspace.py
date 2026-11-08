import json
from pathlib import Path
import tempfile
import unittest
import copy
from unittest.mock import patch

import generate
import native_sources
import release
from model_validation import validate_model
from station_assets import model

class WorkspaceTests(unittest.TestCase):
    def test_model_uses_one_texel_per_model_unit_on_every_face(self):
        block=model('test_repair')
        sizes={f'test_repair:block/{m}':(16,16) for m in ('steel','casing','vent','circuit')}
        self.assertEqual(validate_model(block,sizes),132)
        stretched=copy.deepcopy(block)
        stretched['elements'][0]['faces']['north']['uv']=[0,0,16,16]
        with self.assertRaisesRegex(ValueError,'stretched texture'):
            validate_model(stretched,sizes)
        partial=copy.deepcopy(block)
        partial['elements'][0]['from'][0]=1.5
        with self.assertRaisesRegex(ValueError,'whole-texel grid'):
            validate_model(partial,sizes)
        wrong_resolution={**sizes,'test_repair:block/steel':(32,32)}
        with self.assertRaisesRegex(ValueError,'stretched texture'):
            validate_model(block,wrong_resolution)

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
            (root/'icon.png').write_bytes((generate.ROOT/'icon.png').read_bytes())
            with patch.object(generate,'ROOT',root):
                for target, cfg in release.TARGETS.items():
                    generate.generate(target)
                    output = root / target / 'build/generated/mod'
                    java = '\n'.join(f.read_text() for f in output.rglob('*.java'))
                    self.assertNotRegex(java, r'@[A-Z_]+@')
                    self.assertIn('RepairEngine', java)
                    self.assertIn(props['mod_id'],java)
                    icon_path = f"assets/{props['mod_id']}/icon.png"
                    self.assertEqual((output/'resources'/icon_path).read_bytes(), (root/'icon.png').read_bytes())
                    metadata = next(output.rglob('mcmod.info' if cfg['minecraft'] == '1.12.2' else 'neoforge.mods.toml' if cfg['loader'] == 'neoforge' else 'mods.toml'))
                    self.assertIn(icon_path, metadata.read_text())
                    self.assertIn('openui_mc', metadata.read_text())
                    if cfg['minecraft'] != '1.12.2':
                        self.assertIn(f'versionRange="[{props["openui_version"]},)"', metadata.read_text())
                    materials=output/'resources'/f"assets/{props['mod_id']}/textures/block"
                    for name in ('steel','casing','vent','circuit'):
                        image=(materials/(name+'.png')).read_bytes()
                        self.assertEqual(image[:8],b'\x89PNG\r\n\x1a\n')
                        self.assertEqual((int.from_bytes(image[16:20],'big'),int.from_bytes(image[20:24],'big')),(16,16))
                    block_model=json.loads((output/'resources'/f"assets/{props['mod_id']}/models/block/repair_station.json").read_text())
                    for element in block_model['elements']:
                        self.assertTrue(all(0<=a<b<=16 for a,b in zip(element['from'],element['to'])))
                    files = list(output.rglob('repair_station.json'))
                    recipe = next(json.loads(f.read_text()) for f in files if f.parent.name in ('recipe','recipes'))
                    recipe_root = 'assets' if cfg['minecraft'] == '1.12.2' else 'data'
                    self.assertTrue((output/'resources'/recipe_root/props['mod_id']/('recipe' if cfg['loader'] == 'neoforge' else 'recipes')/'repair_station.json').is_file())
                    self.assertEqual(recipe['pattern'], ['IBI','RAR','IBI'])
                    self.assertEqual(''.join(recipe['pattern']).count('B'), 2)
                    self.assertIn('mending' if cfg['minecraft'] != '1.12.2' else '70s', json.dumps(recipe['key']['B']))
                    key = {k:v if isinstance(v,str) else v.get('item',v.get('items')) for k,v in recipe['key'].items()}
                    result = recipe['result']
                    recipes.append((recipe['pattern'],key,result.get('id',result.get('item')),result['count']))
        self.assertTrue(all(recipe == recipes[0] for recipe in recipes))

    def test_identity_change_reaches_every_adapter(self):
        for target, cfg in release.TARGETS.items():
            family = '112' if cfg['minecraft']=='1.12.2' else '116' if cfg['minecraft']=='1.16.5' else 'modern'
            text = '\n'.join(native_sources.sources(cfg,family).values())
            self.assertIn('@ID@',text)
            self.assertNotIn('powered_repair',text)

    def test_renaming_removes_old_generated_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            text=(generate.ROOT/'gradle.properties').read_text()
            (root/'gradle.properties').write_text(text)
            (root/'targets.json').write_text((generate.ROOT/'targets.json').read_text())
            (root/'icon.png').write_bytes((generate.ROOT/'icon.png').read_bytes())
            with patch.object(generate,'ROOT',root):
                generate.generate('forge-1.20.1')
                old=generate.properties()['mod_id']
                (root/'gradle.properties').write_text(text.replace('mod_id='+old,'mod_id=renamed_repair'))
                generate.generate('forge-1.20.1')
                out=root/'forge-1.20.1/build/generated/mod/resources'
                self.assertFalse((out/'assets'/old).exists())
                self.assertTrue((out/'assets/renamed_repair').is_dir())

    def test_release_is_blocked_for_provisional_identity(self):
        with patch.object(release,'properties',return_value={'identity_final':'false'}):
            with self.assertRaisesRegex(ValueError,'final mod ID'):
                release.preflight()

    def test_no_production_dependencies_on_dev_mods(self):
        for target,cfg in release.TARGETS.items():
            plan = release.metadata(cfg,'alpha','notes')
            self.assertEqual(plan['relations'],{'projects':[{'slug':'openui-mc','type':'requiredDependency'}]})
            self.assertEqual(plan['releaseType'],'alpha')

    def test_dev_lock_has_jei_and_records_powah_gaps(self):
        lock = json.loads((generate.ROOT/'dev-mods.lock.json').read_text())
        for target in release.TARGETS:
            self.assertTrue(any(d['project']=='jei' for d in lock[target]['dependencies']))
            if target in ('forge-1.12.2','neoforge-26.2'):
                self.assertTrue(lock[target]['unavailable'])
                fallback = 'solar-flux-reborn' if target == 'forge-1.12.2' else 'energized-power'
                self.assertTrue(any(d['project']==fallback for d in lock[target]['dependencies']))
            else:
                self.assertTrue(any(d['project']=='powah' for d in lock[target]['dependencies']))

if __name__ == '__main__':
    unittest.main()
