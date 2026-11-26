from tutorial_lib import *  # noqa: F401,F403


def build():
    # ======================================================================= Introduction
    h1("How to use this guide")
    p("This guide teaches you to rebuild every Deneb chart in the **DenebShowcase** report from an empty visual. "
      "The goal is not just to copy specs but to understand them well enough to build your own charts.")
    p("Each chart chapter follows the same pattern:")
    bullets([
        "**What you'll build** — the finished chart and the Power BI fields it needs.",
        "**Steps** — the chart is built in 4–6 small steps. Each step tells you exactly what to add and where, "
        "explains *why* it works, and shows a picture of the result at that point.",
        "**Every step is saved as a file** in `tableau-to-powerbi/tutorial/steps/` (e.g. `ch01_heatmap_step3.json`). "
        "If you get lost, paste that file into the Deneb editor and carry on.",
        "**Check your understanding** — small exercises to try on your own.",
    ])
    p("Chapters 1–4 are the foundations. Read them first even if you are in a hurry: every chart chapter assumes them. "
      "Chapters 5–11 are the Tableau-style charts (pages 1–2 of the report), chapters 12–15 the NYT-style charts "
      "(pages 3–5). Appendices cover troubleshooting and a quick reference.")
    note("tip", "Work inside the DenebShowcase report: it already has all the tables and measures the chapters use. "
         "Add a new page called **Practice** and build each chart there, next to the finished version for comparison.")
    table(["Text style", "Meaning"], [
        ["**bold**", "something you click, type or should notice"],
        ["`code`", "a field name, property or value exactly as it is written in the spec"],
        ["grey code box", "JSON you type or paste into the Deneb editor"],
    ], [2200, 7160])

    # ======================================================================= Chapter 1
    h1("1. How Deneb works")
    h2("1.1 The big picture")
    p("Deneb is a Power BI visual that draws whatever you describe in a **specification** (spec) written in one of two "
      "languages: **Vega-Lite** (short and high-level, good for most charts) or **Vega** (longer and lower-level, needed "
      "for layouts such as packed bubbles, treemaps and maps). Both are JSON: nested `{ \"key\": value }` objects.")
    steps_list([
        "You drag columns and measures into the visual's single **Values** well, like any Power BI visual.",
        "Power BI runs the query: it groups by the columns and evaluates the measures in the current filter context "
        "(slicers, page filters, cross-filters).",
        "Deneb receives the result as a table called `dataset` and passes it to your spec.",
        "Vega-Lite / Vega draw the chart. When the data changes (a slicer moves), steps 2–4 repeat automatically.",
    ])
    h2("1.2 What `dataset` looks like")
    p("For the highlight table in chapter 5 we add **Region**, **SubCategory** and the measure **Total Sales**. "
      "Power BI returns one row per Region × SubCategory combination, with the measure already calculated:")
    rows = dataset("Sales", ["Region", "SubCategory"], ["Total Sales"])
    show = [{k: (round(v) if isinstance(v, float) else v) for k, v in r.items()} for r in rows[:4]]
    code(cjson(show), label="First 4 rows of dataset (as JSON)")
    p("Three things to notice:")
    bullets([
        "**Field names are the display names** from Power BI: `Region`, `SubCategory`, `Total Sales`. Spaces are fine. "
        "The characters `. [ ] \\ \"` are replaced by `_`. If you rename a field in the Values well, the name in the "
        "spec must change too.",
        "**Deneb adds helper fields** whose names start with two underscores: `__row__` (row number), `__selected__` "
        "(is this row selected?) and, for each measure, `<measure>__highlight` and `<measure>__highlightStatus`. "
        "Chapter 4 explains how to use them for interactivity.",
        "**One row per combination of columns.** If you add OrderID as well, you get one row per order. Choose the "
        "columns to match the level of detail you want to draw.",
    ])
    note("why", "Let Power BI do the totals with DAX measures, and let the spec do the drawing. Totals calculated by "
         "measures respect slicers and filters the same way the rest of the report does, and they keep each drawn mark "
         "linked to real rows, which is what makes click-to-filter work.")

    # ======================================================================= Chapter 2
    h1("2. Setting up and the Deneb editor")
    h2("2.1 One-time setup")
    steps_list([
        "Open **DenebShowcase.pbip** in Power BI Desktop and click **Refresh** so the tables load.",
        "Check Deneb is installed: you should see its icon at the end of the **Visualizations** pane. If not, use "
        "**… → Get more visuals**, search **Deneb**, click **Add** (publisher shown as Daniel Marsh-Patrick).",
        "Add a page: right-click a page tab → **New page** → rename it **Practice**.",
    ])
    h2("2.2 Create a Deneb visual and open the editor")
    steps_list([
        "Click an empty area of the page, then click the **Deneb** icon. An empty Deneb visual appears.",
        "With the visual selected, tick the fields you need in the **Data** pane (or drag them into **Values**).",
        "Make the visual larger (drag its corner) — the editor preview uses this size.",
        "Click the visual's **…** (More options) → **Edit**. The Deneb editor opens.",
        "The first time, Deneb asks you to create a specification: choose **Vega-Lite** or **Vega**, pick the "
        "**empty** template (the one without a pre-built chart), and click **Create**.",
    ])
    h2("2.3 A tour of the editor")
    table(["Area", "What it is for"], [
        ["**Specification** tab (left)", "Your spec. This is where you type or paste JSON."],
        ["**Config** tab (left)", "Shared styling (fonts, colours, axis look). Kept separate so the spec stays about the chart itself."],
        ["**Settings** tab (left)", "Interactivity switches: tooltips, context menu, cross-filtering, cross-highlighting."],
        ["**Apply** button / **Ctrl+Enter**", "Re-draws the preview with your changes. There is also an auto-apply toggle."],
        ["Preview (right)", "The chart, drawn at the visual's real size."],
        ["Debug area (bottom right)", "**Data** shows the exact `dataset` rows Deneb received (check field names here!). "
                                      "**Signals** shows Vega signals. **Logs** shows errors and warnings."],
        ["Back to report (top)", "Closes the editor. Your spec is saved inside the visual."],
    ], [3000, 6360])
    note("tip", "When a chart is blank, open the **Data** table first: nine times out of ten a field name in the spec "
         "doesn't exactly match the name in the table (spelling, spaces or capital letters). Then check **Logs**.")
    h2("2.4 The working rhythm")
    bullets([
        "Start with the smallest spec that draws *something*, then add one thing at a time and press **Apply** after each.",
        "If it breaks, undo the last change (**Ctrl+Z**) and read the error in **Logs**.",
        "JSON is strict: every key in double quotes, commas *between* items but never after the last one, matching "
        "`{}` and `[]`. The editor underlines mistakes in red.",
        "Save a copy of a working spec (or use the step files in this guide) before a big change.",
    ])

    # ======================================================================= Chapter 3
    h1("3. Vega-Lite in one chapter")
    p("Vega-Lite describes a chart with a handful of building blocks. Learn these and you can read any Vega-Lite spec.")
    h2("3.1 The smallest useful spec")
    s = {"$schema": VL, "data": {"name": "dataset"}, "mark": "bar",
         "encoding": {"y": {"field": "SubCategory", "type": "nominal"},
                      "x": {"field": "Total Sales", "type": "quantitative"}}}
    code(cjson(s), label="A bar chart in 8 lines")
    image(render(s, dataset("Sales", ["SubCategory"], ["Total Sales"]), "f_minimal_bar", 460, 230), 4.2,
          "What it draws (fields: SubCategory, Total Sales)")
    table(["Key", "Meaning"], [
        ["`$schema`", "Which language and version. Tells the editor how to check your spec. Always the first line."],
        ["`data`", "Where rows come from. In Deneb always `{\"name\": \"dataset\"}`."],
        ["`mark`", "The shape drawn for each row: `bar`, `line`, `point`, `rect`, `text`, `tick`, `rule`, `area`, `arc`…"],
        ["`encoding`", "Which field controls which visual property (*channel*): position (`x`, `y`), `color`, `size`, "
                       "`opacity`, `shape`, `text`, `tooltip`…"],
    ], [1800, 7560])
    h2("3.2 Field types")
    p("Every encoded field needs a `type`, which decides the kind of scale and axis:")
    table(["type", "Use for", "Scale you get"], [
        ["`nominal`", "categories with no order (Region, Category)", "separate bands / distinct colours"],
        ["`ordinal`", "categories with an order (YearMonth as text, PeriodsAgo)", "bands in sorted order / colour ramp"],
        ["`quantitative`", "numbers you measure (Total Sales, Margin)", "continuous axis from a minimum to a maximum"],
        ["`temporal`", "real dates and times", "time axis"],
    ], [1800, 4200, 3360])
    h2("3.3 Mark properties vs encodings")
    p("A **mark property** is the same for every row: `\"mark\": {\"type\": \"bar\", \"color\": \"#4e79a7\"}`. "
      "An **encoding** depends on the data: `\"color\": {\"field\": \"Category\", \"type\": \"nominal\"}`. A fixed value "
      "inside encoding is written `{\"value\": ...}`, and a rule-based value uses `condition` (see 3.6).")
    h2("3.4 Layers")
    p("`layer` stacks several marks on the same axes: bars plus a line, rectangles plus text labels, and so on. Anything "
      "put in the top-level `encoding` is shared by all layers; each layer adds its own `mark` and extra encodings.")
    code(cjson({"encoding": {"x": "…shared…", "y": "…shared…"},
                "layer": [{"mark": "rect", "encoding": {"color": "…"}}, {"mark": "text", "encoding": {"text": "…"}}]}),
         label="Shape of a layered spec")
    p("When two layers need *different* scales on the same channel (Sales in thousands vs a ratio in %), add "
      "`\"resolve\": {\"scale\": {\"y\": \"independent\"}}`. That is how a Tableau dual axis is built (chapter 6).")
    h2("3.5 Transforms: calculating inside the spec")
    p("`transform` is a list of steps applied to the rows *before* drawing, in order. The ones used in this guide:")
    table(["Transform", "What it does", "Example"], [
        ["`calculate`", "adds a new field from an expression", "`{\"calculate\": \"datum['Total Target'] * 0.8\", \"as\": \"B80\"}`"],
        ["`filter`", "keeps rows where the expression is true", "`{\"filter\": \"datum.Margin < 0\"}`"],
        ["`joinaggregate`", "adds a group total to every row (rows are kept)", "max Sales across all rows → `maxSales`"],
        ["`window`", "ranks / running values / previous-next row", "`rank`, `dense_rank`, `lag`, `lead`"],
        ["`aggregate`", "collapses rows into groups (rows are replaced)", "rarely needed — use DAX measures instead"],
        ["`regression`", "fits a trend line", "`{\"regression\": \"Total Profit\", \"on\": \"Total Sales\"}`"],
    ], [1800, 3600, 3960])
    p("In expressions, `datum` is the current row. Use `datum.Region` for simple names and `datum['Total Sales']` for "
      "names with spaces or symbols.")
    h2("3.6 Conditions")
    code(cjson({"color": {"condition": {"test": "datum['Total Sales'] > 100000", "value": "white"}, "value": "#333"}}),
         label="If the test is true use the first value, otherwise the second")
    h2("3.7 Scales, axes and legends")
    bullets([
        "`scale` controls how data maps to the channel: `{\"scheme\": \"blues\"}` for a colour ramp, "
        "`{\"domain\": [\"Met\", \"Missed\"], \"range\": [\"#4e79a7\", \"#e15759\"]}` to pin colours, "
        "`{\"domain\": [-45, 45]}` to fix an axis range.",
        "`axis` controls the axis: `title`, `orient` (`top`/`bottom`/`left`/`right`), `format` (`\"~s\"` = 120k, "
        "`\".0%\"` = 15%), `labelAngle`, `grid`, `labelExpr` (an expression that rewrites each label).",
        "`legend` does the same for legends; `\"legend\": null` hides it. `\"title\": null` hides a title.",
    ])
    h2("3.8 Config")
    p("`config` sets defaults for the whole chart (fonts, colours, axis styling). In Deneb, put it in the **Config** tab "
      "so the spec stays short and the same look can be reused across charts. The Tableau look used in chapters 5–9 is "
      "a config — see section 5, step 6.")

    # ======================================================================= Chapter 4
    h1("4. Vega basics and interactivity")
    h2("4.1 When you need Vega")
    p("Vega-Lite *compiles to* Vega. Vega is more verbose because you spell out everything Vega-Lite does for you — "
      "scales, axes, marks and data flow — but that also lets you use **layouts** Vega-Lite does not have: circle packing, "
      "treemaps, map projections and hierarchical data. Chapters 10, 11, 14 and 15 use Vega.")
    h2("4.2 The parts of a Vega spec")
    table(["Section", "What it holds"], [
        ["`data`", "A list of named datasets. Start with `{\"name\": \"dataset\"}` (from Power BI), then derive new "
                   "datasets with `\"source\"` + `\"transform\"`. Each dataset is a step in a pipeline."],
        ["`signals`", "Named values or expressions (like variables). `width` and `height` are signals Deneb sets for you."],
        ["`scales`", "Functions from data to visuals: `{\"name\": \"color\", \"type\": \"ordinal\", \"domain\": …, \"range\": …}`."],
        ["`projections`", "For maps: how longitude/latitude become x/y (`albersUsa`, `orthographic`, `mercator`…)."],
        ["`axes` / `legends`", "Explicit axes and legends (Vega-Lite creates these automatically, Vega does not)."],
        ["`marks`", "What to draw. Each mark has `type` (`symbol`, `rect`, `text`, `line`, `rule`, `shape`, `group`), "
                    "`from` (which dataset) and `encode` (how each row sets x, y, fill, size…)."],
    ], [2000, 7360])
    p("Inside `encode`, each property is an object: `{\"field\": \"x\"}` reads a field, `{\"value\": \"white\"}` is a "
      "constant, `{\"scale\": \"color\", \"field\": \"Category\"}` passes a field through a scale, and "
      "`{\"signal\": \"datum.r * 2\"}` evaluates an expression. Properties go in `enter` (set once) or `update` "
      "(re-evaluated on every change); this guide uses `update` throughout so it is always safe.")
    h2("4.3 Interactivity: making Deneb behave like a native visual")
    p("Three switches and two helper fields give you most of the Power BI behaviour:")
    table(["Feature", "Switch it on", "What to put in the spec"], [
        ["Tooltips", "Settings → **Tooltips**", "Vega-Lite: a `tooltip` encoding (list of fields). Vega: a `tooltip` "
                                               "property in `encode`."],
        ["Cross-filter (click to filter other visuals)", "Settings → **Cross-filtering**",
         "Nothing is required: clicking a mark selects its row. To *show* the selection, dim rows where "
         "`datum.__selected__ == 'off'`."],
        ["Cross-highlight (other visuals highlight this one)", "Settings → **Cross-highlighting**",
         "Draw `<measure>__highlight` (the highlighted part) on top of a faint copy of the full measure."],
        ["Context menu", "Settings → **Context menu**", "Nothing — right-click works on any mark."],
    ], [2500, 2700, 4160])
    p("`__selected__` is `neutral` when nothing is selected, `on` for the selected rows and `off` for the others. "
      "`<measure>__highlight` equals the measure when nothing is highlighted, and the highlighted portion when another "
      "visual highlights this one. `<measure>__highlightStatus` is `neutral`, `on` or `off` in the same way.")
    code(cjson({"opacity": {"condition": {"test": "datum.__selected__ == 'off'", "value": 0.25}, "value": 1}}),
         label="The selection pattern used in every chart in this guide")
    note("watch", "Click-to-filter works best when every mark is one row of `dataset`. If the spec merges rows itself "
         "(with `aggregate`), Deneb has to guess which rows you clicked by matching field values. It often works, but "
         "the reliable approach is to send totals from DAX measures, as all the charts here do.")
    pagebreak()
