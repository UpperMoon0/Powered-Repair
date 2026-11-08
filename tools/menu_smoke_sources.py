"""Exercise native menu transfers and the signed-short synchronization boundary."""
def menu_probe(cfg):
    v=cfg.get('_recipeMinecraft',cfg['minecraft'])
    old=v in ('1.12.2','1.16.5')
    legacy=v=='1.12.2'
    new=v.startswith('26.')
    ns='net.neoforged.neoforge' if cfg['loader']=='neoforge' else 'net.minecraftforge'
    item='net.minecraft.item' if old else 'net.minecraft.world.item'
    inventory='net.minecraft.entity.player.InventoryPlayer' if legacy else 'net.minecraft.entity.player.PlayerInventory' if old else 'net.minecraft.world.entity.player.Inventory'
    world='net.minecraft.world.WorldServer' if legacy else 'net.minecraft.world.server.ServerWorld' if old else 'net.minecraft.server.level.ServerLevel'
    fake=f'{ns}.common.util.FakePlayer'
    level='world' if legacy else 'level'
    get='getStackInSlot' if legacy else 'getItem'
    put='setInventorySlotContents' if legacy else 'setItem'
    transfer='transferStackInSlot' if legacy else 'quickMoveStack'
    factory='machine.createContainer(probeInventory,probePlayer)' if legacy else 'machine.createMenu(1,probeInventory,probePlayer)'
    client='new RepairMenu(probeInventory,machine)' if legacy else 'new RepairMenu(2,probeInventory)'
    update='updateProgressBar' if legacy else 'setData'
    items='net.minecraft.init.Items' if legacy else item+'.Items'
    invargs='probePlayer,new net.minecraft.world.entity.EntityEquipment()' if new else 'probePlayer'
    return f'''{fake} probePlayer={ns}.common.util.FakePlayerFactory.getMinecraft(({world}){level});
            {inventory} probeInventory=new {inventory}({invargs});
            RepairMenu probeMenu=(RepairMenu){factory};
            {'probeMenu.detectAndSendChanges();' if legacy else ''}
            if(probeMenu.capacity()!=RepairMod.SETTINGS.capacity || probeMenu.energy()!=machine.power.stored()) throw new AssertionError("full-width native menu data");
            RepairMenu probeClient={client};
            probeClient.{update}(0,-1);probeClient.{update}(1,32767);
            probeClient.{update}(2,(short)34464);probeClient.{update}(3,1);
            if(probeClient.energy()!=Integer.MAX_VALUE || probeClient.capacity()!=100000) throw new AssertionError("signed-short menu synchronization");
            {item}.ItemStack probeSaved=machine.{get}(0);
            machine.{put}(0,{item}.ItemStack.EMPTY);
            try {{
                {item}.ItemStack probeTool=new {item}.ItemStack({items}.DIAMOND_PICKAXE);
                probeTool.{'setItemDamage' if legacy else 'setDamageValue'}(10);
                probeInventory.{put}(9,probeTool);
                probeMenu.{transfer}(probePlayer,5);
                if(machine.{get}(0).isEmpty() || !probeInventory.{get}(9).isEmpty()) throw new AssertionError("shift-click damaged equipment into machine");
                probeMenu.{transfer}(probePlayer,0);
                if(!machine.{get}(0).isEmpty()) throw new AssertionError("manual shift-click removal before repair completes");
                probeInventory.{put}(9,new {item}.ItemStack({items}.REDSTONE,32));
                probeMenu.{transfer}(probePlayer,5);
                if(!machine.{get}(0).isEmpty()) throw new AssertionError("non-equipment rejected by repair slots");
            }} finally {{ machine.{put}(0,probeSaved); }}'''
