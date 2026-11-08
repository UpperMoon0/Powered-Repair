# Powered Repair (working name)

A small mod focused on one machine: an energy-powered equipment repair station.

The project name and `powered_repair` ID are temporary. Set the final identity in `gradle.properties` before making a release. No releases are published while `identity_final=false`.

The shared mod and CurseForge icon is [`icon.png`](icon.png). The generator packages it in every loader's assets and references it from the mod metadata. The ready-to-copy CurseForge front page is [`curseforge.md`](curseforge.md).

## Gameplay

Craft the station with four iron ingots, two redstone dust, an anvil, and two Mending I enchanted books:

```text
I B I
R A R
I B I
```

`I` = iron ingot, `R` = redstone dust, `A` = anvil, `B` = Mending I enchanted book.
Ordinary books and books without Mending do not work. Use books containing only Mending
for compatibility with every supported version; Forge 1.12.2 and 1.16.5 require exact book NBT.

Connect an energy source and right-click the station to open its five equipment slots. It restores one durability point per tick for 100 energy by default, sharing work fairly between damaged items. Names, enchantments and other item data are preserved: only damage changes. A redstone signal pauses repairs. The machine receives energy on every face and does not supply energy to other blocks.

Hoppers and compatible pipes insert damaged equipment and extract repaired items. Players can remove items at any time. Breaking the station drops its contents; stored energy is lost. Equipment using nonstandard durability systems may require an integration and can be excluded through the blacklist.

The station has a custom, player-facing workbench model with four 16×16 materials and its own **Powered Repair** creative tab. Its OpenUI screen provides five real repair slots, the full player inventory and hotbar, shift-click transfers, live repair status, and an energy gauge with a live tooltip showing stored energy, capacity, repair speed and input faces. Existing repair rules and automation remain shared across all six versions.

Clients require **OpenUI MC 0.0.16 or newer (no upper version limit)**, matching their Minecraft version and loader. Development builds resolve the pinned 0.0.16 release automatically; OpenUI is not bundled in this mod's JAR. Dedicated servers do not need the client UI dependency.

Settings are in `config/<mod_id>.properties`: `capacity`, `energyPerPoint`, `pointsPerTick`, `blacklist`, and `whitelist`. Restart after editing. An empty whitelist allows all otherwise eligible items. The blacklist takes priority.

## Targets and development utilities

| Module | Game Java | JEI | Powah |
| --- | --- | --- | --- |
| `forge-1.12.2` | 8 | Included in development | Solar Flux Reborn 12.4.11 instead |
| `forge-1.16.5` | 8 | Included in development | 2.3.16 with Lollipop |
| `forge-1.20.1` | 17 | Included in development | 5.0.11 |
| `neoforge-1.21.1` | 21 | Included in development | 6.2.10 |
| `neoforge-26.1.2` | 25 | Included in development | 7.0.4 alpha |
| `neoforge-26.2` | 25 | Included in development | Energized Power 3.0.7 instead |

There are no Fabric targets. Every development environment includes JEI and a power-generation mod. Powah is used where compatible; Solar Flux Reborn supplies Forge 1.12.2 and Energized Power supplies NeoForge 26.2. These development utilities are never bundled or required by the shipped mod. Exact upstream files and transitive requirements are recorded in `dev-mods.lock.json`. Refresh deliberately with `python tools/lock_dev_mods.py`.

## Workspace

`common/` owns repair scheduling, filtering, settings and energy accounting in Java 8. All six modules compile those same sources. `tools/native_sources.py` and `templates/` contain the loader and Minecraft API adapters; generated code lives under each module's ignored `build/` directory. Recipes, models, translations and loader metadata are generated from the same identity and recipe definition by `tools/generate.py`.

Each loader module has its own Gradle wrapper so Forge 1.12.2 can retain Gradle 5/Java 8 without constraining modern NeoForge. Open the root and individual modules together in your IDE.

```sh
# Shared behavior tests
./gradlew :common:test
# Build one module or every module
python tools/build.py forge-1.20.1
python tools/build.py all
# Development client, with JEI and compatible Powah enabled
python tools/build.py neoforge-1.21.1 runClient
# Eight real-client screen/model previews in an isolated copied test world
python tools/preview.py
```

Use `gradlew.bat` on Windows. `tools/build.py` honors `JAVA_HOME_8_X64`, `JAVA_HOME_17_X64`, `JAVA_HOME_21_X64` (or `JAVA8_HOME`, etc.) when switching Gradle launchers. Gradle toolchains provision the game compiler for modern modules. Forge 1.16.5 uses Java 17 for Gradle and Java 8 for the game. Pass `-PdevMods=false` directly to a module wrapper for a production-only dependency graph.

## CI and releases

Jenkins orchestration and release publication are centralized in [NsTut-CICD](https://github.com/UpperMoon0/NsTut-CICD). The repository's Jenkinsfile delegates to `nstutPoweredRepair()`. Reviewed main builds run shared tests, cross-version resource/package checks and all six native server acceptance probes, preserving verified production JARs separately from development test builds.

The CurseForge project is **1791835** ([author dashboard](https://authors.curseforge.com/#/projects/1791835/files)). The final mod identity is `powered_repair` / Powered Repair. OpenUI is a required CurseForge relation; development utilities are excluded.

Publication requires a reviewed request in `jenkins/artifacts/mod-releases.json` in NsTut-CICD: the exact source SHA, successful Jenkins build number, version and release channel. Ordinary pushes and tags do not publish. The host verifies broker success, all six accepted artifact hashes, source identity/version and versioned changelog before creating a GitHub draft and uploading the matching files to CurseForge. It makes the GitHub release public after all six uploads return confirmed IDs.

The publishing token comes from `nstutcommonkv/curseforge-api-token`, never build agents or repository files. SHA-256 checksums and durable per-file receipts support recovery; an uncertain upload blocks retries until inspected. See the centralized [release guide](https://github.com/UpperMoon0/NsTut-CICD/blob/main/jenkins/minecraft-mods/powered-repair/README.md). No files have been published by this setup change.

Compilation and CI results do not establish visual quality or third-party runtime compatibility. Native client checks are tracked separately in the repository's verification notes.
