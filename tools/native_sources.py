"""Small API adapters. All repair, filtering and energy arithmetic lives in common/."""
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[1] / 'templates'

def sources(cfg, family):
    if family == '112':
        return {'RepairMod.java': (TEMPLATES / 'legacy112.java').read_text()}
    if family == '116':
        return legacy116(cfg)
    return modern(cfg)

def modern(cfg):
    neo = cfg['loader'] == 'neoforge'
    new = cfg['minecraft'].startswith('26.')
    lookup = cfg['minecraft'] == '1.21.1'
    ns = 'net.neoforged.neoforge' if neo else 'net.minecraftforge'
    fml = 'net.neoforged.fml' if neo else 'net.minecraftforge.fml'
    bus = 'net.neoforged.bus' if neo else 'net.minecraftforge.eventbus'
    register = 'net.minecraft.core.registries.Registries' if neo else ns+'.registries.ForgeRegistries'
    keys = ('Registries.BLOCK', 'Registries.ITEM', 'Registries.BLOCK_ENTITY_TYPE') if neo else ('ForgeRegistries.BLOCKS', 'ForgeRegistries.ITEMS', 'ForgeRegistries.BLOCK_ENTITY_TYPES')
    mod = '''package com.nstut.repair;
import java.io.File;
import java.util.function.Supplier;
import java.util.Set;
import com.nstut.repair.core.RepairSettings;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.BlockItem;
import @REGISTER@;
import @NS@.registries.DeferredRegister;
import @FML@.common.Mod;
import @BUS@.api.IEventBus;
@CAP_IMPORT@
@Mod(RepairMod.ID)
public final class RepairMod {
    public static final String ID = "@ID@";
    public static final RepairSettings SETTINGS = RepairSettings.load(new File("config", ID + ".properties"));
    private static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(@BLOCKS@, ID);
    private static final DeferredRegister<Item> ITEMS = DeferredRegister.create(@ITEMS@, ID);
    private static final DeferredRegister<BlockEntityType<?>> ENTITIES = DeferredRegister.create(@ENTITIES@, ID);
    public static final Supplier<RepairBlock> BLOCK = BLOCKS.register("repair_station", () -> new RepairBlock(@BLOCK_PROPERTIES@));
    public static final Supplier<Item> ITEM = ITEMS.register("repair_station", () -> new BlockItem(BLOCK.get(), @ITEM_PROPERTIES@));
    public static final Supplier<BlockEntityType<RepairMachine>> MACHINE = ENTITIES.register("repair_station", () -> @BE_FACTORY@);
    public RepairMod(@CONSTRUCTOR_ARG@) {
        @GET_BUS@
        BLOCKS.register(bus); ITEMS.register(bus); ENTITIES.register(bus);
        @CAP_LISTENER@
    }
    @CAP_METHOD@
}
'''
    block = '''package com.nstut.repair;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.*;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.phys.BlockHitResult;
@BLOCK_IMPORTS@
public final class RepairBlock extends BaseEntityBlock {
    public RepairBlock(Properties properties) { super(properties); }
    @CODEC@
    @Override public BlockEntity newBlockEntity(BlockPos pos, BlockState state) { return new RepairMachine(pos, state); }
    @Override public RenderShape getRenderShape(BlockState state) { return RenderShape.MODEL; }
    @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return @IS_CLIENT@ ? null : createTickerHelper(type, RepairMod.MACHINE.get(), (l,p,s,be) -> be.tick());
    }
    @USE_SIGNATURE@ {
        if (!@IS_CLIENT@ && level.getBlockEntity(pos) instanceof RepairMachine) player.openMenu((RepairMachine) level.getBlockEntity(pos));
        return InteractionResult.SUCCESS;
    }
    @REMOVE@
}
'''
    machine = '''package com.nstut.repair;
import com.nstut.repair.core.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.NonNullList;
import net.minecraft.network.chat.Component;
import net.minecraft.world.*;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.HopperMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.core.registries.BuiltInRegistries;
@SAVE_IMPORTS@
@ENERGY_IMPORTS@
public final class RepairMachine extends BlockEntity implements WorldlyContainer, MenuProvider, RepairEngine.Inventory {
    private NonNullList<ItemStack> items = NonNullList.withSize(5, ItemStack.EMPTY);
    private final RepairEngine engine = new RepairEngine();
    public final EnergyBuffer power = new EnergyBuffer(RepairMod.SETTINGS.capacity, this::setChanged);
    @ENERGY_FIELDS@
    public RepairMachine(BlockPos pos, BlockState state) { super(RepairMod.MACHINE.get(), pos, state); }
    public void tick() {
        if (level == null || @BE_IS_CLIENT@) return;
        if (engine.tick(this, power, RepairMod.SETTINGS, level.hasNeighborSignal(worldPosition)) > 0) setChanged();
    }
    @SAVE_METHODS@
    @Override public int getContainerSize() { return 5; }
    @Override public boolean isEmpty() { for (ItemStack stack : items) if (!stack.isEmpty()) return false; return true; }
    @Override public ItemStack getItem(int slot) { return items.get(slot); }
    @Override public ItemStack removeItem(int slot, int count) {
        ItemStack result = ContainerHelper.removeItem(items, slot, count); if (!result.isEmpty()) setChanged(); return result;
    }
    @Override public ItemStack removeItemNoUpdate(int slot) { return ContainerHelper.takeItem(items, slot); }
    @Override public void setItem(int slot, ItemStack stack) { items.set(slot, stack); stack.setCount(Math.min(stack.getCount(), getMaxStackSize())); setChanged(); }
    @Override public int getMaxStackSize() { return 1; }
    @Override public boolean stillValid(Player player) { return level != null && level.getBlockEntity(worldPosition) == this && player.distanceToSqr(worldPosition.getX()+0.5,worldPosition.getY()+0.5,worldPosition.getZ()+0.5) <= 64; }
    @Override public void clearContent() { items.clear(); setChanged(); }
    @Override public boolean canPlaceItem(int slot, ItemStack stack) { return stack.getCount() == 1 && stack.isDamageableItem() && stack.isDamaged() && RepairMod.SETTINGS.allows(BuiltInRegistries.ITEM.getKey(stack.getItem()).toString()); }
    @Override public int[] getSlotsForFace(Direction side) { return new int[]{0,1,2,3,4}; }
    @Override public boolean canPlaceItemThroughFace(int slot, ItemStack stack, Direction side) { return canPlaceItem(slot, stack); }
    @Override public boolean canTakeItemThroughFace(int slot, ItemStack stack, Direction side) { return !stack.isDamaged(); }
    @Override public Component getDisplayName() { return Component.translatable("container.@ID@.repair_station"); }
    @Override public AbstractContainerMenu createMenu(int id, Inventory inventory, Player player) { return new HopperMenu(id, inventory, this); }
    @Override public int size() { return 5; }
    @Override public boolean repairable(int slot) { ItemStack s=items.get(slot); return !s.isEmpty() && s.getCount()==1 && s.isDamageableItem() && s.isDamaged(); }
    @Override public String itemId(int slot) { return BuiltInRegistries.ITEM.getKey(items.get(slot).getItem()).toString(); }
    @Override public int damage(int slot) { return items.get(slot).getDamageValue(); }
    @Override public void damage(int slot, int value) { items.get(slot).setDamageValue(value); }
    @CAP_METHODS@
}
'''
    if new:
        imports = '''import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;'''
        save = '''@Override protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input); items = NonNullList.withSize(5, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(input, items); power.restore(input.getIntOr("Energy", 0));
    }
    @Override protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output); ContainerHelper.saveAllItems(output, items); output.putInt("Energy", power.stored());
    }'''
    else:
        imports = 'import net.minecraft.nbt.CompoundTag;\n' + ('import net.minecraft.core.HolderLookup;' if lookup else '')
        lookup_arg = ', HolderLookup.Provider registries' if lookup else ''
        lookup_pass = ', registries' if lookup else ''
        save = f'''@Override {'protected' if lookup else 'public'} void {'loadAdditional' if lookup else 'load'}(CompoundTag tag{lookup_arg}) {{
        super.{'loadAdditional' if lookup else 'load'}(tag{lookup_pass}); items = NonNullList.withSize(5, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(tag, items{lookup_pass}); power.restore(tag.getInt("Energy"));
    }}
    @Override protected void saveAdditional(CompoundTag tag{lookup_arg}) {{
        super.saveAdditional(tag{lookup_pass}); ContainerHelper.saveAllItems(tag, items{lookup_pass}); tag.putInt("Energy", power.stored());
    }}'''
    if new:
        energy_imports = '''import net.neoforged.neoforge.transfer.energy.EnergyHandler;
import net.neoforged.neoforge.transfer.transaction.SnapshotJournal;
import net.neoforged.neoforge.transfer.transaction.TransactionContext;'''
        energy_fields = '''public final PowerCapability energy = new PowerCapability();
    public final class PowerCapability extends SnapshotJournal<Integer> implements EnergyHandler {
        @Override public long getAmountAsLong() { return power.stored(); }
        @Override public long getCapacityAsLong() { return power.capacity(); }
        @Override public int insert(int amount, TransactionContext transaction) {
            if (amount < 0) throw new IllegalArgumentException("Negative energy");
            updateSnapshots(transaction); return power.receive(amount, false);
        }
        @Override public int extract(int amount, TransactionContext transaction) { return 0; }
        @Override protected Integer createSnapshot() { return power.stored(); }
        @Override protected void revertToSnapshot(Integer snapshot) { power.restore(snapshot); }
        @Override protected void onRootCommit(Integer original) { if (original != power.stored()) setChanged(); }
    }'''
        caps = ''
    else:
        energy_imports = f'import {ns}.energy.IEnergyStorage;'
        energy_fields = '''public final IEnergyStorage energy = new IEnergyStorage() {
        public int receiveEnergy(int amount, boolean simulate) { return power.receive(amount, simulate); }
        public int extractEnergy(int amount, boolean simulate) { return 0; }
        public int getEnergyStored() { return power.stored(); }
        public int getMaxEnergyStored() { return power.capacity(); }
        public boolean canExtract() { return false; }
        public boolean canReceive() { return true; }
    };'''
        caps = ''
        if not neo:
            energy_imports += f'''
import {ns}.common.util.LazyOptional;
import {ns}.common.capabilities.Capability;
import {ns}.common.capabilities.ForgeCapabilities;
import {ns}.items.IItemHandler;
import {ns}.items.wrapper.SidedInvWrapper;'''
            energy_fields += '''
    private LazyOptional<IEnergyStorage> energyCap = LazyOptional.of(() -> energy);
    private LazyOptional<IItemHandler> itemCap = LazyOptional.of(() -> new SidedInvWrapper(this, Direction.DOWN));'''
            caps = '''@Override public <T> LazyOptional<T> getCapability(Capability<T> cap, Direction side) {
        if (!isRemoved()) {
            if (cap == ForgeCapabilities.ENERGY) return energyCap.cast();
            if (cap == ForgeCapabilities.ITEM_HANDLER) return itemCap.cast();
        }
        return super.getCapability(cap, side);
    }
    @Override public void invalidateCaps() { super.invalidateCaps(); energyCap.invalidate(); itemCap.invalidate(); }
    @Override public void reviveCaps() {
        super.reviveCaps(); energyCap = LazyOptional.of(() -> energy);
        itemCap = LazyOptional.of(() -> new SidedInvWrapper(this, Direction.DOWN));
    }'''
    cap_import = f'import {ns}.capabilities.RegisterCapabilitiesEvent;\nimport {ns}.capabilities.Capabilities;' if neo else ''
    item_cap = 'new net.neoforged.neoforge.transfer.item.WorldlyContainerWrapper(be, side)' if new else 'new net.neoforged.neoforge.items.wrapper.SidedInvWrapper(be, side == null ? net.minecraft.core.Direction.DOWN : side)'
    replacements = {
        'REGISTER': register, 'NS': ns, 'FML': fml, 'BUS': bus, 'BLOCKS':keys[0], 'ITEMS':keys[1], 'ENTITIES':keys[2],
        'BLOCK_PROPERTIES': 'BlockBehaviour.Properties.ofFullCopy(Blocks.IRON_BLOCK).setId(net.minecraft.resources.ResourceKey.create(Registries.BLOCK, net.minecraft.resources.Identifier.fromNamespaceAndPath(ID, "repair_station")))' if new else 'BlockBehaviour.Properties.of().strength(3.5F)',
        'ITEM_PROPERTIES': 'new Item.Properties().setId(net.minecraft.resources.ResourceKey.create(Registries.ITEM, net.minecraft.resources.Identifier.fromNamespaceAndPath(ID, "repair_station")))' if new else 'new Item.Properties()',
        'BE_FACTORY': 'new BlockEntityType<>(RepairMachine::new, Set.of(BLOCK.get()))' if new else 'BlockEntityType.Builder.of(RepairMachine::new, BLOCK.get()).build(null)',
        'CONSTRUCTOR_ARG': 'IEventBus bus' if neo else '',
        'GET_BUS': '' if neo else 'IEventBus bus = net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext.get().getModEventBus();',
        'CAP_IMPORT':cap_import, 'CAP_LISTENER':'bus.addListener(RepairMod::capabilities);' if neo else '',
        'CAP_METHOD': f'''private static void capabilities(RegisterCapabilitiesEvent event) {{
        event.registerBlockEntity(Capabilities.Energy{' ' if new else 'Storage '}.BLOCK, MACHINE.get(), (be, side) -> be.energy);
        event.registerBlockEntity(Capabilities.{'Item' if new else 'ItemHandler'}.BLOCK, MACHINE.get(), (be, side) -> {item_cap});
    }}'''.replace(' .BLOCK','.BLOCK') if neo else '',
        'BLOCK_IMPORTS': 'import com.mojang.serialization.MapCodec;' if neo else 'import net.minecraft.world.InteractionHand;',
        'CODEC': '@Override protected MapCodec<? extends BaseEntityBlock> codec() { return simpleCodec(RepairBlock::new); }' if neo else '',
        'USE_SIGNATURE': '@Override protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit)' if neo else '@Override public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit)',
        'IS_CLIENT': 'level.isClientSide()' if new else 'level.isClientSide',
        'BE_IS_CLIENT': 'level.isClientSide()' if new else 'level.isClientSide',
        'REMOVE': '' if new else '''@Override public void onRemove(BlockState state, Level level, BlockPos pos, BlockState replacement, boolean moving) {
        if (!state.is(replacement.getBlock())) {
            BlockEntity be = level.getBlockEntity(pos);
            if (be instanceof RepairMachine) net.minecraft.world.Containers.dropContents(level, pos, (RepairMachine) be);
        }
        super.onRemove(state, level, pos, replacement, moving);
    }''',
        'SAVE_IMPORTS':imports, 'SAVE_METHODS':save, 'ENERGY_IMPORTS':energy_imports, 'ENERGY_FIELDS':energy_fields, 'CAP_METHODS':caps,
    }
    result = {'RepairMod.java':mod, 'RepairBlock.java':block, 'RepairMachine.java':machine}
    for key, value in replacements.items():
        result = {name:text.replace('@'+key+'@',value) for name,text in result.items()}
    return result

def legacy116(cfg):
    # Official 1.16.5 mappings retain older package/class names. Keep gameplay methods identical.
    result = modern(dict(cfg, minecraft='1.20.1'))
    replacements = {
        'net.minecraft.core.BlockPos':'net.minecraft.util.math.BlockPos',
        'net.minecraft.core.Direction':'net.minecraft.util.Direction',
        'net.minecraft.core.NonNullList':'net.minecraft.util.NonNullList',
        'net.minecraft.network.chat.Component':'net.minecraft.util.text.ITextComponent',
        'net.minecraft.world.entity.player.Inventory':'net.minecraft.entity.player.PlayerInventory',
        'net.minecraft.world.entity.player.Player':'net.minecraft.entity.player.PlayerEntity',
        'net.minecraft.world.inventory.AbstractContainerMenu':'net.minecraft.inventory.container.Container',
        'net.minecraft.world.inventory.HopperMenu':'net.minecraft.inventory.container.HopperContainer',
        'net.minecraft.world.item.ItemStack':'net.minecraft.item.ItemStack',
        'net.minecraft.world.item.Item':'net.minecraft.item.Item',
        'net.minecraft.world.item.BlockItem':'net.minecraft.item.BlockItem',
        'net.minecraft.world.level.block.entity.*':'net.minecraft.tileentity.*',
        'net.minecraft.world.level.block.entity.BlockEntityType':'net.minecraft.tileentity.TileEntityType',
        'net.minecraft.world.level.block.entity.BlockEntity':'net.minecraft.tileentity.TileEntity',
        'net.minecraft.world.level.block.state.BlockState':'net.minecraft.block.BlockState',
        'net.minecraft.world.level.block.state.BlockBehaviour':'net.minecraft.block.AbstractBlock',
        'net.minecraft.world.level.block.BaseEntityBlock':'net.minecraft.block.ContainerBlock',
        'net.minecraft.world.level.block.RenderShape':'net.minecraft.block.BlockRenderType',
        'net.minecraft.world.level.block.Blocks':'net.minecraft.block.Blocks',
        'net.minecraft.world.level.block.Block':'net.minecraft.block.Block',
        'net.minecraft.world.level.Level':'net.minecraft.world.World',
        'net.minecraft.world.InteractionResult':'net.minecraft.util.ActionResultType',
        'net.minecraft.world.InteractionHand':'net.minecraft.util.Hand',
        'net.minecraft.world.phys.BlockHitResult':'net.minecraft.util.math.BlockRayTraceResult',
        'net.minecraft.nbt.CompoundTag':'net.minecraft.nbt.CompoundNBT',
        'import net.minecraft.core.registries.BuiltInRegistries;':'import net.minecraftforge.registries.ForgeRegistries;',
        'import net.minecraft.world.*;':'import net.minecraft.inventory.*;\nimport net.minecraft.inventory.container.INamedContainerProvider;\nimport net.minecraft.util.text.TranslationTextComponent;',
        'import net.minecraftforge.common.capabilities.ForgeCapabilities;':'import net.minecraftforge.energy.CapabilityEnergy;\nimport net.minecraftforge.items.CapabilityItemHandler;',
        'ForgeCapabilities.ENERGY':'CapabilityEnergy.ENERGY', 'ForgeCapabilities.ITEM_HANDLER':'CapabilityItemHandler.ITEM_HANDLER_CAPABILITY',
        'BuiltInRegistries.ITEM':'ForgeRegistries.ITEMS',
        'BlockBehaviour':'AbstractBlock', 'BlockEntityType':'TileEntityType', 'BlockEntity':'TileEntity',
        'BaseEntityBlock':'ContainerBlock', 'RenderShape':'BlockRenderType',
        'new RepairMachine(pos, state)':'new RepairMachine()',
        'BlockBehaviour.Properties.of()':'AbstractBlock.Properties.of(net.minecraft.block.material.Material.METAL)',
        'AbstractBlock.Properties.of()':'AbstractBlock.Properties.of(net.minecraft.block.material.Material.METAL)',
        'Component.translatable':'new TranslationTextComponent',
        'WorldlyContainer':'ISidedInventory', 'MenuProvider':'INamedContainerProvider',
        'AbstractContainerMenu':'Container', 'HopperMenu':'HopperContainer',
        'Inventory inventory':'PlayerInventory inventory', 'Player player':'PlayerEntity player',
        'Component getDisplayName':'ITextComponent getDisplayName',
        'CompoundTag':'CompoundNBT', 'InteractionResult':'ActionResultType', 'InteractionHand':'Hand',
        'BlockHitResult':'BlockRayTraceResult', 'Level level':'World level',
        'ContainerHelper':'ItemStackHelper',
        'super(RepairMod.MACHINE.get(), pos, state)':'super(RepairMod.MACHINE.get())',
        'public RepairMachine(BlockPos pos, BlockState state)':'public RepairMachine()',
        'public void tick()':'@Override public void tick()',
        'RepairEngine.Inventory {':'RepairEngine.Inventory, ITickableTileEntity {',
        'net.minecraft.world.Containers.dropContents':'net.minecraft.inventory.InventoryHelper.dropContents',
        'public void load(CompoundNBT tag)':'public void load(BlockState state, CompoundNBT tag)',
        'super.load(tag)':'super.load(state, tag)',
        'protected void saveAdditional(CompoundNBT tag)':'public CompoundNBT save(CompoundNBT tag)',
        'super.saveAdditional(tag)':'super.save(tag)',
        'tag.putInt("Energy", power.stored());':'tag.putInt("Energy", power.stored()); return tag;',
        'isRemoved()':'isRemoved()',
    }
    for key,value in replacements.items():
        result = {name:text.replace(key,value) for name,text in result.items()}
    # 1.16 ticks the tile itself and creates it through EntityBlock's older signature.
    block = result['RepairBlock.java']
    start = block.index('    @Override public <T extends TileEntity>')
    end = block.index('    @Override public ActionResultType use', start)
    block = block[:start] + block[end:]
    block = block.replace('public TileEntity newTileEntity(BlockPos pos, BlockState state)', 'public TileEntity newBlockEntity(net.minecraft.world.IBlockReader world)')
    result['RepairBlock.java'] = block
    result = {name: text.replace('getTileEntity(', 'getBlockEntity(')
              .replace('getBlockRenderType(', 'getRenderShape(')
              .replace('ForgeRegistries.BLOCK_ENTITY_TYPES', 'ForgeRegistries.TILE_ENTITIES')
              .replace('import net.minecraft.tileentity.TileEntity;', 'import net.minecraft.tileentity.TileEntity;\nimport net.minecraft.tileentity.ITickableTileEntity;')
              for name, text in result.items()}
    return result
