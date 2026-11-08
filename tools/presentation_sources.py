"""Native menus, creative tabs and OpenUI adapters for the shared station design."""
from pathlib import Path
import re

TEMPLATES = Path(__file__).resolve().parents[1] / 'templates'

def enhance(result, cfg):
    result['LiveTooltipComponent.java'] = (TEMPLATES/'LiveTooltipComponent.java').read_text()
    version = cfg['minecraft']
    if version == '1.12.2':
        return legacy112(result)
    old = version == '1.16.5'
    neo = cfg['loader'] == 'neoforge'
    new = version.startswith('26.')
    ns = 'net.neoforged.neoforge' if neo else 'net.minecraftforge'
    fml = 'net.neoforged.fml' if neo else 'net.minecraftforge.fml'
    bus = 'net.neoforged.bus' if neo else 'net.minecraftforge.eventbus'
    menu = (TEMPLATES/'RepairMenu.java').read_text().replace('@ITEM_ID@',
        'net.minecraftforge.registries.ForgeRegistries.ITEMS.getKey(stack.getItem()).toString()' if old else
        'net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(stack.getItem()).toString()')
    data = (TEMPLATES/'RepairData.java').read_text()
    screen = screen_source(version)
    menu_registry = 'net.minecraftforge.registries.ForgeRegistries.CONTAINERS' if old else 'net.minecraft.core.registries.Registries.MENU'
    menu_type = 'net.minecraft.inventory.container.ContainerType' if old else 'net.minecraft.world.inventory.MenuType'
    menu_factory = 'new '+menu_type+'<>(RepairMenu::new'+('' if old else ', net.minecraft.world.flag.FeatureFlags.VANILLA_SET')+')'
    registration = f'''private static final {ns}.registries.DeferredRegister<{menu_type}<?>> MENUS = {ns}.registries.DeferredRegister.create({menu_registry}, ID);
    public static final java.util.function.Supplier<{menu_type}<RepairMenu>> MENU = MENUS.register("repair_station", () -> {menu_factory});
    '''
    if old:
        registration += '''public static final net.minecraft.item.ItemGroup TAB = new net.minecraft.item.ItemGroup(ID) {
        @Override public net.minecraft.item.ItemStack makeIcon() { return new net.minecraft.item.ItemStack(ITEM.get()); }
    };
    '''
    else:
        registration += f'''private static final {ns}.registries.DeferredRegister<net.minecraft.world.item.CreativeModeTab> TABS = {ns}.registries.DeferredRegister.create(net.minecraft.core.registries.Registries.CREATIVE_MODE_TAB, ID);
    public static final java.util.function.Supplier<net.minecraft.world.item.CreativeModeTab> TAB = TABS.register("main", () -> net.minecraft.world.item.CreativeModeTab.builder()
        .title(net.minecraft.network.chat.Component.translatable("itemGroup.@ID@"))
        .icon(() -> new net.minecraft.world.item.ItemStack(ITEM.get()))
        .displayItems((parameters, output) -> output.accept(ITEM.get())).build());
    '''
    mod = result['RepairMod.java'].replace('    public RepairMod(', '    '+registration+'public RepairMod(')
    mod = mod.replace('ENTITIES.register(bus);', 'ENTITIES.register(bus); MENUS.register(bus);'+('' if old else ' TABS.register(bus);')+
        f'\n        if ({fml}.loading.FMLEnvironment.dist == {"net.neoforged.api.distmarker.Dist" if neo else "net.minecraftforge.api.distmarker.Dist"}.CLIENT) RepairClient.install(bus);')
    if old:
        # The group must exist before Item.Properties captures it.
        start = mod.index('    public static final net.minecraft.item.ItemGroup TAB')
        end = mod.index('    public RepairMod(', start)
        tab = mod[start:end]
        mod = mod[:start]+mod[end:]
        at = mod.index('    public static final Supplier<Item> ITEM')
        mod = mod[:at]+tab+mod[at:]
        mod = mod.replace('new Item.Properties()', 'new Item.Properties().tab(TAB)')
    if new:
        mod = mod.replace('FMLEnvironment.dist', 'FMLEnvironment.getDist()')
    result['RepairMod.java'] = mod
    result['RepairMachine.java'] = result['RepairMachine.java'].replace('new HopperMenu(id, inventory, this)',
        'new RepairMenu(id, inventory, this, new RepairData(this))').replace('new HopperContainer(id, inventory, this)',
        'new RepairMenu(id, inventory, this, new RepairData(this))')
    if old:
        replacements = {
            'net.minecraft.world.Container':'net.minecraft.inventory.IInventory',
            'net.minecraft.world.SimpleContainer':'net.minecraft.inventory.Inventory',
            'net.minecraft.world.entity.player.Inventory':'net.minecraft.entity.player.PlayerInventory',
            'net.minecraft.world.entity.player.Player':'net.minecraft.entity.player.PlayerEntity',
            'net.minecraft.world.inventory.*':'net.minecraft.inventory.container.*',
            'net.minecraft.world.inventory.ContainerData':'net.minecraft.util.IIntArray',
            'net.minecraft.world.item.ItemStack':'net.minecraft.item.ItemStack',
            'AbstractContainerMenu':'Container', 'ContainerData':'IIntArray', 'SimpleContainerData':'IntArray',
            'new SimpleContainer(':'new net.minecraft.inventory.Inventory(',
            'Container equipment':'IInventory equipment', 'Inventory inventory':'PlayerInventory inventory',
            'Player player':'PlayerEntity player',
        }
        for a,b in replacements.items():
            menu = menu.replace(a,b); data = data.replace(a,b)
        menu = menu.replace('new SimpleIIntArray(', 'new net.minecraft.util.IntArray(').replace('new IntArray(', 'new net.minecraft.util.IntArray(')
        menu = menu.replace('private final Container equipment;', 'private final IInventory equipment;')
        menu = menu.replace('checkIIntArrayCount', 'checkContainerDataCount')
        # IIntArray uses getCount() in the official mappings too.
        menu = menu.replace('import net.minecraft.inventory.container.*;', 'import net.minecraft.inventory.container.*;\nimport net.minecraft.inventory.container.Slot;\nimport net.minecraft.util.IIntArray;')
    result['RepairMenu.java'] = menu
    result['RepairData.java'] = data
    if neo:
        screen_registration = f'''private static void setup({ns}.client.event.RegisterMenuScreensEvent event) {{ event.register(RepairMod.MENU.get(), RepairScreen::new); }}'''
    elif old:
        screen_registration = f'''private static void setup({fml}.event.lifecycle.FMLClientSetupEvent event) {{ event.enqueueWork(() -> net.minecraft.client.gui.ScreenManager.register(RepairMod.MENU.get(), RepairScreen::new)); }}'''
    else:
        screen_registration = f'''private static void setup({fml}.event.lifecycle.FMLClientSetupEvent event) {{ event.enqueueWork(() -> net.minecraft.client.gui.screens.MenuScreens.register(RepairMod.MENU.get(), RepairScreen::new)); }}'''
    result['RepairClient.java'] = f'''package com.nstut.repair;
public final class RepairClient {{
    public static void install({bus}.api.IEventBus bus) {{ bus.addListener(RepairClient::setup); }}
    {screen_registration}
}}
'''
    result['RepairScreen.java'] = screen
    result['RepairBlock.java'] = facing_block(result['RepairBlock.java'], version)
    return result

def screen_source(version):
    old = version in ('1.12.2','1.16.5')
    new = version.startswith('26.')
    text = (TEMPLATES/'RepairScreen.java').read_text()
    values = {'SCREEN_SUPER': 'super(menu,inventory,title'+(',RepairMenu.WIDTH,RepairMenu.HEIGHT' if new else '')+');',
        'SCREEN_DIMENSIONS': '' if new else 'imageWidth=RepairMenu.WIDTH; imageHeight=RepairMenu.HEIGHT;',
        'SCREEN_LEFT':'leftPos','SCREEN_TOP':'topPos','SCREEN_FONT':'font',
        'LABEL_OVERRIDE':'@Override protected void renderLabels(GuiGraphics g,int mx,int my) { }'}
    if new:
        values['LABEL_OVERRIDE']='@Override protected void extractLabels(GuiGraphicsExtractor g,int mx,int my) { }'
        text=text.replace('GuiGraphics','GuiGraphicsExtractor')
    if old:
        text=text.replace('net.minecraft.client.gui.GuiGraphics','com.nstut.openui.graphics.LegacyGuiGraphics').replace('GuiGraphics','LegacyGuiGraphics')
        # The first replacement already added Legacy: avoid a doubled simple name.
        text=text.replace('LegacyLegacyGuiGraphics','LegacyGuiGraphics')
        text=text.replace('net.minecraft.network.chat.Component','net.minecraft.util.text.ITextComponent')
        text=text.replace('net.minecraft.world.entity.player.Inventory','net.minecraft.entity.player.PlayerInventory')
        text=text.replace('Inventory inventory','PlayerInventory inventory')
        text=re.sub(r'\bComponent\b','ITextComponent',text)
        text=text.replace('ITextComponent.translatable(', 'new net.minecraft.util.text.TranslationTextComponent(')
        if version=='1.12.2':
            text=text.replace('net.minecraft.entity.player.PlayerInventory','net.minecraft.entity.player.InventoryPlayer')
            text=text.replace('PlayerInventory inventory','InventoryPlayer inventory')
            text=text.replace('TranslationTextComponent','TextComponentTranslation')
            text=text.replace('net.minecraft.client.gui.Font','com.nstut.openui.compat.LegacyFont')
            text=text.replace('Font f','LegacyFont f')
            text=text.replace('.getString()', '.getUnformattedText()')
            values.update(SCREEN_DIMENSIONS='xSize=RepairMenu.WIDTH; ySize=RepairMenu.HEIGHT;',SCREEN_LEFT='guiLeft',SCREEN_TOP='guiTop',SCREEN_FONT='com.nstut.openui.compat.LegacyFont.current()',
                LABEL_OVERRIDE='@Override protected void drawGuiContainerForegroundLayer(int mx,int my) { }')
        else:
            text=text.replace('net.minecraft.client.gui.Font','net.minecraft.client.gui.FontRenderer').replace('Font f','FontRenderer f')
            values['LABEL_OVERRIDE']='@Override protected void renderLabels(com.mojang.blaze3d.matrix.MatrixStack g,int mx,int my) { }'
    for k,v in values.items(): text=text.replace('@'+k+'@',v)
    # A compact unit label fits the energy card in every translation.
    text=text.replace('label("energy").getString(),x+238','"FE",x+247')
    return text

def facing_block(text, version):
    text=text.replace('super(properties);', 'super(properties); registerDefaultState(stateDefinition.any().setValue(FACING, net.minecraft.core.Direction.NORTH));')
    at=text.index('    public RepairBlock(')
    methods='''    public static final net.minecraft.world.level.block.state.properties.DirectionProperty FACING = net.minecraft.world.level.block.state.properties.BlockStateProperties.HORIZONTAL_FACING;
    @Override protected void createBlockStateDefinition(net.minecraft.world.level.block.state.StateDefinition.Builder<net.minecraft.world.level.block.Block, BlockState> builder) { builder.add(FACING); }
    @Override public BlockState getStateForPlacement(net.minecraft.world.item.context.BlockPlaceContext context) { return defaultBlockState().setValue(FACING,context.getHorizontalDirection().getOpposite()); }
    @Override public net.minecraft.world.phys.shapes.VoxelShape getShape(BlockState state, net.minecraft.world.level.BlockGetter world, BlockPos pos, net.minecraft.world.phys.shapes.CollisionContext context) {
        return net.minecraft.world.phys.shapes.Shapes.or(box(0,0,0,16,10,16),box(1,10,1,15,16,15));
    }
'''
    text=text[:at]+methods+text[at:]
    if version.startswith('26.'):
        text=text.replace('net.minecraft.world.level.block.state.properties.DirectionProperty',
            'net.minecraft.world.level.block.state.properties.EnumProperty<net.minecraft.core.Direction>')
    if version=='1.16.5':
        for a,b in {
            'net.minecraft.core.Direction':'net.minecraft.util.Direction',
            'net.minecraft.world.level.block.state.properties.':'net.minecraft.state.properties.',
            'net.minecraft.world.level.block.state.StateDefinition':'net.minecraft.state.StateContainer',
            'net.minecraft.world.level.block.Block':'net.minecraft.block.Block',
            'net.minecraft.world.item.context.BlockPlaceContext':'net.minecraft.item.BlockItemUseContext',
            'net.minecraft.world.level.BlockGetter':'net.minecraft.world.IBlockReader',
            'net.minecraft.world.phys.shapes.VoxelShape':'net.minecraft.util.math.shapes.VoxelShape',
            'net.minecraft.world.phys.shapes.CollisionContext':'net.minecraft.util.math.shapes.ISelectionContext',
            'net.minecraft.world.phys.shapes.Shapes':'net.minecraft.util.math.shapes.VoxelShapes',
        }.items(): text=text.replace(a,b)
        text=text.replace('net.minecraft.state.properties.DirectionProperty','net.minecraft.state.DirectionProperty')
    return text

def legacy112(result):
    from menu_smoke_sources import menu_probe
    mod=result['RepairMod.java']
    mod=mod.replace('    public static final Station BLOCK', '''    @Mod.Instance(ID) public static RepairMod INSTANCE;
    public static final net.minecraft.creativetab.CreativeTabs TAB = new net.minecraft.creativetab.CreativeTabs(ID) {
        @Override public ItemStack createIcon() { return new ItemStack(BLOCK); }
    };
    public static final Station BLOCK''')
    mod=mod.replace('.setTranslationKey(ID+".repair_station");','.setTranslationKey(ID+".repair_station").setCreativeTab(TAB);')
    mod=mod.replace('GameRegistry.registerTileEntity(Machine.class, new ResourceLocation(ID, "repair_station"));',
        'GameRegistry.registerTileEntity(Machine.class, new ResourceLocation(ID, "repair_station"));\n        net.minecraftforge.fml.common.network.NetworkRegistry.INSTANCE.registerGuiHandler(this,new RepairGuiHandler());')
    mod=mod.replace('player.displayGUIChest((Machine)world.getTileEntity(pos));','player.openGui(INSTANCE,0,world,pos.getX(),pos.getY(),pos.getZ());')
    mod=mod.replace('return new ContainerHopper(inventory,this,p);','return new RepairMenu(inventory,this);')
    mod=mod.replace('public Station() { super(Material.IRON); setHardness(3.5F); }', '''public static final net.minecraft.block.properties.PropertyDirection FACING=net.minecraft.block.properties.PropertyDirection.create("facing",net.minecraft.util.EnumFacing.Plane.HORIZONTAL);
        public Station() { super(Material.IRON); setHardness(3.5F);setDefaultState(blockState.getBaseState().withProperty(FACING,EnumFacing.NORTH)); }
        @Override protected net.minecraft.block.state.BlockStateContainer createBlockState() { return new net.minecraft.block.state.BlockStateContainer(this,FACING); }
        @Override public IBlockState getStateFromMeta(int meta) { return getDefaultState().withProperty(FACING,EnumFacing.byHorizontalIndex(meta)); }
        @Override public int getMetaFromState(IBlockState state) { return state.getValue(FACING).getHorizontalIndex(); }
        @Override public IBlockState getStateForPlacement(World w,BlockPos p,EnumFacing f,float x,float y,float z,int meta,net.minecraft.entity.EntityLivingBase placer,EnumHand hand) { return getDefaultState().withProperty(FACING,placer.getHorizontalFacing().getOpposite()); }
        @Override public boolean isOpaqueCube(IBlockState state) { return false; }
        @Override public boolean isFullCube(IBlockState state) { return false; }''')
    result['RepairMod.java']=mod
    result['RepairMod.java']=mod.replace('energy.receiveEnergy(1000,false);','energy.receiveEnergy(1000,false);\n            '+menu_probe({'minecraft':'1.12.2','loader':'forge'}))
    result['RepairMenu.java']=(TEMPLATES/'RepairMenu112.java').read_text()
    result['RepairScreen.java']=screen_source('1.12.2')
    result['RepairGuiHandler.java']='''package com.nstut.repair;
public final class RepairGuiHandler implements net.minecraftforge.fml.common.network.IGuiHandler {
    public Object getServerGuiElement(int id,net.minecraft.entity.player.EntityPlayer player,net.minecraft.world.World world,int x,int y,int z) {
        net.minecraft.tileentity.TileEntity tile=world.getTileEntity(new net.minecraft.util.math.BlockPos(x,y,z));
        return id==0 && tile instanceof RepairMod.Machine ? new RepairMenu(player.inventory,(RepairMod.Machine)tile) : null;
    }
    public Object getClientGuiElement(int id,net.minecraft.entity.player.EntityPlayer player,net.minecraft.world.World world,int x,int y,int z) {
        Object menu=getServerGuiElement(id,player,world,x,y,z);
        return menu instanceof RepairMenu ? new RepairScreen((RepairMenu)menu,player.inventory,new net.minecraft.util.text.TextComponentTranslation("container.@ID@.repair_station")) : null;
    }
}
'''
    return result
