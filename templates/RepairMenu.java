package com.nstut.repair;

import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.*;
import net.minecraft.world.item.ItemStack;

/** Real vanilla slots and data slots: no client inventory or energy authority. */
public final class RepairMenu extends AbstractContainerMenu {
    public static final int WIDTH = 284, HEIGHT = 238;
    private final Container equipment;
    private final ContainerData data;
    public RepairMenu(int id, Inventory inventory) {
        this(id, inventory, new SimpleContainer(5), new SimpleContainerData(9));
    }
    public RepairMenu(int id, Inventory inventory, Container equipment, ContainerData data) {
        super(RepairMod.MENU.get(), id);
        this.equipment = equipment;
        this.data = data;
        checkContainerSize(equipment, 5);
        checkContainerDataCount(data, 9);
        for (int i = 0; i < 5; i++) addSlot(new Slot(equipment, i, 24 + 40 * i, 70) {
            @Override public boolean mayPlace(ItemStack stack) {
                return stack.isDamageableItem() && stack.isDamaged()
                    && RepairMod.SETTINGS.allows(@ITEM_ID@);
            }
            @Override public int getMaxStackSize() { return 1; }
        });
        for (int row = 0; row < 3; row++) for (int col = 0; col < 9; col++)
            addSlot(new Slot(inventory, col + row * 9 + 9, 16 + col * 18, 145 + row * 18));
        for (int col = 0; col < 9; col++) addSlot(new Slot(inventory, col, 16 + col * 18, 205));
        addDataSlots(data);
    }
    private int value(int index) { return (data.get(index) & 65535) | ((data.get(index + 1) & 65535) << 16); }
    public int energy() { return value(0); }
    public int capacity() { return value(2); }
    public int cost() { return value(4); }
    public int rate() { return value(6); }
    public boolean paused() { return data.get(8) != 0; }
    public int durability(int slot) {
        ItemStack stack=equipment.getItem(slot);
        if(stack.isEmpty() || stack.getMaxDamage()<=0) return -1;
        return (int)Math.max(0,Math.min(100,100L*(stack.getMaxDamage()-stack.getDamageValue())/stack.getMaxDamage()));
    }
    public String status() {
        if (paused()) return "paused";
        int present = 0, damaged = 0;
        for (int i = 0; i < 5; i++) {
            ItemStack item = equipment.getItem(i);
            if (!item.isEmpty()) present++;
            if (!item.isEmpty() && item.isDamaged()) damaged++;
        }
        if (present == 0) return "empty";
        if (damaged == 0) return "ready";
        return energy() < cost() ? "unpowered" : "working";
    }
    @Override public boolean stillValid(Player player) { return equipment.stillValid(player); }
    @Override public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem()) return ItemStack.EMPTY;
        ItemStack original = slot.getItem(), copy = original.copy();
        if (index < 5) {
            if (!moveItemStackTo(original, 5, 41, true)) return ItemStack.EMPTY;
        } else if (!moveItemStackTo(original, 0, 5, false)) {
            if (index < 32) {
                if (!moveItemStackTo(original, 32, 41, false)) return ItemStack.EMPTY;
            } else if (!moveItemStackTo(original, 5, 32, false)) return ItemStack.EMPTY;
        }
        if (original.isEmpty()) slot.set(ItemStack.EMPTY); else slot.setChanged();
        if (original.getCount() == copy.getCount()) return ItemStack.EMPTY;
        slot.onTake(player, original);
        return copy;
    }
}
