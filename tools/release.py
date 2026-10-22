"""Validate a complete six-target bundle and publish with durable upload receipts."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
import uuid
import zipfile

from generate import ROOT, properties

TARGETS = json.loads((ROOT / 'targets.json').read_text())
API = 'https://minecraft.curseforge.com/api'

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
                    'com/nstut/repair/core/EnergyBuffer.class', 'com/nstut/repair/RepairMod.class'}
        cfg = TARGETS[target]
        metadata = 'mcmod.info' if cfg['minecraft'] == '1.12.2' else 'META-INF/neoforge.mods.toml' if cfg['loader'] == 'neoforge' else 'META-INF/mods.toml'
        required |= {metadata, f"assets/{p['mod_id']}/blockstates/repair_station.json"}
        if not required <= names:
            raise ValueError(f'{target}: missing {sorted(required - names)}')
        text = z.read(metadata).decode()
        if p['mod_id'] not in text or p['mod_version'] not in text or '${' in text:
            raise ValueError('Invalid packaged identity/version')
        limit = {8:52,17:61,21:65,25:69}[cfg['java']]
        for name in names:
            if name.endswith('.class'):
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

def gh(*args, check=True):
    return subprocess.run(['gh', *args], cwd=ROOT, check=check, capture_output=True, text=True)

def api(path, data=None, content_type=None):
    headers = {'X-Api-Token': os.environ['CURSEFORGE_API_TOKEN'], 'Accept':'application/json'}
    if content_type:
        headers['Content-Type'] = content_type
    req = urllib.request.Request(API + path, data=data, headers=headers)
    # Never automatically retry a POST: the server may already have accepted the file.
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.load(response)
    except Exception as e:
        raise RuntimeError('CurseForge request failed; inspect upload receipts before retrying (' + type(e).__name__ + ')') from None

def metadata(cfg, release_type, changelog):
    p = properties()
    return {'changelog':changelog, 'changelogType':'markdown',
            'displayName':f"{p['mod_name']} {p['mod_version']} - {cfg['loader'].title().replace('Neoforge','NeoForge')} {cfg['minecraft']}",
            'releaseType':release_type,
            'gameVersionNames':[cfg['minecraft'], 'Forge' if cfg['loader']=='forge' else 'NeoForge'],
            'relations':{'projects':[]}}

def multipart(meta, jar):
    boundary = 'powered-repair-' + uuid.uuid4().hex
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="metadata"\r\nContent-Type: application/json\r\n\r\n'.encode()
            + json.dumps(meta).encode()
            + f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{jar.name}"\r\nContent-Type: application/java-archive\r\n\r\n'.encode()
            + jar.read_bytes() + f'\r\n--{boundary}--\r\n'.encode())
    return body, 'multipart/form-data; boundary=' + boundary

def publish():
    preflight()
    p = properties()
    tag = os.environ['RELEASE_TAG']
    channel = os.environ.get('RELEASE_TYPE', 'alpha')
    if channel not in ('alpha','beta','release'):
        raise ValueError('Invalid release channel')
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if sha != os.environ.get('SOURCE_SHA'):
        raise ValueError('Checkout does not match the workflow commit')
    dist = ROOT / 'dist'
    expected = {filename(t) for t in TARGETS}
    if {f.name for f in dist.glob('*.jar')} != expected:
        raise ValueError('Release bundle must contain exactly the six native production JARs')
    assets = [inspect(t, dist / filename(t)) for t in TARGETS]
    changelog = (ROOT / 'changelog' / (p['mod_version'] + '.md')).read_text()
    plans = {t:metadata(c,channel,changelog) for t,c in TARGETS.items()}
    version_names = {v['name'] for v in api('/game/versions')}
    missing = {n for plan in plans.values() for n in plan['gameVersionNames']} - version_names
    if missing:
        raise ValueError('Unknown CurseForge versions: ' + str(sorted(missing)))
    manifest = {'version':p['mod_version'],'source_sha':sha,'channel':channel,'assets':assets}
    project_id = os.environ['CURSEFORGE_PROJECT_ID']
    identity = {**manifest,'project_id':project_id}
    receipt = {**identity,'uploads':{}}
    receipt_path = dist / 'curseforge-receipts.json'
    existing = gh('release','view',tag,'--json','isDraft',check=False)
    if existing.returncode == 0:
        if not json.loads(existing.stdout)['isDraft']:
            raise ValueError('Release is already public; do not repeat publication')
        # A draft is only created with a receipt, so a missing receipt is an error.
        gh('release','download',tag,'--pattern','curseforge-receipts.json','--dir',str(dist),'--clobber')
        receipt = json.loads(receipt_path.read_text())
        if any(receipt.get(k) != v for k,v in identity.items()):
            raise ValueError('Draft release belongs to a different source, artifact set or channel')
    else:
        gh('release','create',tag,'--verify-tag','--draft','--title',p['mod_name']+' '+p['mod_version'],
           '--notes-file',str(ROOT/'changelog'/(p['mod_version']+'.md')))
    def save():
        receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
        gh('release','upload',tag,str(receipt_path),'--clobber')
    save()
    manifest_path = dist / 'release-manifest.json'
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    gh('release','upload',tag,str(manifest_path),*(str(dist/a['file']) for a in assets),'--clobber')
    for t in TARGETS:
        previous = receipt['uploads'].get(t)
        if previous:
            if previous.get('status') != 'confirmed':
                raise ValueError('Uncertain previous upload for '+t+'; verify on CurseForge before retrying')
            remote = api(f"/projects/{project_id}/files/{previous['file_id']}")
            if remote.get('fileName') != filename(t):
                raise ValueError('Receipt does not match remote CurseForge file')
            continue
        receipt['uploads'][t] = {'status':'pending','file':filename(t)}
        save()
        data, content_type = multipart(plans[t], dist / filename(t))
        response = api(f'/projects/{project_id}/upload-file', data, content_type)
        file_id = response.get('id')
        if not isinstance(file_id,int) or file_id <= 0:
            raise ValueError('Upload returned no confirmed CurseForge file ID')
        receipt['uploads'][t] = {'status':'confirmed','file_id':file_id,'file':filename(t)}
        save()
    gh('release','edit',tag,'--draft=false','--prerelease='+str(channel!='release').lower())

if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'inspect':
        print(json.dumps(inspect(sys.argv[2]), indent=2))
    elif command == 'preflight':
        preflight()
    elif command == 'publish':
        publish()
    else:
        raise SystemExit('Unknown command')
