from tutorial_lib import *  # noqa: F401,F403

CFG = B.TABLEAU_CONFIG


def fields_table(rows):
    table(["Field (drag into Values)", "From table", "Why it is needed"], rows, [2600, 1800, 4960])


def ch_heatmap():
    h1("5. Highlight table (heatmap)")
    p("**What you'll build:** a grid of Region × Sub-category where each cell is coloured by sales and shows the number — "
      "Tableau's *highlight table*. Clicking a cell filters the page; clicking a Segment bar re-colours the cells to that "
      "segment's sales.")
    image(REPO / "renders" / "pbip_tableau1_highlight_table_normal.png", 4.6, "The finished chart (report page 1)")
    fields_table([["Region", "Sales", "columns of the grid"], ["SubCategory", "Sales", "rows of the grid"],
                  ["Total Sales (measure)", "_Measures", "cell colour and label"]])
    C = "ch05_heatmap"
    R = dataset("Sales", ["Region", "SubCategory"], ["Total Sales"])
    RI = dataset("Sales", ["Region", "SubCategory"], ["Total Sales"], interacting=True)

    s1 = {"$schema": VL, "data": {"name": "dataset"}, "mark": "rect",
          "encoding": {"x": {"field": "Region", "type": "nominal"}, "y": {"field": "SubCategory", "type": "nominal"}}}
    step(C, 1, "Draw the grid", s1, R, {
        "do": ["Create a new Vega-Lite spec (empty template), delete everything in the Specification tab and paste:"],
        "why": ["`rect` draws one rectangle per row of `dataset`. Because `x` and `y` are **nominal** (categories), "
                "Vega-Lite splits the width into one band per Region and the height into one band per SubCategory, so the "
                "36 rows become a 4 × 9 grid. Every cell is the same default blue because nothing controls colour yet."]})

    s2 = deep(s1)
    s2["mark"] = {"type": "rect", "stroke": "white", "strokeWidth": 1.5}
    s2["encoding"]["color"] = {"field": "Total Sales", "type": "quantitative", "scale": {"scheme": "blues"}}
    step(C, 2, "Colour each cell by sales", s2, R, {
        "do": ["Change `mark` from a plain string to an object (so it can take properties), and add a `color` encoding:"],
        "why": ["`color` with a **quantitative** field creates a continuous colour scale and a legend. "
                "`\"scheme\": \"blues\"` picks a light-to-dark blue ramp (Tableau's default for highlight tables). "
                "`stroke` + `strokeWidth` on the mark draw white gaps between cells — a mark property, so it applies to every cell."],
        "notes": [("tip", "Other schemes to try: `greens`, `oranges`, `viridis`, `redblue` (diverging). The full list is "
                          "on vega.github.io/vega/docs/schemes.")]},
        show=[("mark", "Replace \"mark\": \"rect\" with:"), ("encoding.color", "Add inside \"encoding\":")])

    s3 = {"$schema": VL, "data": {"name": "dataset"},
          "encoding": {"x": {"field": "Region", "type": "nominal", "axis": {"orient": "top", "title": None, "labelAngle": 0}},
                       "y": {"field": "SubCategory", "type": "nominal", "title": None}},
          "layer": [{"mark": {"type": "rect", "stroke": "white", "strokeWidth": 1.5},
                     "encoding": {"color": {"field": "Total Sales", "type": "quantitative", "scale": {"scheme": "blues"}}}},
                    {"mark": {"type": "text", "fontSize": 11},
                     "encoding": {"text": {"field": "Total Sales", "type": "quantitative", "format": ",.0f"}}}]}
    step(C, 3, "Add the numbers with a second layer", s3, R, {
        "do": ["To put text on top of the rectangles we need two marks, so the spec becomes a **layer**. Replace the whole "
               "spec with:"],
        "why": ["The shared `encoding` (x and y) sits at the top level, so both layers use the same grid. Layer 1 is the "
                "coloured `rect`; layer 2 is a `text` mark whose `text` channel shows Total Sales. `format: \",.0f\"` "
                "uses d3-format: thousands separator, no decimals.",
                "We also tidied the axes: `orient: \"top\"` moves Region labels above the grid like Tableau, "
                "`labelAngle: 0` keeps them horizontal, and `title: null` removes the redundant axis titles."],
        "notes": [("watch", "Layers are drawn in order — the first layer is at the back. Put `text` after `rect` or the "
                            "rectangles will hide the numbers.")]})

    s4 = deep(s3)
    s4["transform"] = [{"joinaggregate": [{"op": "max", "field": "Total Sales", "as": "maxSales"}]}]
    s4["layer"][0]["encoding"]["color"].update({"title": "Sales", "legend": {"format": "~s"}})
    s4["layer"][1]["encoding"]["color"] = {"condition": {"test": "datum['Total Sales'] > datum.maxSales * 0.55", "value": "white"},
                                           "value": "#333"}
    s4 = {k: s4[k] for k in ["$schema", "data", "transform", "encoding", "layer"]}
    step(C, 4, "Make the numbers readable on dark cells", s4, R, {
        "do": ["Dark text disappears on dark blue cells. Add a `transform` (top level, after `data`) and a conditional "
               "text colour in the text layer:"],
        "why": ["`joinaggregate` computes the maximum Total Sales over *all* rows and writes it onto *every* row as "
                "`maxSales` — the rows themselves are kept. Now each text mark can compare its own value to the maximum: "
                "above 55% of the max the cell is dark, so the text turns white.",
                "This is better than a hard-coded number (like `> 100000`) because it keeps working when slicers change "
                "the totals. The legend format `~s` shows 120k instead of 120,000."]},
        show=[("transform", "Add at the top level:"), ("layer[1].encoding.color", "Add inside the text layer's \"encoding\":")])

    s5 = deep(B.SPEC_HEAT); s5.pop("description", None)
    step(C, 5, "Wire up cross-filtering, cross-highlighting and tooltips", s5, R, {
        "do": ["Replace the spec with the version below (the differences are explained underneath), then open the "
               "**Settings** tab and switch on **Tooltips**, **Cross-filtering** and **Cross-highlighting**."],
        "why": ["**Cross-highlight:** colour and text now use `Total Sales__highlight` instead of `Total Sales`. With "
                "nothing highlighted the two are identical; when you click *Consumer* in the Segment bar chart, the "
                "highlight field holds only Consumer sales, so the heatmap re-colours to that segment.",
                "**Cross-filter:** clicking a cell selects that row. The `opacity` condition dims every cell whose "
                "`__selected__` is `off`, so the clicked cell stands out — exactly like a native visual.",
                "**Tooltip:** a list of fields to show on hover. `title` renames a field in the tooltip; `format` "
                "formats numbers."]}, interacting_rows=RI)

    h3("Step 6 — Give it the Tableau look (Config tab)")
    p("Open the **Config** tab, replace its contents with the JSON below and press **Apply**. This is the shared "
      "\"Tableau theme\" used by every chart in chapters 5–9 — paste it into each of them.")
    code(cjson(CFG), label="Config tab · also saved as tutorial/steps/tableau_config.json")
    (STEPS / "tableau_config.json").write_text(json.dumps(CFG, indent=2))
    p("What each part does: `range.category` sets Tableau 10's colours for categories; `axis` makes gridlines and labels "
      "light grey; `view.stroke: null` removes the border around the plot; `font` uses Power BI's Segoe UI; "
      "`autosize: fit` makes the chart fill the visual exactly.")
    image(render(s5, R, f"{C}_final", 480, 320, CFG), 4.6, "Final chart with the Tableau config")
    h3("Check your understanding")
    bullets(["Change the scheme to `greens`. Which part of the spec did you edit?",
             "Show Profit Ratio in the cells instead (add the measure to Values; use `format: \".0%\"`).",
             "Swap rows and columns. Does the text-colour rule still work? Why?"])


def ch_dualaxis():
    h1("6. Dual axis: bars + line")
    p("**What you'll build:** monthly sales as bars with the profit ratio as a line on a second axis — Tableau's "
      "*dual axis* combination chart.")
    image(REPO / "renders" / "pbip_tableau1_dual_axis_normal.png", 5.4, "The finished chart")
    fields_table([["YearMonth", "Sales", "one bar per month (text like 2024-03, sorts correctly)"],
                  ["Total Sales (measure)", "_Measures", "bar height"], ["Profit Ratio (measure)", "_Measures", "line"]])
    C = "ch06_dualaxis"
    R = dataset("Sales", ["YearMonth"], ["Total Sales", "Profit Ratio"])
    RI = dataset("Sales", ["YearMonth"], ["Total Sales", "Profit Ratio"], interacting=True)
    W, H = 620, 280

    s1 = {"$schema": VL, "data": {"name": "dataset"}, "mark": "bar",
          "encoding": {"x": {"field": "YearMonth", "type": "ordinal"}, "y": {"field": "Total Sales", "type": "quantitative"}}}
    step(C, 1, "Monthly bars", s1, R, {
        "do": ["Create a new Vega-Lite visual with the three fields and paste:"],
        "why": ["`YearMonth` is text such as `2024-03`, so we use **ordinal**: categories in sorted order. Text in "
                "`YYYY-MM` form sorts alphabetically in date order, which is why the model includes this column."]},
        config=CFG, w=W, h=H)

    s2 = {"$schema": VL, "data": {"name": "dataset"},
          "encoding": {"x": {"field": "YearMonth", "type": "ordinal"}},
          "layer": [{"mark": "bar", "encoding": {"y": {"field": "Total Sales", "type": "quantitative"}}},
                    {"mark": {"type": "line", "color": "#f28e2b"},
                     "encoding": {"y": {"field": "Profit Ratio", "type": "quantitative"}}}]}
    step(C, 2, "Add the line — and see the problem", s2, R, {
        "do": ["Turn the spec into a layer: the shared x stays on top, each layer brings its own y."],
        "why": ["The line is there but flat along the bottom. By default layers **share** one y scale, which now runs "
                "from 0 to ~80,000; a ratio of 0.15 is invisible on that scale. This is the moment you would drag a "
                "second measure onto the right axis in Tableau."]}, config=CFG, w=W, h=H)

    s3 = deep(s2)
    s3["layer"][0] = {"mark": {"type": "bar", "color": "#4e79a7"},
                      "encoding": {"y": {"field": "Total Sales", "type": "quantitative", "title": "Sales",
                                         "axis": {"titleColor": "#4e79a7", "format": "~s"}}}}
    s3["layer"][1]["encoding"]["y"].update({"title": "Profit ratio", "axis": {"format": ".0%", "titleColor": "#f28e2b", "grid": False}})
    s3["resolve"] = {"scale": {"y": "independent"}}
    step(C, 3, "Give each layer its own axis", s3, R, {
        "do": ["Add `resolve` at the top level and style both axes:"],
        "why": ["`\"resolve\": {\"scale\": {\"y\": \"independent\"}}` gives every layer its own y scale; Vega-Lite "
                "automatically puts the second axis on the right. Colouring each axis title like its mark tells the "
                "reader which axis belongs to which series. `grid: false` on the line's axis avoids two overlapping "
                "sets of gridlines."]},
        show=[("resolve", "Add at the top level:"), ("layer[0]", "Bar layer:"), ("layer[1]", "Line layer:")], config=CFG, w=W, h=H)

    s4 = deep(s3)
    s4["encoding"]["x"].update({"title": None, "axis": {"labelAngle": -45,
                                "labelExpr": "indexof(['01','04','07','10'], slice(datum.value, 5)) >= 0 ? datum.value : ''"}})
    s4["layer"][1]["mark"].update({"strokeWidth": 2.5, "point": {"filled": True, "color": "#f28e2b"}})
    step(C, 4, "Tidy the x-axis and add points", s4, R, {
        "do": ["Twenty-four labels are crowded. Show only quarter starts with a label expression, and add dots to the line:"],
        "why": ["`labelExpr` runs for every axis label. `datum.value` is the label text (e.g. `2024-04`); "
                "`slice(datum.value, 5)` takes the month part (`04`); `indexof([...], ...) >= 0` checks whether it is a "
                "quarter month. If not, the label becomes an empty string. The bars are still all there — only the labels "
                "are thinned.",
                "`point` on a line mark draws a dot at each value, which makes individual months easier to hover."]},
        show=[("encoding.x", "Shared x encoding:"), ("layer[1].mark", "Line mark:")], config=CFG, w=W, h=H)

    s5 = deep(B.SPEC_COMBO); s5.pop("description", None)
    step(C, 5, "Interactivity: highlight and selection on the bars", s5, R, {
        "do": ["Replace with the final spec, then switch on Tooltips, Cross-filtering and Cross-highlighting in **Settings**."],
        "why": ["The bar layer is now a **nested layer** of two bars on the same y scale: a faint full bar "
                "(`opacity: 0.3`) and, on top, a solid bar of `Total Sales__highlight`. When another visual highlights "
                "a segment, the solid part shrinks to that segment's share and the faint bar shows the total — Power "
                "BI's standard highlight look.",
                "Nesting matters: `resolve` makes the *outer* layers independent (bars vs line), while the two bars "
                "inside the nested layer still share one scale. The solid bar's opacity drops to 0 for unselected "
                "months, leaving only the faint outline."]}, config=CFG, w=W, h=H, interacting_rows=RI)
    h3("Check your understanding")
    bullets(["Replace the line with `Total Profit` (format `~s`). Do you still need two axes?",
             "Change the label rule to show only January of each year."])


def ch_bullet():
    h1("7. Bullet graph")
    p("**What you'll build:** for each Category, grey bands at 60/80/100/120% of target, a blue bar for actual sales and a "
      "black tick at the target — Stephen Few's bullet graph, a Tableau favourite.")
    image(REPO / "renders" / "pbip_tableau1_bullet_graph_normal.png", 5.2, "The finished chart")
    fields_table([["Category", "Sales", "one bullet per category"], ["Total Sales", "_Measures", "the bar"],
                  ["Total Target", "_Measures", "the tick and the bands"], ["Attainment %", "_Measures", "tooltip"]])
    C = "ch07_bullet"
    M = ["Total Sales", "Total Target", "Attainment %"]
    R = dataset("Sales", ["Category"], M); RI = dataset("Sales", ["Category"], M, interacting=True)
    W, H = 560, 180
    s1 = {"$schema": VL, "data": {"name": "dataset"}, "mark": "bar",
          "encoding": {"y": {"field": "Category", "type": "nominal", "title": None},
                       "x": {"field": "Total Sales", "type": "quantitative"}}}
    step(C, 1, "A plain bar per category", s1, R, {"do": ["Paste:"],
         "why": ["Putting the category on `y` makes horizontal bars, which suit long labels."]}, config=CFG, w=W, h=H)
    s2 = {"$schema": VL, "data": {"name": "dataset"},
          "encoding": {"y": {"field": "Category", "type": "nominal", "title": None}},
          "layer": [{"mark": {"type": "bar", "color": "#4e79a7", "size": 12},
                     "encoding": {"x": {"field": "Total Sales", "type": "quantitative"}}},
                    {"mark": {"type": "tick", "color": "black", "thickness": 3, "size": 28},
                     "encoding": {"x": {"field": "Total Target", "type": "quantitative"}}}]}
    step(C, 2, "Add the target tick", s2, R, {"do": ["Convert to a layer and add a `tick` mark for the target:"],
         "why": ["A `tick` is a short line across the band. `size` is its length (28 px, taller than the bar) and "
                 "`thickness` its width. The bar's `size: 12` makes it thinner than the band, leaving room for the grey "
                 "background bands we add next."]}, config=CFG, w=W, h=H)
    s3 = deep(s2)
    s3["transform"] = [{"calculate": f"datum['Total Target'] * {k}", "as": f"B{int(k * 100)}"} for k in (0.6, 0.8, 1.2)]
    bands = [{"mark": {"type": "bar", "color": c, "size": 30}, "encoding": {"x": {"field": f, "type": "quantitative"}}}
             for f, c in [("B120", "#e6e6e6"), ("Total Target", "#cfcfcf"), ("B80", "#b5b5b5"), ("B60", "#9e9e9e")]]
    bands[0]["encoding"]["x"].update({"title": "Sales vs target", "axis": {"format": "~s"}})
    s3["layer"] = bands + s3["layer"]
    s3 = {k: s3[k] for k in ["$schema", "data", "transform", "encoding", "layer"]}
    step(C, 3, "Add the qualitative bands", s3, R, {
        "do": ["Calculate the band edges, then put four grey bars *before* the existing layers:"],
        "why": ["`calculate` adds `B60`, `B80` and `B120` to each row (60/80/120% of that row's target); 100% is the "
                "target itself. Each band is just a wide bar starting at 0, so the **widest (120%) is drawn first** and "
                "each narrower, darker band is drawn on top of it. The result looks like adjacent ranges.",
                "Because the bands come from the target measure, they rescale with slicers automatically."],
        "notes": [("watch", "Order matters again: if the 120% band came last it would cover everything else.")]},
        show=[("transform", "Add at the top level:"), ("layer[0]", "First new layer (the others follow the same pattern; see the step file):")],
        config=CFG, w=W, h=H)
    s4 = deep(B.SPEC_BULLET); s4.pop("description", None)
    step(C, 4, "Interactivity", s4, R, {"do": ["Replace with the final spec and switch on the three interactivity settings."],
         "why": ["The actual bar now appears twice: a faint full bar and a solid `Total Sales__highlight` bar on top — "
                 "the same highlight pattern as chapter 6. The tooltip includes Attainment %, which is a measure in "
                 "Values but is not drawn."]}, config=CFG, w=W, h=H, interacting_rows=RI)
    h3("Check your understanding")
    bullets(["Make the bands 50/75/100/125%. Which two places change?", "Colour the bar red when Attainment % < 1 "
             "(hint: a `color` condition in the solid bar layer)."])


def ch_scatter():
    h1("8. Scatter with trend line and quadrants")
    p("**What you'll build:** each Sub-category × Region as a point (Sales vs Profit), coloured by Category, shaped by "
      "Region, with a regression line and average lines that split the chart into quadrants.")
    image(REPO / "renders" / "pbip_tableau2_scatter_with_trend__average__normal.png", 5.0, "The finished chart")
    fields_table([["SubCategory", "Sales", "level of detail (one point per SubCategory…)"],
                  ["Region", "Sales", "…per Region; also the shape"], ["Category", "Sales", "colour"],
                  ["Total Sales / Total Profit", "_Measures", "x / y position"]])
    C = "ch08_scatter"
    cols, M = ["SubCategory", "Region", "Category"], ["Total Sales", "Total Profit"]
    R = dataset("Sales", cols, M); RI = dataset("Sales", cols, M, interacting=True)
    W, H = 520, 320
    s1 = {"$schema": VL, "data": {"name": "dataset"}, "mark": "point",
          "encoding": {"x": {"field": "Total Sales", "type": "quantitative"}, "y": {"field": "Total Profit", "type": "quantitative"}}}
    step(C, 1, "Points", s1, R, {"do": ["Paste:"],
         "why": ["We get 36 points because Power BI returns one row per SubCategory × Region. **The columns you add "
                 "decide the level of detail** — this is the Deneb equivalent of Tableau's Detail shelf."]}, config=CFG, w=W, h=H)
    s2 = deep(s1)
    s2["mark"] = {"type": "point", "filled": True, "size": 110}
    s2["encoding"]["x"].update({"title": "Sales", "axis": {"format": "~s"}})
    s2["encoding"]["y"].update({"title": "Profit", "axis": {"format": "~s"}})
    s2["encoding"]["color"] = {"field": "Category", "type": "nominal"}
    s2["encoding"]["shape"] = {"field": "Region", "type": "nominal"}
    step(C, 2, "Colour, shape and size", s2, R, {"do": ["Fill the points and add two encodings:"],
         "why": ["Nominal `color` uses the category palette from the Config (Tableau 10). `shape` gives each Region a "
                 "different symbol; Vega-Lite adds a second legend automatically."]},
         show=[("mark", "mark:"), ("encoding.color", "Add to encoding:"), ("encoding.shape", "and:")], config=CFG, w=W, h=H)
    s3 = {"$schema": VL, "data": {"name": "dataset"},
          "layer": [{"mark": s2["mark"], "encoding": s2["encoding"]},
                    {"mark": {"type": "line", "color": "#777", "strokeDash": [4, 3]},
                     "transform": [{"regression": "Total Profit", "on": "Total Sales"}],
                     "encoding": {"x": {"field": "Total Sales", "type": "quantitative"},
                                  "y": {"field": "Total Profit", "type": "quantitative"}}}]}
    step(C, 3, "Add a trend line", s3, R, {
        "do": ["Move the points into a layer and add a second layer with a `regression` transform:"],
        "why": ["A transform inside a layer only affects that layer. `regression` replaces the layer's rows with points "
                "on the best-fit line (linear by default; try `\"method\": \"poly\"`), drawn as a dashed `line`. "
                "The points layer is untouched."]}, show=[("layer[1]", "New second layer:")], config=CFG, w=W, h=H)
    s4 = deep(s3)
    s4["layer"] += [{"mark": {"type": "rule", "color": "#bbb"}, "encoding": {"x": {"aggregate": "mean", "field": "Total Sales", "type": "quantitative"}}},
                    {"mark": {"type": "rule", "color": "#bbb"}, "encoding": {"y": {"aggregate": "mean", "field": "Total Profit", "type": "quantitative"}}}]
    step(C, 4, "Average lines (quadrants)", s4, R, {
        "do": ["Add two `rule` layers:"],
        "why": ["A `rule` with only `x` draws a vertical line across the whole chart; with only `y`, a horizontal line. "
                "`aggregate: \"mean\"` in the encoding averages the field over all rows, so there is one line each. "
                "Points to the upper-right are above average on both measures — Tableau's quadrant chart."]},
        show=[("layer[2]", "Layer 3:"), ("layer[3]", "Layer 4:")], config=CFG, w=W, h=H)
    s5 = deep(B.SPEC_SCATTER); s5.pop("description", None)
    step(C, 5, "Interactivity", s5, R, {"do": ["Replace with the final spec and switch on the interactivity settings."],
         "why": ["Points can't be partly highlighted, so for cross-highlight we dim points instead: the opacity "
                 "condition is now a **list** — dim if not selected, *or* if `Total Sales__highlightStatus` is `off` "
                 "(the point has no data for the highlighted segment). The first matching test wins."]},
         config=CFG, w=W, h=H, interacting_rows=RI)
    h3("Check your understanding")
    bullets(["Size the points by Total Profit (add a `size` encoding).", "Label only points above $20k profit (a text layer with a `filter` transform)."])


def ch_barinbar():
    h1("9. Bar-in-bar")
    p("**What you'll build:** a wide light bar for the target with a narrow bar for actual sales inside it, coloured blue if "
      "the target was met and red if missed.")
    image(REPO / "renders" / "pbip_tableau2_barinbar_normal.png", 5.0, "The finished chart")
    fields_table([["SubCategory", "Sales", "one row per sub-category"], ["Total Sales / Total Target", "_Measures", "the two bars"],
                  ["Attainment %", "_Measures", "tooltip"]])
    C = "ch09_barinbar"
    M = ["Total Sales", "Total Target", "Attainment %"]
    R = dataset("Sales", ["SubCategory"], M); RI = dataset("Sales", ["SubCategory"], M, interacting=True)
    W, H = 520, 280
    s1 = {"$schema": VL, "data": {"name": "dataset"}, "mark": {"type": "bar", "color": "#c7d6e8", "size": 22},
          "encoding": {"y": {"field": "SubCategory", "type": "nominal", "title": None},
                       "x": {"field": "Total Target", "type": "quantitative"}}}
    step(C, 1, "The outer (target) bar", s1, R, {"do": ["Paste:"],
         "why": ["`size: 22` sets the bar thickness in pixels so we can later fit a thinner bar inside it."]}, config=CFG, w=W, h=H)
    s2 = {"$schema": VL, "data": {"name": "dataset"},
          "encoding": {"y": {"field": "SubCategory", "type": "nominal", "title": None}},
          "layer": [{"mark": s1["mark"], "encoding": {"x": {"field": "Total Target", "type": "quantitative", "title": "Sales / Target"}}},
                    {"mark": {"type": "bar", "color": "#4e79a7", "size": 10}, "encoding": {"x": {"field": "Total Sales", "type": "quantitative"}}}]}
    step(C, 2, "The inner (actual) bar", s2, R, {"do": ["Layer a narrower bar for Total Sales on top:"],
         "why": ["Both bars share the band for each SubCategory and are centred in it, so the 10 px bar sits inside the "
                 "22 px one. That is all \"bar-in-bar\" is."]}, config=CFG, w=W, h=H)
    s3 = deep(s2)
    s3["transform"] = [{"calculate": "datum['Total Sales'] >= datum['Total Target'] ? 'Met' : 'Missed'", "as": "Status"}]
    s3["encoding"]["y"]["sort"] = "-x"
    s3["layer"][1]["mark"] = {"type": "bar", "size": 10}
    s3["layer"][1]["encoding"]["color"] = {"field": "Status", "type": "nominal", "title": None,
                                           "scale": {"domain": ["Met", "Missed"], "range": ["#4e79a7", "#e15759"]}}
    s3 = {k: s3[k] for k in ["$schema", "data", "transform", "encoding", "layer"]}
    step(C, 3, "Colour by status and sort", s3, R, {"do": ["Add a calculated Status and use it for colour; sort the bars:"],
         "why": ["The `calculate` expression uses the ternary `test ? a : b` operator. Pinning `domain` and `range` "
                 "guarantees Met is always blue and Missed always red, whatever order the data arrives in.",
                 "`\"sort\": \"-x\"` sorts the y categories by their x value, descending (the minus sign)."]},
         show=[("transform", "Top level:"), ("encoding.y", "Shared y:"), ("layer[1].encoding.color", "Inner bar colour:")], config=CFG, w=W, h=H)
    s4 = deep(B.SPEC_BARINBAR); s4.pop("description", None)
    step(C, 4, "Interactivity", s4, R, {"do": ["Replace with the final spec; switch on the interactivity settings."],
         "why": ["The inner bar now draws `Total Sales__highlight`, so cross-highlighting shrinks it to the highlighted "
                 "share, and the usual opacity condition shows the selection."]}, config=CFG, w=W, h=H, interacting_rows=RI)


def ch_bubbles():
    h1("10. Packed bubbles (Vega)")
    p("**What you'll build:** one circle per Sub-category, sized by sales and coloured by Category, packed tightly "
      "together. Vega-Lite has no packing layout, so this is our first **Vega** spec — re-read section 4.2 first.")
    image(REPO / "renders" / "pbip_tableau2_packed_bubbles_vega_normal.png", 4.4, "The finished chart")
    fields_table([["Category", "Sales", "colour"], ["SubCategory", "Sales", "one circle each"], ["Total Sales", "_Measures", "circle size"]])
    C = "ch10_bubbles"
    R = dataset("Sales", ["Category", "SubCategory"], ["Total Sales"])
    RI = dataset("Sales", ["Category", "SubCategory"], ["Total Sales"], interacting=True)
    W, H = 480, 360
    data = [{"name": "dataset"},
            {"name": "tree", "source": "dataset", "transform": [
                {"type": "formula", "expr": "datum.SubCategory", "as": "id"},
                {"type": "formula", "expr": "'root'", "as": "parent"}]},
            {"name": "rootNode", "values": [{"id": "root", "parent": None}]},
            {"name": "nodes", "source": ["rootNode", "tree"], "transform": [
                {"type": "stratify", "key": "id", "parentKey": "parent"},
                {"type": "pack", "field": "Total Sales", "sort": {"field": "value", "order": "descending"},
                 "size": [{"signal": "width"}, {"signal": "height"}], "padding": 4}]}]
    circle = {"type": "symbol", "from": {"data": "nodes"},
              "encode": {"update": {"x": {"field": "x"}, "y": {"field": "y"}, "shape": {"value": "circle"},
                                    "size": {"signal": "4 * datum.r * datum.r"},
                                    "fill": {"value": "#4e79a7"}, "stroke": {"value": "white"}}}}
    s1 = {"$schema": VG, "data": data, "marks": [circle]}
    step(C, 1, "Build a hierarchy and pack it", s1, R, {
        "do": ["Create a new **Vega** spec (empty template) and paste:"],
        "why": ["Circle packing needs a **tree**: every node has an `id` and a `parent`. Our rows have no parent, so the "
                "`tree` dataset gives every row `id = SubCategory` and `parent = 'root'` with two `formula` transforms.",
                "`rootNode` is a one-row dataset for the top of the tree. `nodes` combines both (`source` can be a list) and "
                "runs two transforms: `stratify` links children to parents; `pack` computes `x`, `y` and radius `r` for "
                "every node so that circle areas are proportional to `Total Sales` and nothing overlaps.",
                "The `symbol` mark draws a circle per node. Vega's `size` is the symbol's *area* in square pixels, so "
                "for a circle of radius r we pass `4 * r * r` (the area of its bounding square)."],
        "notes": [("watch", "The big outline circle is the root node — it contains everything. We hide it in step 4."),
                  ("tip", "Dataset names must be unique, and `root` is reserved in Vega, which is why it is called `rootNode`.")]},
        w=W, h=H)
    s2 = deep(s1)
    s2["scales"] = [{"name": "color", "type": "ordinal", "domain": {"data": "dataset", "field": "Category"}, "range": {"scheme": "tableau10"}}]
    s2["legends"] = [{"fill": "color", "title": "Category", "orient": "top-left"}]
    s2["marks"][0]["encode"]["update"]["fill"] = {"scale": "color", "field": "Category"}
    s2 = {k: s2[k] for k in ["$schema", "data", "scales", "legends", "marks"]}
    step(C, 2, "Colour by Category, with a legend", s2, R, {
        "do": ["Add a `scales` and a `legends` section (top level), and use the scale for `fill`:"],
        "why": ["In Vega you create scales yourself. This **ordinal** scale maps each Category (its `domain` is read "
                "from the data) to a colour from the `tableau10` scheme. `\"fill\": {\"scale\": \"color\", \"field\": "
                "\"Category\"}` sends each circle's Category through it. Legends are also explicit: `fill: \"color\"` "
                "builds a legend from that scale."]},
        show=[("scales", "\"scales\":"), ("legends", "\"legends\":"), ("marks[0].encode.update.fill", "Replace the fill:")], w=W, h=H)
    s3 = deep(s2)
    s3["marks"].append({"type": "text", "from": {"data": "nodes"},
                        "encode": {"update": {"x": {"field": "x"}, "y": {"field": "y"}, "align": {"value": "center"},
                                              "baseline": {"value": "middle"}, "fill": {"value": "white"},
                                              "text": {"signal": "datum.r < 16 ? '' : datum.SubCategory"},
                                              "fontSize": {"signal": "max(9, min(14, datum.r / 4))"}}}})
    step(C, 3, "Labels that fit", s3, R, {"do": ["Add a second mark — text at each circle's centre:"],
         "why": ["`text` is a **signal** (an expression): circles smaller than 16 px radius get an empty label because "
                 "the name would not fit. `fontSize` grows with the radius but stays between 9 and 14 px. The root has "
                 "no SubCategory, so its label is empty."]}, show=[("marks[1]", "Add to \"marks\":")], w=W, h=H)
    s4 = deep(B.vega_bubbles()); s4.pop("config", None)
    step(C, 4, "Hide the root, add tooltips and selection", s4, R, {
        "do": ["Replace with the final spec (also turn on Tooltips and Cross-filtering in Settings). The key changes are "
               "in the circle's `fill`, `fillOpacity` and `tooltip`:"],
        "why": ["`fill` is now a **list of rules**: the first whose `test` is true wins, so the root (`id == 'root'`) "
                "is transparent and every other circle uses the colour scale. The tooltip is an object built in an "
                "expression (`null` for the root, so it has none). `fillOpacity` dims unselected circles.",
                "In this version the measure is first copied into a field called `Sales` (the `agg` dataset), which "
                "keeps the rest of the spec independent of the measure's name."]}, w=W, h=H, interacting_rows=RI)


def ch_treemap():
    h1("11. Treemap with category headers (Vega)")
    p("**What you'll build:** a two-level treemap: a box per Category with a header, divided into Sub-categories "
      "sized by sales and coloured by profit.")
    image(REPO / "renders" / "pbip_tableau2_treemap_normal.png", 5.0, "The finished chart")
    fields_table([["Category", "Sales", "outer boxes"], ["SubCategory", "Sales", "inner boxes"],
                  ["Total Sales", "_Measures", "box size"], ["Total Profit", "_Measures", "box colour"]])
    C = "ch11_treemap"
    M = ["Total Sales", "Total Profit"]
    R = dataset("Sales", ["Category", "SubCategory"], M); RI = dataset("Sales", ["Category", "SubCategory"], M, interacting=True)
    W, H = 520, 360
    data = [{"name": "dataset"},
            {"name": "leaf", "source": "dataset", "transform": [
                {"type": "formula", "expr": "datum.Category + '|' + datum.SubCategory", "as": "id"},
                {"type": "formula", "expr": "datum.Category", "as": "parent"}]},
            {"name": "cats", "source": "dataset", "transform": [
                {"type": "aggregate", "groupby": ["Category"]},
                {"type": "formula", "expr": "datum.Category", "as": "id"},
                {"type": "formula", "expr": "'root'", "as": "parent"}]},
            {"name": "rootNode", "values": [{"id": "root", "parent": None}]},
            {"name": "tree", "source": ["rootNode", "cats", "leaf"], "transform": [
                {"type": "stratify", "key": "id", "parentKey": "parent"},
                {"type": "treemap", "field": "Total Sales", "method": "squarify", "round": True,
                 "size": [{"signal": "width"}, {"signal": "height"}], "paddingInner": 2}]},
            {"name": "leaves", "source": "tree", "transform": [{"type": "filter", "expr": "datum.SubCategory"}]}]
    rect = {"type": "rect", "from": {"data": "leaves"},
            "encode": {"update": {"x": {"field": "x0"}, "y": {"field": "y0"}, "x2": {"field": "x1"}, "y2": {"field": "y1"},
                                  "fill": {"value": "#4e79a7"}, "stroke": {"value": "white"}}}}
    s1 = {"$schema": VG, "data": data, "marks": [rect]}
    step(C, 1, "A three-level tree and the treemap layout", s1, R, {"do": ["Create a new Vega spec and paste:"],
         "why": ["This time the tree has three levels: root → Category → SubCategory. `leaf` gives each row an id "
                 "(`Furniture|Chairs` — unique even if two categories shared a sub-category name) and its Category as "
                 "parent. `cats` creates one node per Category: an `aggregate` with only `groupby` simply lists the "
                 "distinct categories.",
                 "`treemap` computes a rectangle (`x0, y0, x1, y1`) for every node, with areas proportional to "
                 "`Total Sales`. `squarify` keeps boxes close to square. We draw only the leaves (rows that have a "
                 "SubCategory); `x2`/`y2` set the opposite corner of each `rect`."]}, w=W, h=H)
    s2 = deep(s1)
    s2["scales"] = [{"name": "color", "type": "linear", "domain": {"data": "leaves", "field": "Total Profit"},
                     "range": ["#e8a87c", "#5b8fc7", "#1f4e89"], "zero": False}]
    s2["legends"] = [{"fill": "color", "title": "Profit", "orient": "bottom", "direction": "horizontal", "format": ",.0f", "gradientLength": 200}]
    s2["padding"] = {"top": 5, "left": 5, "right": 5, "bottom": 50}
    s2["marks"][0]["encode"]["update"]["fill"] = {"scale": "color", "field": "Total Profit"}
    s2 = {k: s2[k] for k in ["$schema", "padding", "data", "scales", "legends", "marks"]}
    step(C, 2, "Colour by profit", s2, R, {"do": ["Add a linear colour scale and legend; leave room for the legend with `padding`:"],
         "why": ["A **linear** scale with a three-colour `range` interpolates orange → mid blue → dark blue, so "
                 "low-profit boxes look warm and high-profit boxes cool (Tableau's orange-blue diverging palette). "
                 "`zero: false` lets the domain start at the smallest profit rather than 0."]},
         show=[("scales", "\"scales\":"), ("legends", "\"legends\":"), ("padding", "\"padding\":")], w=W, h=H)
    s3 = deep(s2)
    s3["data"][4]["transform"][1].update({"paddingTop": 18, "paddingOuter": 0})
    s3["data"].append({"name": "groups", "source": "tree", "transform": [{"type": "filter", "expr": "datum.depth == 1"}]})
    s3["marks"] = [{"type": "rect", "from": {"data": "groups"},
                    "encode": {"update": {"x": {"field": "x0"}, "y": {"field": "y0"}, "x2": {"field": "x1"}, "y2": {"field": "y1"},
                                          "fill": {"value": "#f3f3f3"}}}},
                   {"type": "text", "from": {"data": "groups"},
                    "encode": {"update": {"x": {"signal": "datum.x0 + 4"}, "y": {"signal": "datum.y0 + 13"},
                                          "text": {"field": "Category"}, "fontWeight": {"value": "bold"}, "fill": {"value": "#333"}}}}] + s3["marks"]
    step(C, 3, "Category headers", s3, R, {
        "do": ["Reserve 18 px at the top of each Category box, then draw a grey box and a bold title for each Category:"],
        "why": ["`paddingTop: 18` in the treemap transform leaves an 18 px strip at the top of every *parent* box. "
                "The `groups` dataset keeps only the Category level (`depth == 1`: root is 0, leaves are 2). Its grey "
                "`rect` is drawn first (behind) and the text sits in the reserved strip."]},
        show=[("data[4].transform[1]", "Updated treemap transform:"), ("data[6]", "New dataset:"),
              ("marks[0]", "New first mark:"), ("marks[1]", "New second mark:")], w=W, h=H)
    s4 = deep(B.vega_treemap()); s4.pop("config", None)
    step(C, 4, "Leaf labels, tooltips and selection", s4, R, {"do": ["Replace with the final spec:"],
         "why": ["Each leaf gets a two-line label (`text` can be an array — one line per item). `limit` cuts the text "
                 "with an ellipsis if it is wider than the box minus 8 px. The leaf rect has a tooltip and the usual "
                 "`__selected__` opacity rule. Clicking a Category header box filters to the whole category: Deneb "
                 "matches its Category value to the rows."]}, w=W, h=H, interacting_rows=RI)


def build():
    ch_heatmap(); pagebreak()
    ch_dualaxis(); pagebreak()
    ch_bullet(); pagebreak()
    ch_scatter(); pagebreak()
    ch_barinbar(); pagebreak()
    ch_bubbles(); pagebreak()
    ch_treemap(); pagebreak()
