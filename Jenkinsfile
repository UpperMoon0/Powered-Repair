@Library('nstut-ci') _

nstutGradle(
    verify: "python3 -m unittest discover -s tools -p 'test_*.py' -v",
    plan: 'python3 tools/jenkins_plan.py',
    tests: '**/build/test-results/test/*.xml',
    artifacts: 'ci-production/**',
    diagnostics: '**/build/reports/**,*/run/logs/**,*/run/crash-reports/**,*/run/repair-smoke-result.txt'
)
