"""Opt-in native adapter acceptance probe, run only in isolated development servers."""

def modern_probe(cfg):
    new = cfg['minecraft'].startswith('26.')
    neo = cfg['loader'] == 'neoforge'
    lookup = cfg['minecraft'] == '1.21.1' or new
    ns = 'net.neoforged.neoforge' if neo else 'net.minecraftforge'
    source = '''package com.nstut.repair;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import @NS@.event.server.ServerStartedEvent;
public final class NativeSmoke {
    public static void run(ServerStartedEvent event) {
        try {
            var level = event.getServer().overworld();
            var pos = new BlockPos(0, 90, 0);
            level.setBlockAndUpdate(pos, RepairMod.BLOCK.get().defaultBlockState());
            var machine = (RepairMachine)level.getBlockEntity(pos);
            check(machine != null, "block entity registration");
            var tool = new ItemStack(Items.DIAMOND_PICKAXE);
            tool.setDamageValue(10);
            @NAME@
            machine.setItem(0, tool);
            check(machine.canPlaceItemThroughFace(1,tool,Direction.UP), "automation insertion");
            check(!machine.canTakeItemThroughFace(0,tool,Direction.DOWN), "no premature extraction");
            @POWER@
            int stored = machine.power.stored();
            level.setBlockAndUpdate(pos.east(), Blocks.REDSTONE_BLOCK.defaultBlockState());
            machine.tick();
            check(tool.getDamageValue()==10 && machine.power.stored()==stored, "redstone pause");
            level.removeBlock(pos.east(),false);
            machine.tick();
            check(tool.getDamageValue()==9 && machine.power.stored()==stored-RepairMod.SETTINGS.energyPerPoint, "repair cost");
            check(tool.getHoverName().getString().equals("Preserved name"), "item data preservation");
            @SAVE@
            check(restored instanceof RepairMachine, "saved block entity factory");
            var loaded = (RepairMachine)restored;
            check(loaded.power.stored()==machine.power.stored(), "saved energy");
            check(loaded.getItem(0).getDamageValue()==9 && loaded.getItem(0).getHoverName().getString().equals("Preserved name"), "saved item state");
            for(int i=0;i<9;i++) machine.tick();
            check(tool.getDamageValue()==0 && machine.canTakeItemThroughFace(0,tool,Direction.DOWN), "completion extraction");
            String report="NATIVE_REPAIR_SMOKE_PASS @MC@";
            Files.write(Paths.get("repair-smoke-result.txt"),report.getBytes(StandardCharsets.UTF_8));
            System.out.println(report);
        } catch(Throwable error) {
            error.printStackTrace();
            System.err.println("NATIVE_REPAIR_SMOKE_FAIL @MC@");
        } finally { event.getServer().halt(false); }
    }
    private static void check(boolean valid,String message) { if(!valid) throw new AssertionError(message); }
}
'''
    name = 'tool.set(net.minecraft.core.component.DataComponents.CUSTOM_NAME, net.minecraft.network.chat.Component.literal("Preserved name"));' if lookup else 'tool.setHoverName(net.minecraft.network.chat.Component.literal("Preserved name"));'
    if new:
        power = '''var energy=level.getCapability(net.neoforged.neoforge.capabilities.Capabilities.Energy.BLOCK,pos,Direction.NORTH);
            check(energy != null,"native energy capability");
            try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()) { energy.insert(1000,tx); }
            check(machine.power.stored()==0,"transaction rollback");
            try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()) {
                energy.insert(100,tx);
                try(var nested=net.neoforged.neoforge.transfer.transaction.Transaction.open(tx)) { energy.insert(200,nested); nested.commit(); }
            }
            check(machine.power.stored()==0,"nested transaction rollback");
            try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()) { energy.insert(1000,tx); tx.commit(); }
            check(machine.power.stored()==1000,"transaction commit");
            check(energy.extract(100,null)==0,"receive only");
            check(level.getCapability(net.neoforged.neoforge.capabilities.Capabilities.Item.BLOCK,pos,Direction.DOWN)!=null,"native item capability");'''
    elif neo:
        power = '''var energy=level.getCapability(net.neoforged.neoforge.capabilities.Capabilities.EnergyStorage.BLOCK,pos,Direction.NORTH);
            check(energy != null,"native energy capability");
            energy.receiveEnergy(1000,true); check(machine.power.stored()==0,"energy simulation");
            energy.receiveEnergy(1000,false); check(energy.extractEnergy(100,false)==0,"receive only");
            check(level.getCapability(net.neoforged.neoforge.capabilities.Capabilities.ItemHandler.BLOCK,pos,Direction.DOWN)!=null,"native item capability");'''
    else:
        power = '''var energy=machine.getCapability(net.minecraftforge.common.capabilities.ForgeCapabilities.ENERGY,Direction.NORTH).orElseThrow(()->new AssertionError("native energy capability"));
            energy.receiveEnergy(1000,true); check(machine.power.stored()==0,"energy simulation");
            energy.receiveEnergy(1000,false); check(energy.extractEnergy(100,false)==0,"receive only");
            check(machine.getCapability(net.minecraftforge.common.capabilities.ForgeCapabilities.ITEM_HANDLER,Direction.DOWN).isPresent(),"native item capability");'''
    save = 'var saved=machine.saveWithFullMetadata('+('level.registryAccess()' if lookup else '')+');\n            var restored=BlockEntity.loadStatic(pos,machine.getBlockState(),saved'+(',level.registryAccess()' if lookup else '')+');'
    for key,value in {'NS':ns,'NAME':name,'POWER':power,'SAVE':save,'MC':cfg['minecraft']}.items():
        source=source.replace('@'+key+'@',value)
    return source
