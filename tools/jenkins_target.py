"""Preserve a verified production JAR before running the dev-utility smoke gate."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from release import ROOT, TARGETS, filename, inspect


def main(target):
    if target not in TARGETS:
        raise ValueError('Unknown native target')
    subprocess.run(['./gradlew', 'build', '-PdevMods=false', '--no-daemon', '--max-workers=1', '--console=plain'],
                   cwd=ROOT / target, check=True)
    manifest = inspect(target)
    destination = ROOT / 'ci-production' / target
    destination.mkdir(parents=True)
    jar = destination / filename(target)
    shutil.copyfile(ROOT / target / 'build/libs' / filename(target), jar)
    environment = dict(os.environ, DEV_SMOKE='true')
    subprocess.run([sys.executable, str(ROOT / 'tools/smoke.py'), target],
                   cwd=ROOT, env=environment, check=True)
    if inspect(target, jar) != manifest:
        raise ValueError('Production snapshot changed during native acceptance')
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if not re.fullmatch(r'[a-f0-9]{40}', sha):
        raise ValueError('Missing native acceptance source revision')
    manifest.update(source_sha=sha, native_acceptance='passed', development_utilities=True)
    (destination / 'acceptance.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main(sys.argv[1])
