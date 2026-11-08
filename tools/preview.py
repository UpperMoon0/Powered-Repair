"""Capture the real OpenUI station screen and baked model in an isolated 1.21.1 client."""
import json
import os
from pathlib import Path
import subprocess
import shutil
from java_runtime import java_home

ROOT = Path(__file__).resolve().parents[1]

def main():
    env = os.environ.copy()
    env['JAVA_HOME'] = java_home(21, env) or env.get('JAVA_HOME', '')
    homes = list(dict.fromkeys(home for home in (java_home(v,env) for v in (8,17,21,25)) if home))
    module = ROOT/'neoforge-1.21.1'
    output = module/'build/ui-previews'
    source_world = module/'run/powered-repair-smoke'
    if not (source_world/'level.dat').exists():
        raise RuntimeError('Create the isolated server fixture first: python tools/smoke.py neoforge-1.21.1')
    run = module/'build/ui-preview-run'
    run.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_world, run/'saves/RepairPreviewWorld', dirs_exist_ok=True)
    (run/'options.txt').write_text('onboardAccessibility:false\nguiScale:3\nmaxFps:60\n')
    if (output/'manifest.json').exists():
        (output/'manifest.json').unlink()
    wrapper = 'gradlew.bat' if os.name == 'nt' else './gradlew'
    subprocess.run([wrapper,'runUiPreview','-PuiPreview=true','-Porg.gradle.java.installations.paths='+','.join(homes),
                    '--no-daemon','--console=plain'],cwd=module,env=env,check=True,shell=os.name=='nt',timeout=600)
    manifest = json.loads((output/'manifest.json').read_text())
    assert len(manifest['screens']) == 8
    assert all((output/(name+'.png')).is_file() for name in manifest['screens'])
    print('Eight real-client previews passed:',output)

if __name__ == '__main__':
    main()
