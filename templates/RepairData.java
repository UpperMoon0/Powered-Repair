package com.nstut.repair;
import net.minecraft.world.inventory.ContainerData;

/** Vanilla menu properties are signed shorts on the wire; preserve every bit of int settings. */
public final class RepairData implements ContainerData {
    private final RepairMachine machine;
    public RepairData(RepairMachine machine) { this.machine = machine; }
    @Override public int get(int index) {
        if (index == 8) return machine.getLevel() != null && machine.getLevel().hasNeighborSignal(machine.getBlockPos()) ? 1 : 0;
        int number = index < 2 ? machine.power.stored() : index < 4 ? RepairMod.SETTINGS.capacity
            : index < 6 ? RepairMod.SETTINGS.energyPerPoint : RepairMod.SETTINGS.pointsPerTick;
        return (number >>> ((index & 1) * 16)) & 65535;
    }
    @Override public void set(int index, int value) { }
    @Override public int getCount() { return 9; }
}
