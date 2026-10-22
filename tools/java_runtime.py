"""Find the correct Gradle launcher without depending on this workstation's paths."""
import os
from pathlib import Path
import re

def java_home(major, env):
    explicit = env.get(f'JAVA_HOME_{major}_X64') or env.get(f'JAVA{major}_HOME')
    if explicit:
        return explicit
    candidates = []
    if env.get('JAVA_HOME'):
        candidates.append(Path(env['JAVA_HOME']))
    caches = {Path.home()/'.gradle/jdks'}
    if env.get('GRADLE_USER_HOME'):
        caches.add(Path(env['GRADLE_USER_HOME'])/'jdks')
    for cache in caches:
        if cache.is_dir():
            candidates.extend(cache.glob('*'))
            candidates.extend(cache.glob('*/*'))
    for candidate in candidates:
        release = candidate/'release'
        if release.is_file():
            match = re.search(r'JAVA_VERSION="(?:1\.)?(\d+)', release.read_text(errors='replace'))
            if match and int(match[1])==major:
                return str(candidate)
    return None
