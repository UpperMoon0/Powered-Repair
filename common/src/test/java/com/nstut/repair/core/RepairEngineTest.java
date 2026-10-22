package com.nstut.repair.core;

import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class RepairEngineTest {
    static class Items implements RepairEngine.Inventory {
        int[] damage = {10, 5, 0, 7, 1};
        boolean[] valid = {true, true, true, false, true};
        public int size() { return 5; }
        public boolean repairable(int slot) { return valid[slot]; }
        public String itemId(int slot) { return "test:item" + slot; }
        public int damage(int slot) { return damage[slot]; }
        public void damage(int slot, int value) { damage[slot] = value; }
    }
    final Items items = new Items();
    final EnergyBuffer power = new EnergyBuffer(100000, () -> {});
    final RepairEngine engine = new RepairEngine();
    final RepairSettings defaults = RepairSettings.defaults();
    @Test public void exactCostAndRoundRobin() {
        power.receive(300, false);
        for (int i = 0; i < 3; i++) assertEquals(1, engine.tick(items, power, defaults, false));
        assertArrayEquals(new int[]{9,4,0,7,0}, items.damage);
        assertEquals(0, power.stored());
    }
    @Test public void insufficientEnergyNeverRepairs() {
        power.receive(99, false);
        assertEquals(0, engine.tick(items, power, defaults, false));
        assertEquals(10, items.damage[0]); assertEquals(99, power.stored());
    }
    @Test public void redstonePauseConsumesNothing() {
        power.receive(1000, false);
        assertEquals(0, engine.tick(items, power, defaults, true));
        assertEquals(1000, power.stored());
    }
    @Test public void completedAndInvalidItemsConsumeNothing() {
        Arrays.fill(items.damage, 0); items.damage[3] = 7;
        power.receive(1000, false);
        assertEquals(0, engine.tick(items, power, defaults, false));
        assertEquals(1000, power.stored());
    }
    @Test public void blacklistOverridesWhitelist() {
        RepairSettings settings = new RepairSettings(100000, 100, 10,
            Collections.singleton("test:item0"), new HashSet<String>(Arrays.asList("test:item0", "test:item1")));
        power.receive(1000, false);
        assertEquals(5, engine.tick(items, power, settings, false));
        assertEquals(10, items.damage[0]); assertEquals(0, items.damage[1]); assertEquals(500, power.stored());
    }
    @Test public void largeRatesDoNotOverflowOrOverRepair() {
        RepairSettings settings = new RepairSettings(Integer.MAX_VALUE, Integer.MAX_VALUE, Integer.MAX_VALUE,
            Collections.<String>emptySet(), Collections.<String>emptySet());
        EnergyBuffer large = new EnergyBuffer(Integer.MAX_VALUE, () -> {});
        large.receive(Integer.MAX_VALUE, false);
        assertEquals(1, engine.tick(items, large, settings, false)); assertEquals(0, large.stored());
    }
    @Test public void simulationAndPersistenceClamp() {
        assertEquals(100000, power.receive(Integer.MAX_VALUE, true)); assertEquals(0, power.stored());
        power.restore(Integer.MAX_VALUE); assertEquals(100000, power.stored());
        power.restore(-1); assertEquals(0, power.stored()); assertEquals(0, power.receive(-1, false));
    }
    @Test(expected=IllegalArgumentException.class) public void zeroCostRejected() {
        new RepairSettings(100, 0, 1, Collections.<String>emptySet(), Collections.<String>emptySet());
    }
}
