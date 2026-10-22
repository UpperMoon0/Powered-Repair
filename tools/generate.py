"""Generate loader glue and resources from shared templates and one identity file."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

def properties():
    return dict(line.split('=', 1) for line in (ROOT / 'gradle.properties').read_text().splitlines()
                if '=' in line and not line.lstrip().startswith('#'))

def generate(target):
    p = properties()
    cfg = json.loads((ROOT / 'targets.json').read_text())[target]
    mod = p['mod_id']
    if not re.fullmatch('[a-z][a-z0-9_]{1,63}', mod):
        raise ValueError('mod_id must be a lowercase loader-safe identifier')
    out = ROOT / target / 'build/generated/mod'
    def write(path, value):
        path = out / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding='utf-8')
    def resource(path, data):
        write('resources/' + path, json.dumps(data, indent=2) + '\n')
    values = {'ID': mod, 'NAME': p['mod_name'], 'VERSION': p['mod_version']}
    # Native APIs changed at these boundaries; repair behavior remains in common/.
    family = '112' if cfg['minecraft'] == '1.12.2' else '116' if cfg['minecraft'] == '1.16.5' else 'modern'
    from native_sources import sources
    for filename, text in sources(cfg, family).items():
        for key, value in values.items():
            text = text.replace('@' + key + '@', value)
        write('java/com/nstut/repair/' + filename, text)
    resource('pack.mcmeta', {'pack': {'pack_format': cfg['pack'], 'description': p['mod_name']}})
    resource(f'assets/{mod}/blockstates/repair_station.json', {'variants': {'': {'model': f'{mod}:block/repair_station'}}})
    texture_root = 'blocks' if family == '112' else 'block'
    resource(f'assets/{mod}/models/block/repair_station.json', {
        'parent': 'minecraft:block/cube', 'textures': {
            'particle': f'minecraft:{texture_root}/iron_block', 'down': f'minecraft:{texture_root}/iron_block',
            'up': f'minecraft:{texture_root}/anvil_top', 'north': f'minecraft:{texture_root}/redstone_block',
            'east': f'minecraft:{texture_root}/iron_block', 'south': f'minecraft:{texture_root}/redstone_block',
            'west': f'minecraft:{texture_root}/iron_block'}})
    resource(f'assets/{mod}/models/item/repair_station.json', {'parent': f'{mod}:block/repair_station'})
    lang = {f'block.{mod}.repair_station': p['mod_name'] + ' Station', f'tile.{mod}.repair_station.name': p['mod_name'] + ' Station',
            f'container.{mod}.repair_station': 'Repair Station'}
    if family == '112':
        write(f'resources/assets/{mod}/lang/en_us.lang', '\n'.join(k+'='+v for k,v in lang.items())+'\n')
    else:
        resource(f'assets/{mod}/lang/en_us.json', lang)
    modern = cfg['minecraft'].startswith('26.')
    singular = modern or cfg['minecraft'] == '1.21.1'
    recipes, loot = ('recipe', 'loot_table') if singular else ('recipes', 'loot_tables')
    key = (lambda item: item) if modern else (lambda item: {'item': item})
    result = {'id' if singular else 'item': f'{mod}:repair_station', 'count': 1}
    resource(f'data/{mod}/{recipes}/repair_station.json', {'type': 'minecraft:crafting_shaped',
        'pattern': ['III', 'RAR', 'III'], 'key': {'I': key('minecraft:iron_ingot'),
        'R': key('minecraft:redstone'), 'A': key('minecraft:anvil')}, 'result': result})
    if family != '112':
        resource(f'data/{mod}/{loot}/blocks/repair_station.json', {'type': 'minecraft:block', 'pools': [{'rolls': 1,
            'entries': [{'type': 'minecraft:item', 'name': f'{mod}:repair_station'}],
            'conditions': [{'condition': 'minecraft:survives_explosion'}]}]})
        tags = 'block' if singular else 'blocks'
        resource(f'data/minecraft/tags/{tags}/mineable/pickaxe.json', {'replace': False, 'values': [f'{mod}:repair_station']})
    if modern:
        resource(f'assets/{mod}/items/repair_station.json', {'model': {'type': 'minecraft:model', 'model': f'{mod}:item/repair_station'}})
    if family == '112':
        resource('mcmod.info', [{'modid': mod, 'name': p['mod_name'], 'description': p['mod_description'],
            'version': p['mod_version'], 'mcversion': cfg['minecraft'], 'authorList': [p['mod_authors']]}])
    else:
        neo = cfg['loader'] == 'neoforge'
        minloader = '1' if neo else '36' if family == '116' else '47'
        text = f'''modLoader="javafml"
loaderVersion="[{minloader},)"
license="{p['mod_license']}"
[[mods]]
modId="{mod}"
version="{p['mod_version']}"
displayName="{p['mod_name']}"
authors="{p['mod_authors']}"
description=''' + "'''" + p['mod_description'] + "'''" + f'''
[[dependencies.{mod}]]
modId="{cfg['loader']}"
{'type="required"' if neo else 'mandatory=true'}
versionRange="[{cfg['loaderVersion']},)"
ordering="NONE"
side="BOTH"
[[dependencies.{mod}]]
modId="minecraft"
{'type="required"' if neo else 'mandatory=true'}
versionRange="[{cfg['minecraft']}]"
ordering="NONE"
side="BOTH"
'''
        write('resources/META-INF/' + ('neoforge.mods.toml' if neo else 'mods.toml'), text)

if __name__ == '__main__':
    generate(sys.argv[1])
