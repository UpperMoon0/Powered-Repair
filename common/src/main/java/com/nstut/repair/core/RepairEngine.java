package com.nstut.repair.core;

/** The same repair and energy rules run on every Minecraft version. */
public final class RepairEngine {
    public interface Inventory {
        int size();
        boolean repairable(int slot);
        String itemId(int slot);
        int damage(int slot);
        void damage(int slot, int value);
    }
    public interface Power {
        int stored();
        void consume(int amount);
    }
    private int nextSlot;

    /** Repairs one item per tick; round robin prevents a damaged tool starving the others. */
    public int tick(Inventory inventory, Power power, RepairSettings settings, boolean paused) {
        if (paused || inventory.size() == 0) return 0;
        for (int offset = 0; offset < inventory.size(); offset++) {
            int slot = (nextSlot + offset) % inventory.size();
            if (!inventory.repairable(slot) || !settings.allows(inventory.itemId(slot))) continue;
            int points = Math.min(inventory.damage(slot), Math.min(settings.pointsPerTick, power.stored() / settings.energyPerPoint));
            if (points <= 0) continue;
            int cost = points * settings.energyPerPoint;
            power.consume(cost);
            inventory.damage(slot, inventory.damage(slot) - points);
            nextSlot = (slot + 1) % inventory.size();
            return points;
        }
        return 0;
    }
}
