"""Refresh exact dev-only dependencies from upstream metadata (never runs during builds)."""
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def get(path):
    request = urllib.request.Request('https://api.modrinth.com/v2/' + path,
                                    headers={'User-Agent': 'NsTut/Powered-Repair dev-dependency-lock'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

def main():
    lock = {}
    for target, cfg in json.loads((ROOT / 'targets.json').read_text()).items():
        entries, seen, missing = [], set(), []
        def add(project, optional=False, version=None):
            if project in seen:
                return
            seen.add(project)
            candidates = get('project/' + project + '/version')
            candidates = [v for v in candidates if cfg['minecraft'] in v['game_versions'] and cfg['loader'] in v['loaders']]
            if version:
                candidates = [v for v in candidates if v['version_number'] == version]
            if not candidates:
                if optional:
                    missing.append(project + ': no compatible upstream release')
                    return
                raise ValueError(f'No {project} for {target}')
            v = candidates[0]
            file = next((f for f in v['files'] if f['primary']), v['files'][0])
            entries.append({'project': project, 'version': v['version_number'],
                            'coordinate': f"maven.modrinth:{project}:{v['id']}",
                            'filename': file['filename'], 'sha512': file['hashes']['sha512'],
                            'url': file['url']})
            for dep in v['dependencies']:
                if dep['dependency_type'] == 'required':
                    add(dep['project_id'])
        add('jei')
        if cfg['minecraft'] == '1.16.5':
            entries.extend([
                {'project': 'powah', 'version': '2.3.16', 'coordinate': 'curse.maven:powah-352656:3232535'},
                {'project': 'lollipop', 'version': '3.2.9', 'coordinate': 'curse.maven:lollipop-347954:3232534'}])
        else:
            add('powah', optional=True)
        lock[target] = {'dependencies': entries, 'unavailable': missing}
        print(target, [(e['project'],e['version']) for e in entries], missing, flush=True)
    (ROOT / 'dev-mods.lock.json').write_text(json.dumps(lock, indent=2) + '\n')

if __name__ == '__main__':
    main()
