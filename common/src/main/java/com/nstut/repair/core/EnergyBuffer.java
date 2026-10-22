package com.nstut.repair.core;

public final class EnergyBuffer implements RepairEngine.Power {
    private final int capacity;
    private final Runnable changed;
    private int energy;
    public EnergyBuffer(int capacity, Runnable changed) { this.capacity = capacity; this.changed = changed; }
    public int capacity() { return capacity; }
    @Override public int stored() { return energy; }
    public int receive(int amount, boolean simulate) {
        int accepted = Math.min(Math.max(0, amount), capacity - energy);
        if (!simulate && accepted > 0) { energy += accepted; changed.run(); }
        return accepted;
    }
    public void restore(int amount) { energy = Math.max(0, Math.min(capacity, amount)); }
    @Override public void consume(int amount) {
        if (amount < 0 || amount > energy) throw new IllegalArgumentException("Invalid energy consumption");
        if (amount > 0) { energy -= amount; changed.run(); }
    }
}
