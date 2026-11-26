from tutorial_lib import *  # noqa: F401,F403

US = json.loads((REPO / "nyt-style/geo/us_states.json").read_text())
WORLD = json.loads((REPO / "nyt-style/geo/world_countries.json").read_text())
BG = "#f4f4f4"


def fields(rows):
    table(["Field (drag into Values)", "From table", "Role"], rows, [2600, 1800, 4960])


def ch_streak():
    h1("12. Streak tiles (NYT style)")
    p("**What you'll build:** one column per product line. Each tile is a quarter, newest at the top; red tiles are "
      "quarters that missed target, and the column ends at the last quarter that beat it (blue). Columns are sorted by "
      "streak length, the three longest streaks are annotated, and a serif headline fills the empty corner.")
    image(REPO / "renders" / "nyt_01_streak_tiles.png", 3.4, "The finished chart (report page 3)")
    fields([["Product", "Streaks", "the column"], ["Period", "Streaks", "tile label, e.g. 2025 Q3"],
            ["PeriodsAgo", "Streaks", "tile position: 0 = newest, at the top"], ["Result", "Streaks", "Beat / Missed → colour"],
            ["Note", "Streaks", "footnote marker (* or †) added to the label"]])
    note("why", "The data is already one row per tile, so there are **no measures** in this chart. The `Streaks` table "
         "is illustrative. To use your own data, build a table with the same five columns, e.g. from a fact table in "
         "Power Query or with DAX.")
    C = "ch12_streak"
    R = dataset("Streaks", ["Product", "Period", "PeriodsAgo", "Result", "Note"])
    W, H = 430, 700
    s1 = {"$schema": VL, "data": {"name": "dataset"}, "mark": "rect",
          "encoding": {"x": {"field": "Product", "type": "nominal"}, "y": {"field": "PeriodsAgo", "type": "ordinal"}}}
    step(C, 1, "A grid of tiles", s1, R, {"do": ["Paste:"],
         "why": ["Exactly like the highlight table in chapter 5, but y is `PeriodsAgo` as **ordinal**, so 0 is at the top "
                 "and each product's column is as long as its history. Columns are alphabetical for now."]}, w=W, h=H, img_w=3.0)
    s2 = deep(s1)
    s2["mark"] = {"type": "rect", "cornerRadius": 2}
    s2["encoding"]["x"] = {"field": "Product", "type": "nominal", "title": None,
                           "sort": {"field": "PeriodsAgo", "op": "max", "order": "ascending"},
                           "scale": {"paddingInner": 0.1, "paddingOuter": 0.02},
                           "axis": {"orient": "top", "domain": False, "ticks": False, "labelAngle": 0}}
    s2["encoding"]["y"] = {"field": "PeriodsAgo", "type": "ordinal", "axis": None,
                           "scale": {"paddingInner": 0.14, "paddingOuter": 0}}
    s2["encoding"]["color"] = {"field": "Result", "type": "nominal", "legend": None,
                               "scale": {"domain": ["Beat", "Missed"], "range": ["#2f73b8", "#df7a7a"]}}
    step(C, 2, "Sort by streak, colour and spacing", s2, R, {
        "do": ["Replace the encodings:"],
        "why": ["**Sorting by another field:** `sort: {field: \"PeriodsAgo\", op: \"max\", order: \"ascending\"}` orders "
                "the columns by each product's largest PeriodsAgo, i.e. its streak length — short columns on the left, "
                "the longest on the right, which creates the staircase.",
                "`paddingInner` on the band scales makes the gaps between tiles (as a fraction of the band). "
                "`axis: null` removes the y axis entirely; the x axis is moved to the top without its line or ticks. "
                "`cornerRadius` softens the tiles."]}, show=[("encoding", "\"encoding\":"), ("mark", "\"mark\":")], w=W, h=H, img_w=3.0)
    s3 = {"$schema": VL, "data": {"name": "dataset"},
          "transform": [{"calculate": "datum.Period + datum.Note", "as": "label"}],
          "encoding": s2["encoding"] | {},
          "layer": [{"mark": s2["mark"], "encoding": {"color": s2["encoding"]["color"]}},
                    {"mark": {"type": "text", "fontSize": 11},
                     "encoding": {"text": {"field": "label"}, "color": {"value": "white"},
                                  "fontWeight": {"condition": {"test": "datum.Result == 'Beat'", "value": "bold"}, "value": "normal"}}}]}
    s3["encoding"] = {k: v for k, v in s2["encoding"].items() if k != "color"}
    step(C, 3, "Label every tile", s3, R, {
        "do": ["Move to a layer (tiles + text) and build the label with a calculate transform:"],
        "why": ["`datum.Period + datum.Note` joins two text fields: `2025 Q3` + `*` = `2025 Q3*`. `color` moves "
                "into the tile layer only, so the text layer can be white. Bold labels on the blue tiles draw the eye to "
                "the quarters that beat target."]},
        show=[("transform", "Top level:"), ("layer[1]", "Text layer:")], w=W, h=H, img_w=3.0)
    s4 = deep(s3)
    s4["transform"].insert(0, {"joinaggregate": [{"op": "max", "field": "PeriodsAgo", "as": "streakLen"}], "groupby": ["Product"]})
    s4["layer"].append({
        "transform": [{"filter": "datum.PeriodsAgo == datum.streakLen && datum.Result == 'Beat' && datum.streakLen >= 3"},
                      {"window": [{"op": "dense_rank", "as": "rk"}], "sort": [{"field": "streakLen", "order": "descending"}]},
                      {"filter": "datum.rk <= 3"},
                      {"calculate": "[(datum.streakLen - 1) + ' consecutive', 'missed quarters', 'for ' + datum.Product]", "as": "note"}],
        "mark": {"type": "text", "align": "right", "baseline": "bottom", "dx": -46, "dy": 4, "fontSize": 11, "lineHeight": 13},
        "encoding": {"text": {"field": "note"}}})
    step(C, 4, "Annotate the three longest streaks", s4, R, {
        "do": ["Add a `joinaggregate` that finds each product's streak length, and an annotation layer:"],
        "why": ["`joinaggregate` with `groupby: [\"Product\"]` writes each product's maximum PeriodsAgo onto all of "
                "its rows as `streakLen`.",
                "The annotation layer has its **own** transforms: keep only the bottom tile of each column (the last "
                "\"Beat\"), rank those by streak length with `dense_rank`, keep the top 3 and build a 3-line note (a text "
                "array = one line per item). `align: right` with `dx: -46` places the note to the left of the tile.",
                "Because everything is computed, the annotations move by themselves when the data changes."]},
        show=[("transform[0]", "Add first in \"transform\":"), ("layer[2]", "New layer:")], w=W, h=H, img_w=3.0)
    s5 = deep(N.streak)
    step(C, 5, "Headline, background and interactivity", s5, R, {"do": ["Replace with the final spec:"],
         "why": ["The headline is a text layer with its **own inline data** (`data: {values: [...]}`), so it is drawn once "
                 "rather than once per row. Its position uses pixel values: `x: {value: 0}` and "
                 "`y: {value: {expr: \"height * 0.55\"}}` — just over halfway down, whatever size the visual is.",
                 "`background` sets the light grey NYT page colour; tiles get a tooltip and the usual selection opacity."]},
         w=W, h=H, img_w=3.0)


def ch_diverging():
    h1("13. Diverging bars (\"balance of power\")")
    p("**What you'll build:** one horizontal bar per year, extending left (below target, blue) or right (above target, "
      "red) from a central zero line, with smart labels on the peaks and a lighter projected bar.")
    image(REPO / "renders" / "nyt_02_diverging_balance.png", 4.4, "The finished chart")
    fields([["Year", "Balance", "one bar per year"], ["Margin", "Balance", "signed value, negative = below target"],
            ["Projected", "Balance", "Yes for the forecast year"]])
    C = "ch13_diverging"
    R = dataset("Balance", ["Year", "Margin", "Projected"])
    W, H = 600, 620
    s1 = {"$schema": VL, "data": {"name": "dataset"}, "mark": "bar",
          "encoding": {"y": {"field": "Year", "type": "ordinal"}, "x": {"field": "Margin", "type": "quantitative"}}}
    step(C, 1, "Bars that go both ways", s1, R, {"do": ["Paste:"],
         "why": ["A quantitative x scale that contains negative values automatically includes zero, so bars grow left "
                 "for negative margins and right for positive ones. `Year` is ordinal so each year is one band."]}, w=W, h=H, img_w=4.0)
    s2 = deep(s1)
    s2["transform"] = [{"calculate": "datum.Projected == 'Yes' ? 'Projected' : (datum.Margin < 0 ? 'Below' : 'Above')", "as": "Side"}]
    s2["encoding"]["color"] = {"field": "Side", "type": "nominal", "legend": None,
                               "scale": {"domain": ["Below", "Above", "Projected"], "range": ["#5394cf", "#e07a7a", "#9dc3e6"]}}
    s2 = {k: s2[k] for k in ["$schema", "data", "transform", "mark", "encoding"]}
    step(C, 2, "Colour by side", s2, R, {"do": ["Classify each row, then colour by the class:"],
         "why": ["A nested ternary (`a ? b : (c ? d : e)`) gives three classes. The projected year is checked first so "
                 "it wins over the sign. Pinning `domain`/`range` fixes the colours."]},
         show=[("transform", "Top level:"), ("encoding.color", "Add to encoding:")], w=W, h=H, img_w=4.0)
    s3 = deep(s2)
    s3["background"] = BG
    s3["encoding"]["y"] = {"field": "Year", "type": "ordinal", "title": None, "scale": {"paddingInner": 0.06},
                           "axis": {"domain": False, "ticks": False, "labelColor": "#8a8a8a", "labelFontSize": 13, "labelPadding": 14,
                                    "labelExpr": "datum.value % 10 == 0 || datum.value == 2026 ? datum.label : ''"}}
    s3["encoding"]["x"] = {"field": "Margin", "type": "quantitative", "title": None, "scale": {"domain": [-45, 45]},
                           "axis": {"orient": "top", "values": [-40, -30, -20, -10, 0, 10, 20, 30, 40], "domain": False, "ticks": False,
                                    "grid": True, "gridColor": "#dddddd", "labelColor": "#8a8a8a", "labelFontSize": 13,
                                    "labelExpr": "datum.value == 0 ? 'Even' : '+' + abs(datum.value)"}}
    s3["config"] = {"view": {"stroke": None}}
    step(C, 3, "NYT-style axes", s3, R, {"do": ["Restyle both axes and fix the x range:"],
         "why": ["`scale.domain: [-45, 45]` makes the axis symmetrical, so \"Even\" is exactly in the middle. `values` "
                 "lists the exact tick positions.",
                 "`labelExpr` rewrites the labels: both sides show `+N` (the size of the lead, not a negative number) "
                 "and zero shows `Even`. On the y axis only decades (`% 10 == 0`) and 2026 keep their label.",
                 "`background` and `config.view.stroke: null` give the flat grey look."]},
        show=[("encoding.x", "x encoding:"), ("encoding.y", "y encoding:")], w=W, h=H, img_w=4.0)
    s4 = deep(s3)
    bar = {"mark": {"type": "bar"}, "encoding": {"x": s4["encoding"].pop("x"), "color": s4["encoding"].pop("color")}}
    s4["layer"] = [bar, {"mark": {"type": "rule", "color": "#111", "strokeWidth": 2}, "encoding": {"x": {"datum": 0}}}]
    s4.pop("mark")
    s4 = {k: s4[k] for k in ["$schema", "data", "background", "transform", "encoding", "layer", "config"]}
    step(C, 4, "The centre line", s4, R, {"do": ["Make it a layer and add a black `rule` at zero:"],
         "why": ["`\"x\": {\"datum\": 0}` places the rule at the data value 0 on the x scale (unlike `value`, which "
                 "would mean 0 *pixels*). A rule with only x spans the full height."]}, show=[("layer[1]", "Second layer:")], w=W, h=H, img_w=4.0)
    s5 = deep(N.balance)
    step(C, 5, "Smart labels and side headers", s5, R, {"do": ["Replace with the final spec:"],
         "why": ["`window` with `lag`/`lead` copies the previous and next year's margin onto each row, so an expression "
                 "can ask \"is this bar bigger than both neighbours?\" — a local peak. A second window ranks bars by size "
                 "to find the overall largest. `showLabel` combines the rules (peaks ≥ 10, the largest, zero and the "
                 "projection); `label` builds the text.",
                 "Labels on the left must be right-aligned and labels on the right left-aligned. Text alignment is a mark "
                 "property, not an encoding, so there are **two text layers**, one filtered to negative margins and one to "
                 "positive margins. The \"Below target / Above target\" headers are a layer with inline data placed at "
                 "x = ±30 above the plot (`dy: -30`)."]}, w=W, h=H, img_w=4.0)


def ch_usmap():
    h1("14. US bubble + route map (Vega)")
    p("**What you'll build:** a US map (Alaska and Hawaii inset) with a circle per airport sized by cancellations, grey "
      "lines for cancelled routes, the seven busiest airports ringed and labelled, and KPI totals across the top.")
    image(REPO / "renders" / "nyt_03_us_route_map.png", 5.6, "The finished chart (report page 4)")
    fields([["Origin, OriginName, OriginLon, OriginLat", "Routes", "start airport code, name and coordinates"],
            ["Dest, DestName, DestLon, DestLat", "Routes", "end airport"], ["Cancelled", "Routes", "count for the route"]])
    note("why", "Each row is a **route**. Airports are not a separate table: the spec derives them from the two ends of "
         "the routes. Set every coordinate column's *Summarization* to **Don't summarize** in the model (already done in "
         "the showcase), otherwise Power BI would add up latitudes.")
    h2("Getting the map outline into the spec")
    p("Deneb (like every certified visual) cannot download files, so the US outline must be **inside** the spec. The "
      "file `tableau-to-powerbi/nyt-style/geo/us_states.json` (23 KB of TopoJSON) is pasted as the `values` of a "
      "dataset. In the code boxes below it is shown as `\"<contents of us_states.json>\"`; the step files in "
      "`tutorial/steps/` already contain it, so you can paste those directly.")
    steps_list(["Open `us_states.json` in Notepad and select all (**Ctrl+A**), copy (**Ctrl+C**).",
                "In the spec, replace the placeholder text *including its quotes* with the copied content.",
                "Press **Apply**. The file starts with `{\"type\":\"Topology\"` — if you see that after `\"values\":`, it is in the right place."])
    C = "ch14_usmap"
    R = dataset("Routes", list(B.TABLES["Routes"][1]))
    W, H = 760, 480
    ph = "<contents of us_states.json>"
    base_data = [{"name": "dataset"}, {"name": "states", "values": US, "format": {"type": "topojson", "feature": "states"}}]
    proj = [{"name": "proj", "type": "albersUsa", "fit": {"signal": "data('states')"}, "size": {"signal": "[width, height]"}}]
    states = {"type": "shape", "from": {"data": "states"}, "transform": [{"type": "geoshape", "projection": "proj"}],
              "encode": {"update": {"fill": {"value": "#e4e4e4"}, "stroke": {"value": "white"}, "strokeWidth": {"value": 1}}}}
    s1 = {"$schema": VG, "autosize": "none", "data": deep(base_data), "projections": proj, "marks": [states]}
    step(C, 1, "Draw the map", s1, R, {"do": ["Create a new **Vega** spec with all nine fields and paste (then insert the TopoJSON):"],
         "why": ["`format: {type: \"topojson\", feature: \"states\"}` tells Vega the values are TopoJSON and to extract "
                 "the object called `states` as one map feature per state.",
                 "A **projection** turns longitude/latitude into x/y. `albersUsa` is a US-specific projection that moves "
                 "Alaska and Hawaii into insets. `fit` + `size` scale and centre it so the states fill the visual.",
                 "The `shape` mark with a `geoshape` transform draws each feature as a path: light grey with white "
                 "borders. `dataset` is declared but not used yet.",
                 "`\"autosize\": \"none\"` keeps the chart exactly the size of the visual. Vega's default "
                 "(`pad`) enlarges the drawing to fit every mark, which for maps and large circles makes the chart "
                 "spill out of the visual."]},
        placeholder=ph, w=W, h=H, img_w=5.4)
    end = lambda pfx: [{"type": "formula", "expr": f"datum.{pfx}", "as": "code"},  # noqa: E731
                       {"type": "formula", "expr": f"datum.{pfx}Name", "as": "name"},
                       {"type": "formula", "expr": f"datum.{pfx}Lon", "as": "lon"},
                       {"type": "formula", "expr": f"datum.{pfx}Lat", "as": "lat"}]
    airports = [{"name": "o", "source": "dataset", "transform": end("Origin")},
                {"name": "d", "source": "dataset", "transform": end("Dest")},
                {"name": "airports", "source": ["o", "d"], "transform": [
                    {"type": "aggregate", "groupby": ["code", "name", "lon", "lat"], "fields": ["Cancelled"], "ops": ["sum"], "as": ["n"]},
                    {"type": "geopoint", "projection": "proj", "fields": ["lon", "lat"]}]}]
    dots = {"type": "symbol", "from": {"data": "airports"},
            "encode": {"update": {"x": {"field": "x"}, "y": {"field": "y"}, "size": {"value": 60}, "fill": {"value": "#e8892c"}}}}
    s2 = {"$schema": VG, "data": deep(base_data) + airports, "projections": proj, "marks": [states, dots]}
    step(C, 2, "Derive airports from the routes", s2, R, {
        "do": ["Add three datasets after `states`, and a `symbol` mark:"],
        "why": ["Datasets `o` and `d` rename the origin and destination columns to the same names (`code`, `name`, "
                "`lon`, `lat`). `airports` stacks them (`source: [\"o\", \"d\"]`) and `aggregate`s by airport, summing "
                "`Cancelled` into `n`: every cancellation counts at both ends of its route.",
                "`geopoint` runs each airport's lon/lat through the projection and adds pixel coordinates `x` and `y`, "
                "which the symbol mark uses."]},
        show=[("data[2]", "Dataset o:"), ("data[4]", "Dataset airports (d is like o with Dest):"), ("marks[1]", "New mark:")],
        placeholder=ph, w=W, h=H, img_w=5.4)
    s3 = deep(s2)
    s3["scales"] = [{"name": "size", "type": "linear", "domain": {"data": "airports", "field": "n"}, "zero": True, "range": [0, 4200]}]
    s3["data"][4]["transform"].append({"type": "collect", "sort": {"field": "n", "order": "ascending"}})
    s3["marks"][1]["encode"]["update"].update({"size": {"scale": "size", "field": "n"}, "fill": {"value": "#f4b46a"},
                                               "fillOpacity": {"value": 0.55}, "stroke": {"value": "#e8892c"}, "strokeWidth": {"value": 0.8},
                                               "tooltip": {"signal": "{'Airport': datum.name, 'Cancelled': datum.n}"}})
    s3 = {k: s3[k] for k in ["$schema", "data", "projections", "scales", "marks"]}
    step(C, 3, "Size circles by cancellations", s3, R, {
        "do": ["Add a size scale and update the circle style; sort the airports so small ones draw last:"],
        "why": ["Vega's symbol `size` is an **area**, and readers judge circles by area, so a **linear** scale from 0 "
                "makes area proportional to the count: twice the cancellations, twice the ink. (Using radius would "
                "exaggerate big airports.)",
                "`collect` sorts the rows by `n` ascending, so the largest circles are drawn first and small ones stay "
                "visible on top. Transparent fill with a solid orange edge reproduces the NYT look."]},
        show=[("scales", "\"scales\":"), ("marks[1].encode.update", "Circle properties:")], placeholder=ph, w=W, h=H, img_w=5.4)
    s4 = deep(s3)
    s4["data"].append({"name": "routes", "source": "dataset", "transform": [
        {"type": "geopoint", "projection": "proj", "fields": ["OriginLon", "OriginLat"], "as": ["x1", "y1"]},
        {"type": "geopoint", "projection": "proj", "fields": ["DestLon", "DestLat"], "as": ["x2", "y2"]}]})
    s4["marks"].insert(1, {"type": "rule", "from": {"data": "routes"},
                           "encode": {"update": {"x": {"field": "x1"}, "y": {"field": "y1"}, "x2": {"field": "x2"}, "y2": {"field": "y2"},
                                                 "stroke": {"value": "#7d7d7d"}, "strokeOpacity": {"value": 0.3}, "strokeWidth": {"value": 0.7}}}})
    step(C, 4, "Route lines", s4, R, {"do": ["Project both ends of every route and draw a `rule` between them, *before* the circles:"],
         "why": ["`geopoint` can run twice with different `as` names, giving the start (`x1, y1`) and end (`x2, y2`) "
                 "in pixels. A `rule` mark draws a straight line between two points. With 400+ lines, low opacity "
                 "(0.3) lets busy corridors appear darker. Marks are drawn in order, so lines go between the map and "
                 "the circles."]}, show=[("data[5]", "New dataset:"), ("marks[1]", "New mark (second in the list):")],
         placeholder=ph, w=W, h=H, img_w=5.4)
    s5 = deep(s4)
    s5["data"][4]["transform"].insert(2, {"type": "window", "sort": {"field": "n", "order": "descending"}, "ops": ["row_number"], "as": ["rank"]})
    upd = s5["marks"][2]["encode"]["update"]
    upd["stroke"] = [{"test": "datum.rank <= 7", "value": "#111"}, {"value": "#e8892c"}]
    upd["strokeWidth"] = [{"test": "datum.rank <= 7", "value": 2}, {"value": 0.8}]
    s5["marks"].append({"type": "text", "from": {"data": "airports"}, "encode": {"update": {
        "x": {"field": "x"}, "y": {"signal": "datum.y + sqrt(scale('size', datum.n) / PI) + 11"},
        "text": {"signal": "datum.rank <= 7 ? datum.name + ' ' + datum.n : ''"}, "align": {"value": "center"},
        "fontWeight": {"value": "bold"}, "fontSize": {"value": 12}, "fill": {"value": "#111"}}}})
    step(C, 5, "Ring and label the top seven", s5, R, {
        "do": ["Rank airports, give the top 7 a black ring, and add a label mark:"],
        "why": ["`window` with `row_number` sorted by `n` descending numbers the airports 1, 2, 3… The `stroke` "
                "property is a list of rules: black and 2 px for rank ≤ 7, otherwise orange.",
                "The label sits just below each circle: `scale('size', datum.n)` returns the circle's area, "
                "`sqrt(area / PI)` its radius, plus 11 px. All other airports get an empty label."]},
        show=[("data[4].transform[2]", "Add to the airports transforms:"), ("marks[3]", "New label mark:")],
        placeholder=ph, w=W, h=H, img_w=5.4)
    s6 = deep(N.us_map())
    step(C, 6, "KPI header and final layout", s6, R, {"do": ["Replace with the final spec (insert the TopoJSON again):"],
         "why": ["The KPI numbers come from two small aggregate datasets: `kpi` counts airports and `kpi2` counts routes "
                 "and sums cancellations. A `group` mark with `from: {data: \"kpi\"}` draws its text marks once, using "
                 "that single row. Like everything else, they update with slicers.",
                 "The projection now uses `extent` instead of `size`: `[[20, top], [width - 20, height - 10]]` fits the "
                 "map into a box that starts 90 px down (`top` is a signal), leaving room for the header. Name and count "
                 "are now two separate text marks so the count can be lighter."]},
         placeholder=ph, w=1000, h=700, img_w=6.0)


def ch_globe():
    h1("15. Globe with routes (Vega, orthographic)")
    p("**What you'll build:** a 3D-looking globe centred on the Indian Ocean, with a shaded ocean, country outlines, "
      "hundreds of semi-transparent sea routes that glow where they overlap, red position dots and place labels.")
    image(REPO / "renders" / "nyt_04_globe_routes.png", 5.8, "The finished chart (report page 5)")
    fields([["Kind", "Tankers", "Route (a waypoint) or Position (a dot)"], ["Id", "Tankers", "which route a waypoint belongs to"],
            ["Seq", "Tankers", "waypoint order along the route"], ["Lane, Lon, Lat", "Tankers", "lane name and coordinates"],
            ["RowId", "Tankers", "unique id so identical rows are not merged"]])
    note("why", "Deneb has a single `dataset`, so routes and positions share one table and the `Kind` column separates "
         "them. A route is a sequence of waypoint rows (same `Id`, increasing `Seq`). `RowId` matters: Power BI merges "
         "identical rows, and two positions could happen to have the same values.")
    p("As in chapter 14, the map outline is pasted in: this time `nyt-style/geo/world_countries.json` (60 KB), shown as "
      "`\"<contents of world_countries.json>\"`.")
    C = "ch15_globe"
    R = dataset("Tankers", list(B.TABLES["Tankers"][1]))
    W, H = 780, 540
    ph = "<contents of world_countries.json>"
    sig = [{"name": "centerLon", "value": 76}, {"name": "centerLat", "value": 10}, {"name": "zoom", "update": "width * 0.56"}]
    proj = [{"name": "proj", "type": "orthographic", "scale": {"signal": "zoom"},
             "rotate": [{"signal": "-centerLon"}, {"signal": "-centerLat"}, 0],
             "translate": [{"signal": "width / 2"}, {"signal": "height * 0.62"}]}]
    gdata = [{"name": "dataset"}, {"name": "world", "values": WORLD, "format": {"type": "topojson", "feature": "countries"}},
             {"name": "graticule", "transform": [{"type": "graticule", "step": [15, 15]}]},
             {"name": "sphere", "values": [{"type": "Sphere"}]}]
    geo = lambda d, enc: {"type": "shape", "from": {"data": d}, "transform": [{"type": "geoshape", "projection": "proj"}],  # noqa: E731
                          "encode": {"update": enc}}
    s1 = {"$schema": VG, "autosize": "none", "signals": sig, "data": deep(gdata), "projections": proj,
          "marks": [geo("sphere", {"fill": {"value": "#dfe4e8"}}),
                    geo("graticule", {"stroke": {"value": "#c9ced2"}, "strokeWidth": {"value": 0.5}, "fill": {"value": None}}),
                    geo("world", {"fill": {"value": "white"}, "stroke": {"value": "#b9b9b9"}, "strokeWidth": {"value": 0.6}})]}
    step(C, 1, "An orthographic globe", s1, R, {"do": ["Create a Vega spec with the seven fields and paste:"],
         "why": ["**orthographic** draws the Earth as seen from space. `rotate: [-lon, -lat]` turns the globe so the "
                 "point (76°E, 10°N) faces you; we keep those numbers in signals so they are easy to change.",
                 "`scale` (the zoom) is a signal based on the visual's width, and `translate` puts the globe's centre "
                 "62% of the way down, so the top is cropped like the original. `\"autosize\": \"none\"` is what allows "
                 "the cropping: without it Vega would grow the canvas to show the whole sphere (see chapter 14, step 1).",
                 "Three layers, drawn in order: the **sphere** (a special GeoJSON type meaning \"the whole globe\", used as "
                 "the ocean), a **graticule** (latitude/longitude grid generated by a transform) and the **countries**."],
         "notes": [("watch", "If the whole globe turns white, a country polygon is \"inside out\" (it happens after "
                              "simplifying shapes that cross the 180° line, like Fiji). The supplied file has been fixed.")]},
        placeholder=ph, w=W, h=H, img_w=5.6)
    s2 = deep(s1)
    s2["marks"][0]["encode"]["update"]["fill"] = {"value": {"gradient": "radial", "x1": 0.5, "y1": 0.5, "r1": 0.35, "x2": 0.5, "y2": 0.5, "r2": 0.5,
                                                            "stops": [{"offset": 0, "color": "#eef0f2"}, {"offset": 1, "color": "#cfd5da"}]}}
    s2["marks"][1]["encode"]["update"]["stroke"] = {"value": "#e3e6e8"}
    step(C, 2, "Shade the ocean", s2, R, {"do": ["Replace the sphere's fill with a radial gradient:"],
         "why": ["A radial gradient goes from the centre (`r1`, light) to the edge (`r2`, darker). Coordinates are "
                 "fractions of the shape's bounding box, so 0.5/0.5 is its centre. The darker rim makes the flat disc "
                 "read as a sphere."]}, show=[("marks[0].encode.update.fill", "Sphere fill:")], placeholder=ph, w=W, h=H, img_w=5.6)
    s3 = deep(s2)
    s3["data"].append({"name": "routes", "source": "dataset", "transform": [
        {"type": "filter", "expr": "datum.Kind == 'Route'"}, {"type": "collect", "sort": {"field": ["Id", "Seq"]}},
        {"type": "geopoint", "projection": "proj", "fields": ["Lon", "Lat"]}]})
    s3["marks"].append({"type": "group", "from": {"facet": {"name": "routeSeg", "data": "routes", "groupby": "Id"}},
                        "marks": [{"type": "line", "from": {"data": "routeSeg"},
                                   "encode": {"update": {"x": {"field": "x"}, "y": {"field": "y"}, "interpolate": {"value": "basis"},
                                                         "stroke": {"value": "#f2b300"}, "strokeOpacity": {"value": 0.16},
                                                         "strokeWidth": {"value": 1.6}}}}]})
    step(C, 3, "Draw the routes", s3, R, {
        "do": ["Add a `routes` dataset and a **group** mark that draws one line per route:"],
        "why": ["The dataset keeps only route waypoints, sorts them by route and order (`collect`), and projects them to "
                "x/y with `geopoint`.",
                "A single `line` mark would join *all* waypoints into one long line. A **facet group** splits the data "
                "by `Id` into one sub-dataset per route (`routeSeg`) and draws the inner `line` mark once for each.",
                "`interpolate: basis` turns the waypoint polyline into a smooth curve. Each line is only 16% opaque, so "
                "where dozens of routes overlap the colour builds up into a bright band — the effect in the NYT graphic."]},
        show=[("data[4]", "New dataset:"), ("marks[3]", "New mark:")], placeholder=ph, w=W, h=H, img_w=5.6)
    s4 = deep(s3)
    s4["data"].append({"name": "positions", "source": "dataset", "transform": [
        {"type": "filter", "expr": "datum.Kind == 'Position'"}, {"type": "geopoint", "projection": "proj", "fields": ["Lon", "Lat"]}]})
    s4["marks"].append({"type": "symbol", "from": {"data": "positions"},
                        "encode": {"update": {"x": {"field": "x"}, "y": {"field": "y"}, "size": {"value": 9},
                                              "fill": {"value": "#e8342b"}, "fillOpacity": {"value": 0.85}}}})
    step(C, 4, "Add the positions", s4, R, {"do": ["Same idea for the dots — filter, project, draw small red symbols:"],
         "why": ["`size: 9` is an area of 9 px², a dot about 3 px across. Drawn after the routes, the dots sit on top."]},
        show=[("data[5]", "New dataset:"), ("marks[4]", "New mark:")], placeholder=ph, w=W, h=H, img_w=5.6)
    s5 = deep(N.globe())
    step(C, 5, "Labels and legend", s5, R, {"do": ["Replace with the final spec (insert the TopoJSON again):"],
         "why": ["Place labels come from an inline dataset of name, lon, lat and kind (`city`, `key`, `country`, "
                 "`sea`). Each kind has its own colour, weight, size and style, looked up with an expression such as "
                 "`{\"city\": \"#222\", \"sea\": \"#7a7a7a\"}[datum.k]` — one text mark styles four kinds of label.",
                 "Cities get a black dot and their label is placed to the left or right depending on longitude so it "
                 "points away from the busy shipping lanes. The legend at the top is made of ordinary marks: a red "
                 "symbol, a short orange rule and two text marks."],
         "notes": [("tip", "Rotate the globe by changing `centerLon` / `centerLat` in `signals` — for example 0 and 45 "
                           "centres Europe.")]}, placeholder=ph, w=1100, h=760, img_w=6.0)


def appendices():
    pagebreak()
    h1("Appendix A — Troubleshooting")
    table(["Symptom", "Likely cause", "Fix"], [
        ["Visual is blank, no error", "A field name in the spec doesn't match `dataset`",
         "Open the editor's **Data** table; copy the exact names (spaces and capitals matter)."],
        ["Red underline / \"Unexpected token\"", "JSON syntax: missing or extra comma, unmatched bracket, single quotes around keys",
         "Look at the line before the underline. Keys and text values need double quotes."],
        ["Line or bar flat at the bottom", "Two layers sharing a y scale with very different ranges",
         "`\"resolve\": {\"scale\": {\"y\": \"independent\"}}` (chapter 6)."],
        ["Bars in the wrong order", "Default alphabetical sort", "`\"sort\": \"-x\"`, or `sort` by another field (chapter 12)."],
        ["Clicking does nothing", "Cross-filtering is off, or the spec aggregates rows",
         "Settings → Cross-filtering; send totals from DAX measures instead of `aggregate`."],
        ["Highlight has no effect", "Cross-highlighting is off, or the spec doesn't use `<measure>__highlight`", "Chapter 4.3 / step 5 of chapter 5."],
        ["Numbers summed wrongly / huge latitudes", "Columns default to Sum", "Set the column's *Summarization* to *Don't summarize* in the model."],
        ["Map is white / missing", "TopoJSON not inside `values`, wrong `feature` name, or an inside-out polygon",
         "Check `feature` matches the object name in the file (`states`, `countries`)."],
        ["Only part of the data shows", "Row limit", "Visual format → Deneb → **Data limit** → override row limit; or reduce detail."],
        ["Text cut off at the edges", "Labels outside the plot area", "Add `padding` at the top level, or shorten labels with `limit`."],
    ], [2700, 3200, 3460])
    h1("Appendix B — Quick reference")
    h3("Vega-Lite skeleton")
    code(cjson({"$schema": VL, "data": {"name": "dataset"}, "transform": [],
                "encoding": {"x": {"field": "…", "type": "nominal"}, "y": {"field": "…", "type": "quantitative"}},
                "layer": [{"mark": {"type": "bar"}}, {"mark": {"type": "text"}, "encoding": {"text": {"field": "…"}}}]}))
    h3("Vega skeleton")
    code(cjson({"$schema": VG, "signals": [], "data": [{"name": "dataset"}, {"name": "derived", "source": "dataset", "transform": []}],
                "scales": [], "projections": [], "axes": [], "legends": [],
                "marks": [{"type": "symbol", "from": {"data": "derived"}, "encode": {"update": {"x": {"field": "…"}}}}]}))
    h3("Formats (d3-format) and handy expressions")
    table(["Write", "Gets you"], [
        ["`\",.0f\"`", "12,345"], ["`\"~s\"`", "12.3k / 1.2M"], ["`\".1%\"`", "15.3%"], ["`\"$,.0f\"`", "$12,345"],
        ["`datum['Total Sales']`", "a field whose name has spaces"], ["`test ? a : b`", "if / else"],
        ["`format(datum.x, ',.0f')`", "formatted text inside an expression"], ["`slice(text, 5)`, `indexof(list, x)`", "text and list helpers"],
        ["`datum.__selected__ == 'off'`", "row is not selected while something else is"],
    ], [3600, 5760])
    h1("Appendix C — Files and further learning")
    table(["Where", "What"], [
        ["`tutorial/steps/*.json`", "Every step of every chapter, ready to paste (maps include the TopoJSON)."],
        ["`tutorial/steps/tableau_config.json`", "The Tableau-look Config used in chapters 5–9."],
        ["`deneb/`, `nyt-style/specs/`", "Final specs; `powerbi-sample/` contains the report itself."],
        ["`nyt-style/geo/`", "Simplified US states and world countries TopoJSON."],
        ["vega.github.io/vega-lite/examples", "Hundreds of Vega-Lite examples to adapt (replace their data with `{\"name\": \"dataset\"}`)."],
        ["vega.github.io/vega/docs", "Vega reference: transforms, marks, projections, expressions."],
        ["deneb.guide", "Deneb documentation: interactivity, templates, settings."],
    ], [3400, 5960])


def build():
    ch_streak(); pagebreak()
    ch_diverging(); pagebreak()
    ch_usmap(); pagebreak()
    ch_globe()
    appendices()
