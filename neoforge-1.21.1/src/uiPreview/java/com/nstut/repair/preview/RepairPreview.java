package com.nstut.repair.preview;

import com.nstut.repair.*;
import com.mojang.blaze3d.platform.NativeImage;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.item.*;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import java.nio.file.*;
import java.util.List;

/** Isolated real-renderer fixture. This source set is never included in production jars. */
@EventBusSubscriber(modid=RepairMod.ID,value=Dist.CLIENT)
public final class RepairPreview {
    private static final List<String> CASES=List.of("working","empty","unpowered","paused","ready","energy-tooltip","item-tooltip","model");
    private static int index=-1;
    private static boolean advance;
    private static final Path OUTPUT=Path.of("..","ui-previews");
    @SubscribeEvent public static void tick(ClientTickEvent.Post event) {
        Minecraft mc=Minecraft.getInstance();
        if(index<0 && mc.player != null && mc.level != null && mc.screen == null && mc.getOverlay()==null) {
            System.out.println("POWERED_REPAIR_PREVIEW_START");
            mc.options.guiScale().set(3); mc.resizeDisplay();
            mc.options.pauseOnLostFocus=false;
            index=0; show();
        } else if(advance) {
            advance=false;
            if(++index<CASES.size()) show();
            else {
                try { Files.writeString(OUTPUT.resolve("manifest.json"),"{\"screens\":[\""+String.join("\",\"",CASES)+"\"]}"); }
                catch(Exception e) { throw new IllegalStateException(e); }
                mc.stop();
            }
        }
    }
    private static void show() {
        Minecraft mc=Minecraft.getInstance();
        String state=CASES.get(index);
        if(state.equals("model")) { mc.setScreen(new ModelPreview());return; }
        Inventory inventory=new Inventory(null);
        inventory.setItem(0,new ItemStack(Items.IRON_INGOT,24));
        inventory.setItem(1,new ItemStack(Items.REDSTONE,16));
        inventory.setItem(9,new ItemStack(Items.DIAMOND,8));
        SimpleContainer equipment=new SimpleContainer(5);
        if(!state.equals("empty")) {
            Item[] items={Items.DIAMOND_PICKAXE,Items.IRON_CHESTPLATE,Items.DIAMOND_AXE,Items.IRON_SWORD,Items.DIAMOND_BOOTS};
            for(int i=0;i<5;i++) {
                ItemStack item=new ItemStack(items[i]);
                item.setDamageValue(state.equals("ready")?0:Math.min(40+i*20,item.getMaxDamage()-1));
                equipment.setItem(i,item);
            }
        }
        SimpleContainerData data=new SimpleContainerData(9);
        int[] values={state.equals("unpowered")?0:73500,100000,100,1};
        for(int i=0;i<4;i++) { data.set(i*2,values[i]&65535);data.set(i*2+1,values[i]>>>16); }
        data.set(8,state.equals("paused")?1:0);
        mc.setScreen(new MenuPreview(new RepairMenu(0,inventory,equipment,data),inventory,state,data));
    }
    private static void capture(String name) {
        try {
            Files.createDirectories(OUTPUT);
            try(NativeImage image=Screenshot.takeScreenshot(Minecraft.getInstance().getMainRenderTarget())) {
                image.writeToFile(OUTPUT.resolve(name+".png"));
            }
            advance=true;
        } catch(Exception e) { throw new IllegalStateException(e); }
    }
    private static final class MenuPreview extends RepairScreen {
        private final String state;
        private final SimpleContainerData data;
        private int frames;
        private long first;
        MenuPreview(RepairMenu menu,Inventory inventory,String state,SimpleContainerData data) { super(menu,inventory,Component.literal("Repair Station"));this.state=state;this.data=data; }
        @Override protected void containerTick() { }
        @Override public void renderBackground(GuiGraphics g,int mx,int my,float pt) {
            g.fill(0,0,width,height,0xFF0A1420);
            renderBackgroundLayer(g,pt,mx,my);
        }
        @Override public void render(GuiGraphics g,int mx,int my,float pt) {
            if(first==0) first=System.nanoTime();
            if(state.equals("energy-tooltip") && System.nanoTime()-first>700_000_000L) {
                data.set(0,72123&65535);data.set(1,72123>>>16);
            }
            int px=-1,py=-1;
            if(state.equals("energy-tooltip")) { px=leftPos+253;py=topPos+84; }
            if(state.equals("item-tooltip")) { px=leftPos+32;py=topPos+78; }
            super.render(g,px,py,0);
            if(++frames>=12 && System.nanoTime()-first>2_000_000_000L) {
                if(state.equals("energy-tooltip") && uiRuntime().overlays().components().stream().noneMatch(c->c instanceof com.nstut.openui.controls.Tooltip))
                    throw new AssertionError("Energy gauge must show a real OpenUI tooltip");
                g.flush();capture(state);frames=-10000;
            }
        }
    }
    private static final class ModelPreview extends Screen {
        private int frames;
        ModelPreview() { super(Component.literal("Repair Station model")); }
        @Override public void render(GuiGraphics g,int mx,int my,float pt) {
            g.fill(0,0,width,height,0xFF0A1420);
            g.drawCenteredString(font,"Powered Repair | 16 x 16 materials",width/2,24,0xFFE4F3F3);
            g.pose().pushPose();g.pose().translate(width/2f-96,height/2f-80,0);g.pose().scale(12,12,12);
            g.renderItem(new ItemStack(RepairMod.ITEM.get()),0,0);g.pose().popPose();
            if(++frames>=20) { g.flush();capture("model");frames=-10000; }
        }
    }
}
