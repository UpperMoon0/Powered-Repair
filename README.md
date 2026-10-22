# Powered Repair (working name)

A small mod focused on one machine: an energy-powered equipment repair station.

The project name and `powered_repair` ID are temporary. Set the final identity in `gradle.properties` before making a release. No releases are published while `identity_final=false`.

## Gameplay

Craft the station with six iron ingots, two redstone dust, and an anvil:

```text
I I I
R A R
I I I
```

Connect an energy source and right-click the station to open its five equipment slots. It restores one durability point per tick for 100 energy by default, sharing work fairly between damaged items. Names, enchantments and other item data are preserved: only damage changes. A redstone signal pauses repairs. The machine receives energy on every face and does not supply energy to other blocks.

Hoppers and compatible pipes insert damaged equipment and extract repaired items. Players can remove items at any time. Breaking the station drops its contents; stored energy is lost. Equipment using nonstandard durability systems may require an integration and can be excluded through the blacklist.

Settings are in `config/<mod_id>.properties`: `capacity`, `energyPerPoint`, `pointsPerTick`, `blacklist`, and `whitelist`. Restart after editing. An empty whitelist allows all otherwise eligible items. The blacklist takes priority.

## Targets and development utilities

| Module | Game Java | JEI | Powah |
| --- | --- | --- | --- |
| `forge-1.12.2` | 8 | Included in development | No upstream release |
| `forge-1.16.5` | 8 | Included in development | 2.3.16 with Lollipop |
| `forge-1.20.1` | 17 | Included in development | 5.0.11 |
| `neoforge-1.21.1` | 21 | Included in development | 6.2.10 |
| `neoforge-26.1.2` | 25 | Included in development | 7.0.4 alpha |
| `neoforge-26.2` | 25 | Included in development | No compatible upstream release found |

There are no Fabric targets. JEI and Powah are development utilities, never bundled or required by the shipped mod. Exact upstream files and transitive requirements are recorded in `dev-mods.lock.json`. Refresh deliberately with `python tools/lock_dev_mods.py`.

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
```

Use `gradlew.bat` on Windows. `tools/build.py` honors `JAVA_HOME_8_X64`, `JAVA_HOME_17_X64`, `JAVA_HOME_21_X64` (or `JAVA8_HOME`, etc.) when switching Gradle launchers. Gradle toolchains provision the game compiler for modern modules. Forge 1.16.5 uses Java 17 for Gradle and Java 8 for the game. Pass `-PdevMods=false` directly to a module wrapper for a production-only dependency graph.

## CI and releases

Every push and pull request runs shared tests, cross-version resource/package checks, and builds all six loader artifacts. Release tags use `v<mod_version>` and must match `gradle.properties`. The release workflow waits for the full build matrix before creating a draft GitHub release and uploading to CurseForge. It publishes the GitHub release after all six CurseForge uploads return confirmed file IDs.

Before the first release:

1. Set `mod_id`, `mod_name` and `identity_final=true` in `gradle.properties`.
2. Create the CurseForge mod project and set repository variable `CURSEFORGE_PROJECT_ID` to its numeric ID.
3. Configure repository secret `CURSEFORGE_API_TOKEN`.
4. Add versioned notes under `changelog/<mod_version>.md`, then push a matching version tag.

Release uploads default to alpha. The workflow supports alpha, beta and release for manual runs on a version tag. Upload receipts and SHA-256 hashes are kept with the draft release. A retry skips confirmed uploads and refuses to repeat an upload whose outcome is uncertain.

Compilation and CI results do not establish visual quality or third-party runtime compatibility. Native client checks are tracked separately in the repository's verification notes.
