"""Generate the existing native build/acceptance matrix without publishing."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def plan(targets=None):
    targets = targets if targets is not None else json.loads((ROOT / 'targets.json').read_text())
    result = [{'name': 'Shared repair contracts', 'java': 17,
               'command': './gradlew :common:test --no-daemon --max-workers=1'}]
    for target, configuration in targets.items():
        if not re.fullmatch(r'(?:forge|neoforge)-[0-9]+(?:\.[0-9]+)*', target):
            raise ValueError('Invalid native target')
        # Preserve the launchers used by the existing workflow/smoke controller.
        launcher = 8 if configuration['gradle'].startswith('5.') else 21 if configuration['java'] >= 21 else 17
        result.append({'name': target, 'java': launcher, 'minutes': 60,
                       'command': 'python3 tools/jenkins_target.py ' + target})
    return result


if __name__ == '__main__':
    print(json.dumps(plan()))
