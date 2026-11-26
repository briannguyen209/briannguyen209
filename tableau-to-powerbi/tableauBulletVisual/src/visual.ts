"use strict";
// Bullet Graph kiểu Tableau cho Power BI: dải tham chiếu xám, thanh thực tế, vạch mục tiêu.
// Hỗ trợ tooltip và click để cross-filter các visual khác (giống action filter của Tableau).
import powerbi from "powerbi-visuals-api";
import { FormattingSettingsService } from "powerbi-visuals-utils-formattingmodel";
import * as d3 from "d3";
import "./../style/visual.less";

import VisualConstructorOptions = powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions = powerbi.extensibility.visual.VisualUpdateOptions;
import IVisual = powerbi.extensibility.visual.IVisual;
import IVisualHost = powerbi.extensibility.visual.IVisualHost;
import ISelectionManager = powerbi.extensibility.ISelectionManager;
import ISelectionId = powerbi.visuals.ISelectionId;

import { VisualFormattingSettingsModel } from "./settings";

interface Row { category: string; actual: number; target: number; id: ISelectionId; }

export class Visual implements IVisual {
    private host: IVisualHost;
    private svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
    private selection: ISelectionManager;
    private settings: VisualFormattingSettingsModel;
    private fmt = new FormattingSettingsService();

    constructor(options: VisualConstructorOptions) {
        this.host = options.host;
        this.selection = this.host.createSelectionManager();
        this.svg = d3.select(options.element).append("svg").classed("bullet", true);
        this.svg.on("click", () => { this.selection.clear(); this.svg.selectAll(".row").style("opacity", 1); });
    }

    public update(options: VisualUpdateOptions) {
        this.host.eventService.renderingStarted(options);
        const dv = options.dataViews?.[0];
        this.settings = this.fmt.populateFormattingSettingsModel(VisualFormattingSettingsModel, dv);
        const { width, height } = options.viewport;
        this.svg.attr("width", width).attr("height", height).selectAll("*").remove();
        const cat = dv?.categorical?.categories?.[0];
        const vals = dv?.categorical?.values;
        if (!cat || !vals) { this.host.eventService.renderingFinished(options); return; }
        const actualCol = vals.find(v => v.source.roles?.actual);
        const targetCol = vals.find(v => v.source.roles?.target);
        const rows: Row[] = cat.values.map((c, i) => ({
            category: String(c),
            actual: Number(actualCol?.values[i] ?? 0),
            target: Number(targetCol?.values[i] ?? 0),
            id: this.host.createSelectionIdBuilder().withCategory(cat, i).createSelectionId()
        }));

        const s = this.settings.bulletCard;
        const m = { top: 10, right: 50, bottom: 24, left: 110 };
        const w = Math.max(10, width - m.left - m.right), h = Math.max(10, height - m.top - m.bottom);
        const y = d3.scaleBand<string>().domain(rows.map(r => r.category)).range([0, h]).padding(0.3);
        const maxV = d3.max(rows, r => Math.max(r.actual, r.target * (s.showBands.value ? 1.2 : 1))) || 1;
        const x = d3.scaleLinear().domain([0, maxV]).nice().range([0, w]);
        const g = this.svg.append("g").attr("transform", `translate(${m.left},${m.top})`);
        g.append("g").attr("class", "axis").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x).ticks(5, "~s"));

        const row = g.selectAll(".row").data(rows).enter().append("g").attr("class", "row")
            .attr("transform", r => `translate(0,${y(r.category)})`).style("cursor", "pointer");
        const bh = y.bandwidth();
        if (s.showBands.value) {
            [[1.2, "#e6e6e6"], [1.0, "#cfcfcf"], [0.8, "#b5b5b5"], [0.6, "#9e9e9e"]].forEach(([k, c]) =>
                row.append("rect").attr("height", bh).attr("width", r => x(r.target * (k as number))).attr("fill", c as string));
        }
        row.append("rect").attr("y", bh / 3).attr("height", bh / 3).attr("width", r => x(r.actual)).attr("fill", s.barColor.value.value);
        row.append("rect").attr("x", r => x(r.target) - 1.5).attr("y", bh * 0.1).attr("width", 3).attr("height", bh * 0.8).attr("fill", s.targetColor.value.value);
        row.append("text").attr("class", "cat").attr("x", -8).attr("y", bh / 2).attr("dy", "0.35em").attr("text-anchor", "end").text(r => r.category);
        if (s.showLabels.value) {
            row.append("text").attr("class", "pct").attr("x", r => Math.max(x(r.actual), x(r.target * 1.2)) + 4)
                .attr("y", bh / 2).attr("dy", "0.35em").text(r => r.target ? d3.format(".0%")(r.actual / r.target) : "");
        }

        const tip = this.host.tooltipService;
        row.on("mousemove", (ev: MouseEvent, r: Row) => tip.show({
            coordinates: [ev.clientX, ev.clientY], isTouchEvent: false, identities: [r.id],
            dataItems: [{ displayName: "Danh mục", value: r.category }, { displayName: "Thực tế", value: d3.format(",.0f")(r.actual) },
                        { displayName: "Mục tiêu", value: d3.format(",.0f")(r.target) }, { displayName: "% đạt", value: r.target ? d3.format(".1%")(r.actual / r.target) : "-" }]
        })).on("mouseleave", () => tip.hide({ immediately: true, isTouchEvent: false }))
           .on("click", (ev: MouseEvent, r: Row) => {
                ev.stopPropagation();
                this.selection.select(r.id, ev.ctrlKey || ev.metaKey).then(ids => {
                    row.style("opacity", (d: Row) => ids.length === 0 || ids.some(i => d.id.equals(i as ISelectionId)) ? 1 : 0.35);
                });
           });
        this.host.eventService.renderingFinished(options);
    }

    public getFormattingModel(): powerbi.visuals.FormattingModel {
        return this.fmt.buildFormattingModel(this.settings);
    }
}
