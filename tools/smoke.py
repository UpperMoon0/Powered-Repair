"""Start a module-owned server and require a native acceptance report."""
import json
import os
from pathlib import Path
import subprocess
import sys
from java_runtime import java_home

ROOT = Path(__file__).resolve().parents[1]
TARGETS = json.loads((ROOT/'targets.json').read_text())

def main():
    target = sys.argv[1]
    cfg = TARGETS[target]
    run = ROOT / target / 'run'
    run.mkdir(exist_ok=True)
    report = run / 'repair-smoke-result.txt'
    report.unlink(missing_ok=True)
    (run/'eula.txt').write_text('eula=true\n')
    flat = 'FLAT' if cfg['java']==8 else 'minecraft:flat'
    (run/'server.properties').write_text('level-name=powered-repair-smoke\nonline-mode=false\nserver-ip=127.0.0.1\nserver-port=0\nmax-players=1\nview-distance=2\nsimulation-distance=2\nspawn-protection=0\nlevel-type='+flat+'\n')
    env = os.environ.copy()
    env['POWERED_REPAIR_SMOKE']='1'
    # Set DEV_SMOKE=true to exercise the locked JEI/Powah dev dependency graph too.
    launcher = 8 if cfg['gradle'].startswith('5.') else 21 if cfg['java'] >= 21 else 17
    home = java_home(launcher,env)
    if home:
        env['JAVA_HOME']=home
    wrapper = 'gradlew.bat' if os.name=='nt' else './gradlew'
    command=[wrapper,'runServer','--no-daemon','--console=plain']
    if env.get('DEV_SMOKE')!='true':
        command.append('-PdevMods=false')
    subprocess.run(command,cwd=ROOT/target,env=env,check=True,timeout=900,shell=os.name=='nt')
    expected='NATIVE_REPAIR_SMOKE_PASS '+cfg['minecraft']
    if not report.is_file() or report.read_text()!=expected:
        raise RuntimeError('Native smoke probe did not finish successfully: '+target)
    print(expected)

if __name__=='__main__':
    main()
