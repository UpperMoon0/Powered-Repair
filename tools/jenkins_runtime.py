"""Native-OS CI launch helpers; orchestration is owned by NsTut-CICD."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from java_runtime import java_home

ROOT = Path(__file__).resolve().parents[1]


def environment(target=None):
    env = os.environ.copy()
    homes = {major: java_home(major, env) for major in (8, 17, 21, 25)}
    if not all(homes.values()):
        raise RuntimeError('CI requires the verified Java 8, 17, 21 and 25 toolchains')
    cache = ROOT / 'build/jenkins-gradle-cache'
    cache.mkdir(parents=True, exist_ok=True)
    # Build-local derived caches prevent one loader/repository contaminating another.
    paths = ','.join(str(Path(home)).replace('\\', '/') for home in homes.values())
    (cache/'gradle.properties').write_text('org.gradle.java.installations.paths='+paths+
        '\norg.gradle.java.installations.auto-detect=false\norg.gradle.java.installations.auto-download=false'
        '\norg.gradle.workers.max=1\norg.gradle.jvmargs=-Xmx1536m -XX:ActiveProcessorCount=2\n')
    env['GRADLE_USER_HOME'] = str(cache)
    if target:
        cfg = json.loads((ROOT/'targets.json').read_text())[target]
        launcher = 8 if cfg['gradle'].startswith('5.') else 21 if cfg['java'] >= 21 else 17
    else:
        launcher = 17
    env['JAVA_HOME'] = homes[launcher]
    env['PATH'] = str(Path(homes[launcher])/'bin') + os.pathsep + env.get('PATH', '')
    for major, home in homes.items():
        env[f'JAVA_HOME_{major}'] = home
    return env


def gradle(target, tasks, env, capture=False):
    root = ROOT / target if target else ROOT
    wrapper = 'gradlew.bat' if os.name == 'nt' else './gradlew'
    if os.name != 'nt':
        path = root / 'gradlew'
        path.chmod(path.stat().st_mode | 0o111)
    return subprocess.run([wrapper, *tasks, '--no-daemon', '--max-workers=1', '--console=plain'],
                          cwd=root, env=env, check=not capture, shell=os.name == 'nt',
                          capture_output=capture, text=True)


def prepare_legacy_assets(target, env):
    """Retry only download preparation; never retry a server acceptance failure."""
    if target != 'forge-1.12.2':
        return
    transient = ('read timed out', 'connect timed out', 'connection reset',
                 'http response code: 429', 'http response code: 502',
                 'http response code: 503', 'http response code: 504')
    for attempt in range(3):
        result = gradle(target, ['downloadAssets', '-PdevMods=false', '-PclientUi=false'], env, capture=True)
        output = (result.stdout or '') + (result.stderr or '')
        print(output, end='', flush=True)
        if result.returncode == 0:
            return
        if attempt == 2 or not any(marker in output.lower() for marker in transient):
            raise subprocess.CalledProcessError(result.returncode, result.args)
        print('Transient vanilla asset download failed; retrying preparation only', flush=True)
        time.sleep((2, 5)[attempt])


if __name__ == '__main__':
    env = environment()
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tools', '-p', 'test_*.py', '-v'],
                   cwd=ROOT, env=env, check=True)
    gradle(None, [':common:test'], env)
