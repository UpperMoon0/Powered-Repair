# Powered Repair

A Minecraft mod that repairs damaged equipment using energy. The **Repair Station** has five slots, supports item automation, and can be paused with redstone.

[CurseForge description](curseforge.md) · [GitHub releases](https://github.com/UpperMoon0/Powered-Repair/releases) · [Issues](https://github.com/UpperMoon0/Powered-Repair/issues)

## How it works

1. Craft a Repair Station using the recipe below.
2. Place it and connect a compatible energy source to any side.
3. Open the station and insert damaged tools, weapons, or armor.
4. Take the repaired items out, or use a hopper or compatible pipe to automate input and output.

```text
I B I
R A R
I B I
```

`I` = iron ingot, `B` = Mending I enchanted book, `R` = redstone dust, `A` = anvil.

Both books must have Mending. For Forge 1.12.2 and 1.16.5, use unrenamed books with only Mending because those recipes require exact item data.

By default, the station stores **100,000 energy**, consumes **100 energy per durability point**, and restores **one point per tick across all five slots**. It rotates between damaged items so one item does not take all the repairs. Repairing changes only durability; enchantments, custom names, and other item data remain unchanged.

A redstone signal pauses repairs. Hoppers and compatible pipes can insert damaged items, but automated extraction only takes fully repaired items. The station accepts energy from every face and does not output it. Its inventory and energy survive world reloads; breaking the block drops its items but loses its stored energy.

Only items using the standard Minecraft durability system are supported by default. Items with custom energy, charge, or damage systems need a separate integration.

## Supported versions

| Loader | Minecraft | Game Java |
| --- | --- | --- |
| Forge | 1.12.2 | 8 |
| Forge | 1.16.5 | 8 |
| Forge | 1.20.1 | 17 |
| NeoForge | 1.21.1 | 21 |
| NeoForge | 26.1.2 | 25 |
| NeoForge | 26.2 | 25 |

Install the matching Powered Repair JAR on client and server.

**OpenUI MC 0.0.16+ is required on clients**, with a matching Minecraft version and loader. It is not bundled in Powered Repair; dedicated servers do not require the UI mod. JEI and Powah are optional. Supply energy through a mod compatible with your loader's energy API.

The development environments include JEI and a power-generation mod for testing. Where Powah is unavailable, Forge 1.12.2 uses Solar Flux Reborn and NeoForge 26.2 uses Energized Power. None of these test utilities are included in released JARs; see [`dev-mods.lock.json`](dev-mods.lock.json) for exact development dependencies. A working connection to every third-party cable network has not been tested.

## Configuration

Settings are stored in `config/powered_repair.properties`. Restart the game or server after editing.

| Property | Default | Description |
| --- | --- | --- |
| `capacity` | `100000` | Energy the station can store |
| `energyPerPoint` | `100` | Energy used per durability point |
| `pointsPerTick` | `1` | Total durability restored per tick |
| `blacklist` | Empty | Comma-separated item IDs to exclude |
| `whitelist` | Empty | Optional comma-separated item IDs to allow |

An empty whitelist permits all normally repairable items; blacklisted IDs are always excluded. `capacity` must be at least `energyPerPoint`, and all three numeric settings must be positive.

## Building and testing

`common/` contains the shared repair engine, energy accounting, scheduling, and filters. Each Forge/NeoForge module compiles the same shared behavior with an adapter for its Minecraft version. Generated resources and mod metadata come from `gradle.properties`, `targets.json`, `tools/generate.py`, and `templates/`.

Each loader module has its own Gradle wrapper. Use the module-specific JDK listed above; Forge 1.16.5 launches Gradle with Java 17 while targeting Java 8 for the game.

```sh
# Shared behavior tests
./gradlew :common:test

# Build one production target, or all six
python tools/build.py forge-1.20.1
python tools/build.py all

# Development client with test dependencies
python tools/build.py neoforge-1.21.1 runClient

# Native server acceptance for one version
python tools/smoke.py forge-1.20.1

# Isolated UI previews (NeoForge 1.21.1)
python tools/preview.py
```

On Windows, the root Gradle launcher is `gradlew.bat`. Build tools accept version-specific `JAVA_HOME_8_X64`, `JAVA_HOME_17_X64`, and `JAVA_HOME_21_X64` (or `JAVA8_HOME`-style alternatives). Use `-PdevMods=false` on an individual module wrapper to skip development utilities.

For screenshots and model implementation details, see [the UI documentation](docs/station-design.md). For what has actually been tested, see [the verification record](VERIFICATION.md).

## Releases

Powered Repair `0.1.0` is available as a **Release** for six supported versions. [View the published JARs and checksums](https://github.com/UpperMoon0/Powered-Repair/releases/tag/v0.1.0).

CI and publication are managed in [NsTut-CICD](https://github.com/UpperMoon0/NsTut-CICD). A reviewed release request pins the source commit, successful Jenkins build, version, and release channel. Publication checks the build and artifact hashes, then publishes the six corresponding files to CurseForge project **1791835** and GitHub. Builds do not publish just because a commit or tag appears.

The publisher keeps per-file receipts and blocks duplicate uploads after an uncertain response. See the [release process](https://github.com/UpperMoon0/NsTut-CICD/blob/main/jenkins/minecraft-mods/releases.md) for maintenance details.
