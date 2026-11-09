# Powered Repair

Powered Repair adds a **Repair Station** that fixes damaged equipment using energy. Put up to five items in the station, connect a power source, and it repairs them automatically. No manual repair step is needed once it has power.

## Features

- **Five repair slots:** accepts damaged tools, weapons, armor, and other items that use Minecraft's normal durability system.
- **Energy-based repairs:** by default, the station uses 100 energy per durability point and repairs up to one point per tick **total**, shared between the occupied slots.
- **Item-safe repairs:** keeps enchantments, custom names, and other item data intact.
- **Hopper and pipe automation:** inserts eligible items and extracts them once fully repaired.
- **Redstone pause:** a redstone signal stops repairs without removing items.
- **Configurable operation:** adjust storage, energy consumption, repair speed, and item allow/block lists.

Items using custom charge or durability mechanics are not automatically supported.

## Getting started

Craft a Repair Station using this pattern:

```text
Iron Ingot   Mending I Book   Iron Ingot
Redstone     Anvil            Redstone
Iron Ingot   Mending I Book   Iron Ingot
```

The recipe requires **4 iron ingots, 2 redstone dust, 1 anvil, and 2 Mending I enchanted books**. Both books must have Mending; ordinary books will not work. For Forge 1.12.2 and 1.16.5, use unrenamed Mending-only books because those recipes check exact item data.

Place the station, supply energy through any side, and right-click it to insert damaged gear. You can take items out at any time. Hoppers or compatible pipes can automate loading and unloading; automated extraction waits until an item is fully repaired.

The station receives energy but does **not** send power to other blocks. It keeps its stored items and energy when the world is saved. Breaking the station drops the stored items, but loses the stored energy.

## Supported versions

| Loader | Minecraft |
| --- | --- |
| Forge | 1.12.2, 1.16.5, 1.20.1 |
| NeoForge | 1.21.1, 26.1.2, 26.2 |

Install the file for your loader and Minecraft version on both client and server.

**Client requirement:** [OpenUI MC](https://www.curseforge.com/minecraft/mc-mods/openui-mc) 0.0.16 or newer, for the matching loader and game version. Dedicated servers do not need OpenUI. JEI and Powah are optional and are not bundled. A compatible energy-producing mod is required to power the station.

## Configuration

Edit `config/powered_repair.properties` and restart the game or server to apply changes.

| Setting | Default | Effect |
| --- | --- | --- |
| `capacity` | `100000` | Internal energy storage |
| `energyPerPoint` | `100` | Energy used per durability point |
| `pointsPerTick` | `1` | Maximum durability repaired per tick across the station |
| `blacklist` | Empty | Comma-separated item IDs that cannot be repaired |
| `whitelist` | Empty | If set, only these item IDs can be repaired |

The blacklist takes priority over the whitelist.

## Support

[Report an issue](https://github.com/UpperMoon0/Powered-Repair/issues) · [Source code](https://github.com/UpperMoon0/Powered-Repair)

Made by NsTut.
