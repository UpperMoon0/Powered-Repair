import unittest
from jenkins_plan import plan


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
