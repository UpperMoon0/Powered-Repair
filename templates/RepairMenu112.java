package com.nstut.repair;

import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.entity.player.InventoryPlayer;
import net.minecraft.inventory.*;
import net.minecraft.item.ItemStack;

public final class RepairMenu extends Container {
    public static final int WIDTH=284,HEIGHT=238;
    private final RepairMod.Machine machine;
    private final int[] values=new int[9],previous=new int[9];
    public RepairMenu(InventoryPlayer inventory,RepairMod.Machine machine) {
        this.machine=machine;
        java.util.Arrays.fill(previous,-1);
        for(int i=0;i<5;i++) addSlotToContainer(new Slot(machine,i,24+40*i,70) {
            @Override public boolean isItemValid(ItemStack stack) { return stack.isItemStackDamageable() && stack.isItemDamaged() && RepairMod.SETTINGS.allows(stack.getItem().getRegistryName().toString()); }
            @Override public int getSlotStackLimit() { return 1; }
        });
        for(int row=0;row<3;row++) for(int col=0;col<9;col++) addSlotToContainer(new Slot(inventory,col+row*9+9,16+col*18,145+row*18));
        for(int col=0;col<9;col++) addSlotToContainer(new Slot(inventory,col,16+col*18,205));
    }
    private int current(int i) {
        if(i==8) return machine.getWorld()!=null && machine.getWorld().isBlockPowered(machine.getPos())?1:0;
        int n=i<2?machine.power.stored():i<4?RepairMod.SETTINGS.capacity:i<6?RepairMod.SETTINGS.energyPerPoint:RepairMod.SETTINGS.pointsPerTick;
        return (n >>> ((i&1)*16))&65535;
    }
    @Override public void addListener(IContainerListener listener) {
        super.addListener(listener);
        for(int i=0;i<9;i++) listener.sendWindowProperty(this,i,current(i));
    }
    @Override public void detectAndSendChanges() {
        super.detectAndSendChanges();
        for(int i=0;i<9;i++) {
            int n=current(i); values[i]=n;
            if(n!=previous[i]) for(IContainerListener listener:listeners) listener.sendWindowProperty(this,i,n);
            previous[i]=n;
        }
    }
    @Override public void updateProgressBar(int id,int value) { if(id>=0 && id<9) values[id]=value&65535; }
    private int value(int i) { return (values[i]&65535)|((values[i+1]&65535)<<16); }
    public int energy() { return value(0); } public int capacity() { return value(2); }
    public int cost() { return value(4); } public int rate() { return value(6); }
    public boolean paused() { return values[8]!=0; }
    public int durability(int slot) {
        ItemStack stack=machine.getStackInSlot(slot);
        if(stack.isEmpty() || stack.getMaxDamage()<=0)return -1;
        return (int)Math.max(0,Math.min(100,100L*(stack.getMaxDamage()-stack.getItemDamage())/stack.getMaxDamage()));
    }
    public String status() {
        if(paused())return "paused";
        int present=0,damaged=0;
        for(int i=0;i<5;i++) { ItemStack s=machine.getStackInSlot(i); if(!s.isEmpty())present++;if(!s.isEmpty()&&s.isItemDamaged())damaged++; }
        if(present==0)return "empty";if(damaged==0)return "ready";return energy()<cost()?"unpowered":"working";
    }
    @Override public boolean canInteractWith(EntityPlayer player) { return machine.isUsableByPlayer(player); }
    @Override public ItemStack transferStackInSlot(EntityPlayer player,int index) {
        Slot slot=inventorySlots.get(index);
        if(!slot.getHasStack())return ItemStack.EMPTY;
        ItemStack original=slot.getStack(),copy=original.copy();
        if(index<5) { if(!mergeItemStack(original,5,41,true))return ItemStack.EMPTY; }
        else if(!mergeItemStack(original,0,5,false)) {
            if(index<32) { if(!mergeItemStack(original,32,41,false))return ItemStack.EMPTY; }
            else if(!mergeItemStack(original,5,32,false))return ItemStack.EMPTY;
        }
        if(original.isEmpty())slot.putStack(ItemStack.EMPTY);else slot.onSlotChanged();
        if(original.getCount()==copy.getCount())return ItemStack.EMPTY;
        slot.onTake(player,original);return copy;
    }
}
