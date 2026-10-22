"""Build isolated loader modules with their compatible Gradle JVMs."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TARGETS = json.loads((ROOT / 'targets.json').read_text())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', choices=['all', *TARGETS])
    parser.add_argument('tasks', nargs='*', default=['build'])
    args = parser.parse_args()
    for target in TARGETS if args.target == 'all' else [args.target]:
        config = TARGETS[target]
        env = os.environ.copy()
        # The legacy Gradle 5 launcher itself needs Java 8. Modern builds use 17/21.
        launcher_java = 8 if config['gradle'].startswith('5.') else 17 if config['java'] < 21 else 21
        java_home = env.get(f'JAVA_HOME_{launcher_java}_X64') or env.get(f'JAVA{launcher_java}_HOME')
        if java_home:
            env['JAVA_HOME'] = java_home
        wrapper = 'gradlew.bat' if os.name == 'nt' else './gradlew'
        cmd = [wrapper, *(args.tasks or ['build']), '--no-daemon', '--console=plain']
        print(f'Building {target}: {cmd}', flush=True)
        subprocess.run(cmd, cwd=ROOT / target, env=env, check=True, shell=os.name == 'nt')

if __name__ == '__main__':
    main()
