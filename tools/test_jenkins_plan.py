import unittest
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from jenkins_plan import plan
import jenkins_runtime
from java_runtime import java_home


class JenkinsPlanTests(unittest.TestCase):
    def test_new_native_contract_target_gets_build_and_smoke_verification(self):
        result = plan({'neoforge-26.99': {'java': 25, 'gradle': '9.2.1'}})
        self.assertEqual(result[-1]['name'], 'neoforge-26.99')
        self.assertEqual(result[-1]['java'], 21)
        self.assertEqual(result[-1]['command'], 'python3 tools/jenkins_target.py neoforge-26.99')

    def test_old_gradle_launcher_and_unsafe_target(self):
        self.assertEqual(plan({'forge-1.12.2': {'java': 8, 'gradle': '5.6.4'}})[-1]['java'], 8)
        with self.assertRaises(ValueError):
            plan({'../other': {'java': 8, 'gradle': '5.6.4'}})


class GradleToolchainCompatibilityTests(unittest.TestCase):
    def test_pinned_jenkins_jdk_environment_is_honored(self):
        self.assertEqual(java_home(8, {'JAVA_HOME_8': 'pinned-java8'}), 'pinned-java8')

    def test_native_ci_wrapper_on_each_os(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'forge-1.12.2').mkdir()
            (root/'forge-1.12.2/gradlew').write_text('fixture')
            for platform, wrapper in [('nt', 'gradlew.bat'), ('posix', './gradlew')]:
                with self.subTest(platform=platform), patch.object(jenkins_runtime, 'ROOT', root), \
                        patch.object(jenkins_runtime, 'os', SimpleNamespace(name=platform)), \
                        patch.object(jenkins_runtime.subprocess, 'run') as run:
                    jenkins_runtime.gradle('forge-1.12.2', ['build', '-PdevMods=false'], {'JAVA_HOME':'pinned'})
                    self.assertEqual(run.call_args.args[0][0], wrapper)
                    self.assertIn('-PdevMods=false', run.call_args.args[0])
                    self.assertEqual(run.call_args.kwargs['shell'], platform == 'nt')

    def test_ci_cache_is_build_local_and_all_pinned_toolchains_are_configured(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'targets.json').write_text(json.dumps({'forge-1.12.2': {'java':8,'gradle':'5.6.4'}}))
            homes = {major: str(root/('jdk'+str(major))) for major in (8,17,21,25)}
            with patch.object(jenkins_runtime,'ROOT',root), \
                    patch.object(jenkins_runtime,'java_home',side_effect=lambda major, env:homes[major]):
                env = jenkins_runtime.environment('forge-1.12.2')
                self.assertEqual(env['JAVA_HOME'],homes[8])
                self.assertEqual(Path(env['GRADLE_USER_HOME']),root/'build/jenkins-gradle-cache')
                props=(Path(env['GRADLE_USER_HOME'])/'gradle.properties').read_text()
                self.assertIn('auto-download=false',props)
                for home in homes.values():
                    self.assertIn(home.replace('\\','/'),props)

    def test_gradle9_targets_do_not_use_pre_1_0_foojay_resolver(self):
        root = Path(__file__).resolve().parents[1]
        targets = json.loads((root / "targets.json").read_text(encoding="utf-8"))
        verified = 0
        for name, data in targets.items():
            if int(data["gradle"].split(".", 1)[0]) < 9:
                continue
            settings = (root / name / "settings.gradle").read_text(encoding="utf-8")
            self.assertIn("id 'org.gradle.toolchains.foojay-resolver-convention' version '1.0.0'", settings)
            self.assertNotIn("version '0.9.0'", settings)
            verified += 1
        self.assertEqual(verified, 2)
