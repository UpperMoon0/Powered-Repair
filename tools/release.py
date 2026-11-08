"""Inspect production JARs; release orchestration is owned by NsTut-CICD."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import zipfile

from generate import ROOT, properties

TARGETS = json.loads((ROOT / 'targets.json').read_text())

def filename(target):
    p = properties()
    return f"{p['mod_id']}-{target}-{p['mod_version']}.jar"

def inspect(target, jar=None):
    p = properties()
    jar = Path(jar) if jar else ROOT / target / 'build/libs' / filename(target)
    if jar.name != filename(target):
        raise ValueError('Unexpected artifact name: ' + jar.name)
    with zipfile.ZipFile(jar) as z:
        names = set(z.namelist())
        required = {'com/nstut/repair/core/RepairEngine.class', 'com/nstut/repair/core/RepairSettings.class',
                    'com/nstut/repair/core/EnergyBuffer.class', 'com/nstut/repair/RepairMod.class',
                    'com/nstut/repair/RepairMenu.class','com/nstut/repair/RepairScreen.class'}
        cfg = TARGETS[target]
        metadata = 'mcmod.info' if cfg['minecraft'] == '1.12.2' else 'META-INF/neoforge.mods.toml' if cfg['loader'] == 'neoforge' else 'META-INF/mods.toml'
        icon_path = f"assets/{p['mod_id']}/icon.png"
        required |= {metadata, f"assets/{p['mod_id']}/blockstates/repair_station.json", icon_path}
        required |= {f"assets/{p['mod_id']}/textures/block/{material}.png" for material in ('steel','casing','vent','circuit')}
        if not required <= names:
            raise ValueError(f'{target}: missing {sorted(required - names)}')
        text = z.read(metadata).decode()
        if p['mod_id'] not in text or p['mod_version'] not in text or '${' in text:
            raise ValueError('Invalid packaged identity/version')
        if icon_path not in text or z.read(icon_path) != (ROOT/'icon.png').read_bytes():
            raise ValueError('Missing icon metadata or outdated packaged icon')
        if 'openui_mc' not in text:
            raise ValueError('Missing OpenUI client dependency')
        for material in ('steel','casing','vent','circuit'):
            image=z.read(f"assets/{p['mod_id']}/textures/block/{material}.png")
            if image[:8] != b'\x89PNG\r\n\x1a\n' or int.from_bytes(image[16:20],'big') != 16 or int.from_bytes(image[20:24],'big') != 16:
                raise ValueError('Block textures must be 16x16 PNGs')
        from model_validation import validate_model
        block_model=json.loads(z.read(f"assets/{p['mod_id']}/models/block/repair_station.json"))
        validate_model(block_model,{f"{p['mod_id']}:block/{m}":(16,16) for m in ('steel','casing','vent','circuit')})
        limit = {8:52,17:61,21:65,25:69}[cfg['java']]
        for name in names:
            if name.endswith('.class'):
                if name.startswith('com/nstut/repair/preview/'):
                    raise ValueError('Development preview leaked into production JAR')
                if not name.startswith('com/nstut/repair/'):
                    raise ValueError('Unexpected bundled dependency: ' + name)
                if int.from_bytes(z.read(name)[6:8], 'big') > limit:
                    raise ValueError('Incompatible bytecode: ' + name)
        if 'fabric.mod.json' in names:
            raise ValueError('Fabric metadata in a Forge/NeoForge artifact')
    return {'target': target, 'file': jar.name, 'sha256': hashlib.sha256(jar.read_bytes()).hexdigest()}

def preflight():
    p = properties()
    if p.get('identity_final') != 'true':
        raise ValueError('Set the final mod ID/name and identity_final=true before publishing')
    if os.environ.get('RELEASE_TAG') != 'v' + p['mod_version']:
        raise ValueError('Release must run on the tag matching mod_version')
    if not re.fullmatch('[1-9][0-9]*', os.environ.get('CURSEFORGE_PROJECT_ID', '')):
        raise ValueError('Configure repository variable CURSEFORGE_PROJECT_ID')
    if not os.environ.get('CURSEFORGE_API_TOKEN'):
        raise ValueError('Configure repository secret CURSEFORGE_API_TOKEN')
    if not (ROOT / 'changelog' / (p['mod_version'] + '.md')).is_file():
        raise ValueError('Missing versioned changelog')


def metadata(cfg, release_type, changelog):
    p = properties()
    return {'changelog':changelog, 'changelogType':'markdown',
            'displayName':f"{p['mod_name']} {p['mod_version']} - {cfg['loader'].title().replace('Neoforge','NeoForge')} {cfg['minecraft']}",
            'releaseType':release_type,
            'gameVersionNames':[cfg['minecraft'], 'Forge' if cfg['loader']=='forge' else 'NeoForge'],
            'relations':{'projects':[{'slug':'openui-mc','type':'requiredDependency'}]}}


if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'inspect':
        print(json.dumps(inspect(sys.argv[2]), indent=2))
    elif command == 'preflight':
        raise SystemExit('Release orchestration is owned by UpperMoon0/NsTut-CICD/jenkins/artifacts/mod_release.py')
    elif command == 'publish':
        raise SystemExit('Publish through the reviewed NsTut-CICD release request, not the mod checkout')
    else:
        raise SystemExit('Unknown command')
