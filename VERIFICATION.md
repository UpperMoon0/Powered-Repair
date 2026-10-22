# Verification record

Local verification on 2026-10-23:

- All six production modules compiled and their JAR identity, shared core classes, bytecode level and absence of bundled dependencies were checked.
- Eight shared Java behavior tests passed: exact cost, round-robin scheduling, insufficient power, redstone pause, invalid/completed items, filters, overflow bounds and simulation/persistence bounds.
- Seven workspace checks passed, covering target scope, generated recipe parity, identity propagation/rename cleanup, provisional-release blocking, and development dependency separation.
- All six isolated native dedicated-server probes passed with development utilities enabled.

| Target | JEI | Powah | Native repair probe |
| --- | --- | --- | --- |
| Forge 1.12.2 | Loaded | Unavailable upstream | Passed |
| Forge 1.16.5 | Loaded | Loaded with Lollipop | Passed |
| Forge 1.20.1 | Loaded | Loaded | Passed |
| NeoForge 1.21.1 | Loaded | Loaded | Passed |
| NeoForge 26.1.2 | Loaded | Loaded | Passed |
| NeoForge 26.2 | Loaded | No compatible upstream release | Passed |

Native probes check block/entity registration, energy and item capability lookup, simulated energy insertion, receive-only energy, redstone pause, exact repair cost, preserved custom item name, saved-block factory/inventory/energy reload, and extraction after completion. The 26.x probes additionally check aborted root transactions, nested transaction rollback and successful commit.

Probe reports live in each module's ignored `run/repair-smoke-result.txt`. Reproduce with `DEV_SMOKE=true python tools/smoke.py <target>` (set the environment variable with your shell's syntax). Each probe owns its module's development `run/` directory and uses a local-only server with an automatically assigned port. Production servers do not run these probes.

The Forge 1.12.2 development launcher uses the pinned MCP merge helper from Simply Speakers' requested-generation port. This avoids the known obsolete merge configuration that breaks Forge's network initialization. Its resolver has a build-time negative-control check, and it changes no game access flags.

The machine menu uses Minecraft's five-slot hopper screen. Native client appearance, interactive menu behavior and a real Powah cable network have not been visually tested. The server probes exercise the loader energy capability directly.

CurseForge publishing is configured but has not been executed. Final mod identity, CurseForge project ID and upload credentials are still required. Workflow checks are visible under [GitHub Actions](https://github.com/UpperMoon0/Powered-Repair/actions).
