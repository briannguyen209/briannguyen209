"use strict";
import { formattingSettings } from "powerbi-visuals-utils-formattingmodel";

class BulletCard extends formattingSettings.SimpleCard {
    barColor = new formattingSettings.ColorPicker({ name: "barColor", displayName: "Màu thanh thực tế", value: { value: "#4e79a7" } });
    targetColor = new formattingSettings.ColorPicker({ name: "targetColor", displayName: "Màu vạch mục tiêu", value: { value: "#000000" } });
    showBands = new formattingSettings.ToggleSwitch({ name: "showBands", displayName: "Hiện dải 60/80/100/120%", value: true });
    showLabels = new formattingSettings.ToggleSwitch({ name: "showLabels", displayName: "Hiện % đạt", value: true });
    name = "bulletSettings";
    displayName = "Bullet (kiểu Tableau)";
    slices = [this.barColor, this.targetColor, this.showBands, this.showLabels];
}

export class VisualFormattingSettingsModel extends formattingSettings.Model {
    bulletCard = new BulletCard();
    cards = [this.bulletCard];
}
