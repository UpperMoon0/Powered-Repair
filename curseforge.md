# Powered Repair

**Turn spare energy into repaired equipment.** Powered Repair adds a dedicated repair station with five equipment slots. Connect power, drop in damaged gear, and let the station restore its durability while you work on something else.

## Features

- **Five equipment slots:** repair tools, weapons, armor and other eligible equipment, with work rotating fairly between damaged items.
- **Energy-powered repairs:** configurable energy cost, repair speed and internal energy storage.
- **Keep your gear's identity:** repairs preserve names, enchantments and other item data; only durability damage changes.
- **Automate the process:** hoppers and compatible item pipes can insert damaged equipment and extract fully repaired items.
- **Redstone control:** power the station with a redstone signal to pause repairs.
- **Pack-friendly filters:** use item whitelists and blacklists to control which equipment can be repaired.
- **Modded equipment:** items using Minecraft's standard durability system are eligible too. Custom durability or charge systems may need a dedicated integration.

## Getting Started

1. Craft a **Repair Station** using the recipe below.
2. Place it and connect a compatible energy source or cable to any face.
3. Right-click to open the station and insert damaged equipment.
4. Collect your repaired gear manually, or use a hopper or compatible pipe for automation.

By default, the station stores **100,000 energy** and restores **one durability point per tick across the station**, at **100 energy per point**. With sufficient power, that is 20 durability points per second at normal tick speed. It receives energy but does not supply energy to other blocks.

## Crafting Recipe

```text
Iron Ingot    Mending I Book    Iron Ingot
Redstone      Anvil             Redstone
Iron Ingot    Mending I Book    Iron Ingot
```

**Total:** 4 iron ingots, 2 redstone dust, 1 anvil and **2 Mending I enchanted books**.

Both book slots require Mending; ordinary books and books with other enchantments instead of Mending do not work. Use books containing only Mending for compatibility with every supported version. Forge 1.12.2 and 1.16.5 require exact book NBT, so use unrenamed books without extra item data on those versions.

## Supported Platforms

| Mod Loader | Minecraft Versions |
| --- | --- |
| Forge | 1.12.2, 1.16.5, 1.20.1 |
| NeoForge | 1.21.1, 26.1.2, 26.2 |

Choose the file matching your Minecraft version and loader. Install the matching mod on both the client and server when playing multiplayer. Fabric is not supported.

## Dependencies and Compatibility

Powered Repair requires its matching Forge or NeoForge loader. **JEI and Powah are optional**, and neither is bundled with the mod. Supply power from a mod that exposes the energy API supported by your chosen loader version.

Standard durability is the compatibility boundary: a modded item looking damaged does not guarantee it uses that system. Equipment powered by charge or a separate custom durability mechanic is not automatically supported. Specific cable networks and client visuals have not yet been verified; see the [verification record](https://github.com/UpperMoon0/Powered-Repair/blob/main/VERIFICATION.md) for the current test coverage.

## Configuration

Settings are stored in `config/powered_repair.properties`. Restart the game or server after editing.

| Setting | Default | Purpose |
| --- | --- | --- |
| `capacity` | `100000` | Internal energy storage |
| `energyPerPoint` | `100` | Energy consumed per durability point |
| `pointsPerTick` | `1` | Maximum durability restored per tick across the station |
| `blacklist` | Empty | Comma-separated item IDs to exclude |
| `whitelist` | Empty | Optional comma-separated list of allowed item IDs |

An empty whitelist allows all otherwise eligible equipment. The blacklist always takes priority.

The station saves its inventory and stored energy across world reloads. Breaking it drops the equipment inside, but its stored energy is lost.

## Support

- [Report bugs or request features](https://github.com/UpperMoon0/Powered-Repair/issues)
- [Browse the source](https://github.com/UpperMoon0/Powered-Repair)

Created by **NsTut**.
