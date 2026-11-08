# Verification record

UI copy and dependency-range cleanup on 2026-11-08:

- Removed the fill percentage and per-point energy cost from the energy tooltip, and removed the sidebar's Shift-click hint. Transfer behavior is unchanged.
- OpenUI metadata now has a lower-only `[0.0.16,)` range on the five TOML-based targets; legacy 1.12.2 already has no upper version restriction. Development resolution remains pinned to 0.0.16.
- All eight workspace checks, all six builds and all six packaged-JAR inspections passed. Generated-metadata checks cover the uncapped range across every TOML-based target.
- Eight isolated real-client previews passed on NeoForge 1.21.1. Visually confirmed the three-line live energy tooltip and sidebar without the Shift-click hint; refreshed the saved screen and tooltip images in `docs/previews/`.

Texel-density correction on 2026-11-08:

- Replaced stretched circuit-panel mappings with matching-size texture crops. All 22 cuboids now use integer coordinates; all 132 faces have explicit UVs with exactly one 16×16-material texel per model unit on both axes.
- Eight workspace tests passed, including rejection of stretched UVs, fractional geometry and a mismatched texture resolution. Generation and packaged-JAR validation enforce the density rule for all six targets.
- All six builds and package inspections passed. The eight native client previews were refreshed and the updated baked model was visually inspected; `docs/previews/repair-model.png` contains the corrected view. Gameplay/server code was unchanged, so the previous native server acceptance checks were not repeated.

Station redesign verification on 2026-11-08:

- All six production builds and package checks passed. The custom model has 22 bounded cuboids, four 16×16 ImageGen material PNGs, four placement orientations and native creative-tab registration. Package checks verify the material dimensions, menu/screen classes and OpenUI dependency, and reject bundled framework or development-preview classes.
- All seven workspace checks passed. All six isolated native server probes passed with JEI and each target's power-generation mod enabled, but OpenUI excluded at runtime. The new menu probes verify exact 32-bit synchronization through signed-short properties, shift-click insertion/removal, and rejection of non-equipment. Existing recipe, energy, redstone, item-data and persistence checks also passed.
- Eight isolated NeoForge 1.21.1 client previews passed in a copied test world: repairing, empty, no power, redstone pause, completed, energy tooltip, item tooltip and baked block-item model. Actual screenshots were inspected; the stationary-pointer tooltip updates from 73,500 to 72,123 FE in the fixture. The final screen and model previews are saved under `docs/previews/`.
- Client appearance was checked on NeoForge 1.21.1. These previews use production screens with sample synchronized menu data; they do not establish physical-input behavior, live multiplayer behavior, shader compatibility or a real generator/cable connection. Existing running clients need a restart to load the redesigned screen and model.

Development environment verification on 2026-11-08:

- All six development environments include JEI and a power-generation mod. Powah remains enabled on Forge 1.16.5/1.20.1 and NeoForge 1.21.1/26.1.2; Forge 1.12.2 uses Solar Flux Reborn 12.4.11 and NeoForge 26.2 uses Energized Power 3.0.7.
- All seven workspace checks passed. Both changed environments passed native server probes with their development mods enabled; this checks successful loading and the station's native repair behavior, not a real generator-to-station connection.
- Launched the NeoForge 1.21.1 client with JEI and Powah. Client initialization reached resource loading and a native game window opened. Visual verification was stopped by the user's Escape key; no interactive repair or cable-network result is claimed.
- The build launcher passes discovered local JDK paths to Gradle so launch works even with stale machine-wide toolchain paths and auto-detection disabled.

Branding verification on 2026-11-08:

- The final gradient-background wrench-and-lightning PNG project icon is 1,424,037 bytes, below the 2 MB limit. All seven workspace checks passed and all six generated modules contain identical icon bytes with matching metadata references.
- All six production module builds and package inspections passed during the earlier icon integration. The final graphic has been refreshed in generated resources; existing built JARs need rebuilding to include this latest revision.
- Mod-list display was verified through generated metadata and packaged assets; it has not been visually checked in a running client.

Recipe verification on 2026-11-08:

- All seven workspace checks passed with the updated recipe on all six targets.
- All six native dedicated-server probes passed. Both book slots accept Mending I books and reject ordinary books, empty enchanted books and Unbreaking-only books. These runs used `devMods=false`.
- Forge 1.12.2 recipes now use the legacy `assets/<mod_id>/recipes` directory, explicit anvil metadata, and development resources beside the mod classes so the native loader can discover them.

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

The original baseline used Minecraft's five-slot hopper screen; the custom OpenUI screen above supersedes it. A real Powah cable network remains outside the automated probes, which exercise the loader energy capability directly.

CurseForge publishing is configured but has not been executed. Final mod identity, CurseForge project ID and upload credentials are still required. Workflow checks are visible under [GitHub Actions](https://github.com/UpperMoon0/Powered-Repair/actions).
