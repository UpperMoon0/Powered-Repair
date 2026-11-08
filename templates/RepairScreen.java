package com.nstut.repair;

import com.nstut.openui.api.*;
import com.nstut.openui.graphics.SurfaceStyle;
import com.nstut.openui.graphics.UiCanvas;
import com.nstut.openui.minecraft.UiContainerScreen;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import java.util.Locale;

/** OpenUI surfaces surround native inventory slots; decoration never captures slot input. */
public class RepairScreen extends UiContainerScreen<RepairMenu> {
    private static final int TEXT = 0xFFF1F6F7, MUTED = 0xFFACC6CA, MINT = 0xFF7AEAC2;
    private static final SurfaceStyle SHELL = new SurfaceStyle(0xF3264955,0xF010202F,0xFF477382,9,5,0x70000000);
    private static final SurfaceStyle CARD = new SurfaceStyle(0xE01A3543,0xEC122733,0xFF355564,5,0,0);
    private static final SurfaceStyle WELL = new SurfaceStyle(0xFF0B1923,0xFF162C37,0xFF47636D,3,0,0);
    private final RepairMenu repair;
    public RepairScreen(RepairMenu menu, Inventory inventory, Component title) {
        @SCREEN_SUPER@
        repair = menu;
        @SCREEN_DIMENSIONS@
    }
    private static Component label(String key, Object... values) { return Component.translatable("ui.@ID@." + key, values); }
    private static String number(int value) { return String.format(Locale.ROOT, "%,d", value); }
    @LABEL_OVERRIDE@
    @Override protected void renderBackgroundLayer(GuiGraphics g, float pt, int mx, int my) {
        UiCanvas c = new UiCanvas(g, @SCREEN_FONT@);
        int x = @SCREEN_LEFT@, y = @SCREEN_TOP@;
        c.surface(x,y,RepairMenu.WIDTH,RepairMenu.HEIGHT,SHELL);
        UiRender.roundedRect(g,x+14,y+12,3,20,1,MINT);
        UiRender.text(g,@SCREEN_FONT@,"@NAME@",x+23,y+13,TEXT);
        UiRender.text(g,@SCREEN_FONT@,label("subtitle").getString(),x+23,y+27,MUTED);
        c.surface(x+12,y+44,216,78,CARD);
        c.surface(x+234,y+44,38,78,CARD);
        c.surface(x+10,y+139,174,90,CARD);
        c.surface(x+192,y+139,80,90,CARD);
        UiRender.text(g,@SCREEN_FONT@,label("equipment").getString(),x+22,y+51,MUTED);
        UiRender.text(g,@SCREEN_FONT@,label("energy").getString(),x+238,y+49,MUTED);
        for (int i=0;i<5;i++) {
            c.surface(x+23+40*i,y+69,18,18,WELL);
            int durability=repair.durability(i);
            UiRender.text(g,@SCREEN_FONT@,durability<0?"-":durability+"%",x+23+40*i,y+92,durability==100?MINT:MUTED);
        }
        String status=repair.status();
        int statusColor = status.equals("unpowered") || status.equals("paused") ? 0xFFF0C979 : MINT;
        UiRender.roundedRect(g,x+22,y+110,4,4,2,statusColor);
        UiRender.text(g,@SCREEN_FONT@,label(status).getString(),x+32,y+107,statusColor);
        UiRender.text(g,@SCREEN_FONT@,label("inventory").getString(),x+16,y+128,MUTED);
        for (int row=0;row<3;row++) for(int col=0;col<9;col++) c.surface(x+15+18*col,y+144+18*row,18,18,WELL);
        for(int col=0;col<9;col++) c.surface(x+15+18*col,y+204,18,18,WELL);
        UiRender.text(g,@SCREEN_FONT@,label("cost").getString(),x+200,y+148,MUTED);
        UiRender.text(g,@SCREEN_FONT@,number(repair.cost())+" FE",x+200,y+162,TEXT);
        UiRender.text(g,@SCREEN_FONT@,label("rate").getString(),x+200,y+180,MUTED);
        UiRender.text(g,@SCREEN_FONT@,number(repair.rate())+" /t",x+200,y+194,TEXT);
    }
    @Override protected UIComponent buildUI() {
        UIComponent energy = new LiveTooltipComponent() {
            @Override public int preferredWidth(Font f) { return 26; }
            @Override public int preferredHeight(Font f) { return 54; }
            @Override protected String tooltipText(int mx, int my) {
                return label("energy_tip",number(repair.energy()),number(repair.capacity()),number(repair.rate())).getString();
            }
            @Override public void render(GuiGraphics g, Font f, int mx, int my, float pt) {
                UiRender.roundedOutline(g,x+6,y,14,height,3,0xFF091722,0xFF527B83);
                int amount = repair.capacity() <= 0 ? 0 : (int)Math.min(height-4,(long)(height-4)*repair.energy()/repair.capacity());
                if(amount>0) new UiCanvas(g,f).surface(x+8,y+height-2-amount,10,amount,
                    new SurfaceStyle(0xFFA0FFE2,0xFF36B7A0,0,2,0,0));
            }
        };
        UIComponent help = Ui.spacer().width(205).height(14).tooltip(label("equipment_tip"));
        return Ui.stack(Ui.positioned(energy.width(26).height(54)).left(240).top(62),
            Ui.positioned(help).left(18).top(47));
    }
}
