package com.nstut.repair;

import com.nstut.repair.core.*;
import java.io.File;
import net.minecraft.block.Block;
import net.minecraft.block.material.Material;
import net.minecraft.block.state.IBlockState;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.entity.player.InventoryPlayer;
import net.minecraft.inventory.*;
import net.minecraft.item.Item;
import net.minecraft.item.ItemBlock;
import net.minecraft.item.ItemStack;
import net.minecraft.nbt.NBTTagCompound;
import net.minecraft.tileentity.TileEntity;
import net.minecraft.util.*;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.text.*;
import net.minecraft.world.World;
import net.minecraft.world.IInteractionObject;
import net.minecraftforge.common.capabilities.Capability;
import net.minecraftforge.energy.*;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.common.event.FMLPreInitializationEvent;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;
import net.minecraftforge.event.RegistryEvent;
import net.minecraftforge.fml.common.registry.GameRegistry;
import net.minecraftforge.items.*;
import net.minecraftforge.items.wrapper.SidedInvWrapper;

@Mod(modid=RepairMod.ID, name="@NAME@", version="@VERSION@", acceptedMinecraftVersions="[1.12.2]")
@Mod.EventBusSubscriber(modid=RepairMod.ID)
public final class RepairMod {
    public static final String ID = "@ID@";
    public static RepairSettings SETTINGS = RepairSettings.defaults();
    public static final Station BLOCK = (Station) new Station().setRegistryName(ID, "repair_station").setTranslationKey(ID+".repair_station");
    @Mod.EventHandler public void init(FMLPreInitializationEvent event) {
        SETTINGS = RepairSettings.load(new File(event.getModConfigurationDirectory(), ID+".properties"));
        GameRegistry.registerTileEntity(Machine.class, new ResourceLocation(ID, "repair_station"));
    }
    @SubscribeEvent public static void blocks(RegistryEvent.Register<Block> event) { event.getRegistry().register(BLOCK); }
    @SubscribeEvent public static void items(RegistryEvent.Register<Item> event) { event.getRegistry().register(new ItemBlock(BLOCK).setRegistryName(BLOCK.getRegistryName())); }
    @Mod.EventHandler public void started(net.minecraftforge.fml.common.event.FMLServerStartedEvent event) {
        if (!"1".equals(System.getenv("POWERED_REPAIR_SMOKE"))) return;
        net.minecraft.server.MinecraftServer server=net.minecraftforge.fml.common.FMLCommonHandler.instance().getMinecraftServerInstance();
        try {
            World world=server.getWorld(0); BlockPos pos=new BlockPos(0,90,0);
            world.setBlockState(pos,BLOCK.getDefaultState());
            Machine machine=(Machine)world.getTileEntity(pos);
            if(machine==null) throw new AssertionError("block entity registration");
            ItemStack tool=new ItemStack(net.minecraft.init.Items.DIAMOND_PICKAXE);
            tool.setItemDamage(10); tool.setStackDisplayName("Preserved name"); machine.setInventorySlotContents(0,tool);
            if(!machine.canInsertItem(1,tool,EnumFacing.UP) || machine.canExtractItem(0,tool,EnumFacing.DOWN)) throw new AssertionError("automation rules");
            IEnergyStorage energy=machine.getCapability(CapabilityEnergy.ENERGY,EnumFacing.NORTH);
            if(energy==null || !machine.hasCapability(CapabilityItemHandler.ITEM_HANDLER_CAPABILITY,EnumFacing.DOWN)) throw new AssertionError("native capabilities");
            energy.receiveEnergy(1000,true);
            if(machine.power.stored()!=0) throw new AssertionError("energy simulation");
            energy.receiveEnergy(1000,false);
            if(energy.extractEnergy(100,false)!=0) throw new AssertionError("receive only");
            world.setBlockState(pos.east(),net.minecraft.init.Blocks.REDSTONE_BLOCK.getDefaultState());
            machine.update();
            if(tool.getItemDamage()!=10 || machine.power.stored()!=1000) throw new AssertionError("redstone pause");
            world.setBlockToAir(pos.east()); machine.update();
            if(tool.getItemDamage()!=9 || machine.power.stored()!=900 || !tool.getDisplayName().equals("Preserved name")) throw new AssertionError("repair accounting and item data");
            TileEntity restored=TileEntity.create(world,machine.writeToNBT(new NBTTagCompound()));
            if(!(restored instanceof Machine)) throw new AssertionError("saved block entity factory");
            Machine loaded=(Machine)restored;
            if(loaded.power.stored()!=900 || loaded.getStackInSlot(0).getItemDamage()!=9 || !loaded.getStackInSlot(0).getDisplayName().equals("Preserved name")) throw new AssertionError("saved energy and item data");
            for(int i=0;i<9;i++) machine.update();
            if(tool.getItemDamage()!=0 || !machine.canExtractItem(0,tool,EnumFacing.DOWN)) throw new AssertionError("completion extraction");
            java.nio.file.Files.write(java.nio.file.Paths.get("repair-smoke-result.txt"),"NATIVE_REPAIR_SMOKE_PASS 1.12.2".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            System.out.println("NATIVE_REPAIR_SMOKE_PASS 1.12.2");
        } catch(Throwable error) { error.printStackTrace(); System.err.println("NATIVE_REPAIR_SMOKE_FAIL 1.12.2"); }
        finally { server.initiateShutdown(); }
    }
    @Mod.EventBusSubscriber(modid=RepairMod.ID, value=net.minecraftforge.fml.relauncher.Side.CLIENT)
    public static final class Client {
        @SubscribeEvent public static void models(net.minecraftforge.client.event.ModelRegistryEvent event) {
            net.minecraftforge.client.model.ModelLoader.setCustomModelResourceLocation(Item.getItemFromBlock(BLOCK), 0,
                new net.minecraft.client.renderer.block.model.ModelResourceLocation(BLOCK.getRegistryName(), "inventory"));
        }
    }
    public static final class Station extends Block {
        public Station() { super(Material.IRON); setHardness(3.5F); }
        @Override public boolean hasTileEntity(IBlockState state) { return true; }
        @Override public TileEntity createTileEntity(World world, IBlockState state) { return new Machine(); }
        @Override public boolean onBlockActivated(World world, BlockPos pos, IBlockState state, EntityPlayer player, EnumHand hand, EnumFacing side, float x, float y, float z) {
            if (!world.isRemote && world.getTileEntity(pos) instanceof Machine) player.displayGUIChest((Machine)world.getTileEntity(pos));
            return true;
        }
        @Override public void breakBlock(World world, BlockPos pos, IBlockState state) {
            TileEntity tile = world.getTileEntity(pos);
            if (tile instanceof Machine) InventoryHelper.dropInventoryItems(world, pos, (Machine)tile);
            super.breakBlock(world, pos, state);
        }
    }
    public static final class Machine extends TileEntity implements ISidedInventory, IInteractionObject, ITickable, RepairEngine.Inventory {
        private NonNullList<ItemStack> items = NonNullList.withSize(5, ItemStack.EMPTY);
        private final RepairEngine engine = new RepairEngine();
        public final EnergyBuffer power = new EnergyBuffer(SETTINGS.capacity, this::markDirty);
        private final IItemHandler handler = new SidedInvWrapper(this, EnumFacing.DOWN);
        private final IEnergyStorage energy = new IEnergyStorage() {
            public int receiveEnergy(int amount, boolean simulate) { return power.receive(amount, simulate); }
            public int extractEnergy(int amount, boolean simulate) { return 0; }
            public int getEnergyStored() { return power.stored(); }
            public int getMaxEnergyStored() { return power.capacity(); }
            public boolean canReceive() { return true; }
            public boolean canExtract() { return false; }
        };
        @Override public void update() {
            if (world == null || world.isRemote) return;
            if (engine.tick(this, power, SETTINGS, world.isBlockPowered(pos)) > 0) markDirty();
        }
        @Override public void readFromNBT(NBTTagCompound tag) {
            super.readFromNBT(tag); items=NonNullList.withSize(5,ItemStack.EMPTY);
            ItemStackHelper.loadAllItems(tag, items); power.restore(tag.getInteger("Energy"));
        }
        @Override public NBTTagCompound writeToNBT(NBTTagCompound tag) {
            super.writeToNBT(tag); ItemStackHelper.saveAllItems(tag,items); tag.setInteger("Energy",power.stored()); return tag;
        }
        @Override public boolean hasCapability(Capability<?> cap, EnumFacing side) {
            return !isInvalid() && (cap == CapabilityEnergy.ENERGY || cap == CapabilityItemHandler.ITEM_HANDLER_CAPABILITY) || super.hasCapability(cap,side);
        }
        @Override public <T> T getCapability(Capability<T> cap, EnumFacing side) {
            if (!isInvalid()) {
                if (cap == CapabilityEnergy.ENERGY) return CapabilityEnergy.ENERGY.cast(energy);
                if (cap == CapabilityItemHandler.ITEM_HANDLER_CAPABILITY) return CapabilityItemHandler.ITEM_HANDLER_CAPABILITY.cast(handler);
            }
            return super.getCapability(cap, side);
        }
        @Override public int getSizeInventory() { return 5; }
        @Override public boolean isEmpty() { for(ItemStack s:items) if(!s.isEmpty()) return false; return true; }
        @Override public ItemStack getStackInSlot(int slot) { return items.get(slot); }
        @Override public ItemStack decrStackSize(int slot,int amount) { ItemStack s=ItemStackHelper.getAndSplit(items,slot,amount); if(!s.isEmpty()) markDirty(); return s; }
        @Override public ItemStack removeStackFromSlot(int slot) { return ItemStackHelper.getAndRemove(items,slot); }
        @Override public void setInventorySlotContents(int slot,ItemStack stack) { items.set(slot,stack); stack.setCount(Math.min(stack.getCount(),1)); markDirty(); }
        @Override public int getInventoryStackLimit() { return 1; }
        @Override public boolean isUsableByPlayer(EntityPlayer p) { return world.getTileEntity(pos)==this && p.getDistanceSq(pos.getX()+0.5,pos.getY()+0.5,pos.getZ()+0.5)<=64; }
        @Override public void openInventory(EntityPlayer p) {}
        @Override public void closeInventory(EntityPlayer p) {}
        @Override public boolean isItemValidForSlot(int slot,ItemStack s) { return s.getCount()==1 && s.isItemStackDamageable() && s.isItemDamaged() && SETTINGS.allows(s.getItem().getRegistryName().toString()); }
        @Override public int getField(int id) { return 0; }
        @Override public void setField(int id,int value) {}
        @Override public int getFieldCount() { return 0; }
        @Override public void clear() { items.clear(); markDirty(); }
        @Override public int[] getSlotsForFace(EnumFacing side) { return new int[]{0,1,2,3,4}; }
        @Override public boolean canInsertItem(int slot,ItemStack s,EnumFacing side) { return isItemValidForSlot(slot,s); }
        @Override public boolean canExtractItem(int slot,ItemStack s,EnumFacing side) { return !s.isItemDamaged(); }
        @Override public String getName() { return "container.@ID@.repair_station"; }
        @Override public boolean hasCustomName() { return false; }
        @Override public ITextComponent getDisplayName() { return new TextComponentTranslation(getName()); }
        @Override public String getGuiID() { return "minecraft:hopper"; }
        @Override public Container createContainer(InventoryPlayer inventory,EntityPlayer p) { return new ContainerHopper(inventory,this,p); }
        @Override public int size() { return 5; }
        @Override public boolean repairable(int slot) { ItemStack s=items.get(slot); return !s.isEmpty() && s.getCount()==1 && s.isItemStackDamageable() && s.isItemDamaged(); }
        @Override public String itemId(int slot) { return items.get(slot).getItem().getRegistryName().toString(); }
        @Override public int damage(int slot) { return items.get(slot).getItemDamage(); }
        @Override public void damage(int slot,int value) { items.get(slot).setItemDamage(value); }
    }
}
