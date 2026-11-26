"""Generate a Power BI Project (.pbip) that demonstrates Deneb with a fixed, embedded dataset.

Open  powerbi-sample/DenebShowcase/DenebShowcase.pbip  in Power BI Desktop.

* Data is embedded in Power Query (compressed CSV), so nothing external is needed.
* Pages 1-2: Tableau-style charts wired for cross-filtering / cross-highlighting.
* Pages 3-5: NYT-style charts (tiles, diverging bars, route map, globe) - illustrative data.

Usage:  python powerbi-sample/build_pbip.py
"""
import base64, csv, io, json, pathlib, shutil, sys, uuid, zlib

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
OUT = ROOT / "DenebShowcase"
NAME = "DenebShowcase"
DENEB = "deneb7E15AEF80B9E4D4F8E12924291ECE89A"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric"
sys.path.insert(0, str(REPO / "nyt-style"))
import build_specs as nyt  # noqa: E402

TAB = "\t"


def tag(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "deneb-showcase/" + "/".join(parts)))


def hexid(*parts):
    return uuid.uuid5(uuid.NAMESPACE_URL, "deneb-showcase-v/" + "/".join(parts)).hex[:20]


# ======================================================================================
# 1. DATA  (English Superstore-style sales + NYT-style illustrative tables)
# ======================================================================================
VI_EN = {"Miền Bắc": "North", "Miền Trung": "Central", "Miền Nam": "South", "Tây Nguyên": "West",
         "Cá nhân": "Consumer", "Doanh nghiệp": "Corporate", "Văn phòng tại gia": "Home Office",
         "Nội thất": "Furniture", "Văn phòng phẩm": "Office Supplies", "Công nghệ": "Technology",
         "Bàn": "Tables", "Ghế": "Chairs", "Kệ sách": "Bookcases", "Giấy": "Paper", "Bút": "Pens",
         "Bìa hồ sơ": "Binders", "Điện thoại": "Phones", "Máy in": "Printers", "Phụ kiện": "Accessories"}


def sales_rows():
    rows = []
    for r in csv.DictReader(open(REPO / "data/superstore_sample.csv", encoding="utf-8")):
        r = {k: VI_EN.get(v, v) for k, v in r.items()}
        r["Year"] = r["OrderDate"][:4]
        r["YearMonth"] = r["OrderDate"][:7]
        rows.append(r)
    return rows


def csv_rows(name, add_rowid=False):
    rows = list(csv.DictReader(open(REPO / "nyt-style/data" / name, encoding="utf-8")))
    if add_rowid:
        for i, r in enumerate(rows, 1): r["RowId"] = str(i)
    return rows


# table name -> (rows, {column: (tmdl dataType, M type, summarizeBy, formatString)})
S, I, D, T, DT = "string", "int64", "double", "type text", "dateTime"
TABLES = {
    "Sales": (sales_rows(), {
        "OrderID": (S, "type text", "none", None), "OrderDate": (DT, "type date", "none", "yyyy-mm-dd"),
        "Year": (I, "Int64.Type", "none", "0"), "YearMonth": (S, "type text", "none", None),
        "ShipDays": (I, "Int64.Type", "none", "0"), "Region": (S, "type text", "none", None),
        "Segment": (S, "type text", "none", None), "Category": (S, "type text", "none", None),
        "SubCategory": (S, "type text", "none", None), "Sales": (D, "type number", "sum", "#,0"),
        "Profit": (D, "type number", "sum", "#,0"), "Quantity": (I, "Int64.Type", "sum", "#,0"),
        "Target": (D, "type number", "sum", "#,0")}),
    "Streaks": (csv_rows("streaks.csv"), {
        "Product": (S, T, "none", None), "Period": (S, T, "none", None), "PeriodsAgo": (I, "Int64.Type", "none", "0"),
        "Result": (S, T, "none", None), "Note": (S, T, "none", None)}),
    "Balance": (csv_rows("balance.csv"), {
        "Year": (I, "Int64.Type", "none", "0"), "Margin": (I, "Int64.Type", "none", "0"), "Projected": (S, T, "none", None)}),
    "Routes": (csv_rows("routes.csv"), {
        "Origin": (S, T, "none", None), "OriginName": (S, T, "none", None),
        "OriginLon": (D, "type number", "none", None), "OriginLat": (D, "type number", "none", None),
        "Dest": (S, T, "none", None), "DestName": (S, T, "none", None),
        "DestLon": (D, "type number", "none", None), "DestLat": (D, "type number", "none", None),
        "Cancelled": (I, "Int64.Type", "none", "0")}),
    "Tankers": (csv_rows("tankers.csv", add_rowid=True), {
        "Kind": (S, T, "none", None), "Id": (I, "Int64.Type", "none", "0"), "Seq": (I, "Int64.Type", "none", "0"),
        "Lane": (S, T, "none", None), "Lon": (D, "type number", "none", None), "Lat": (D, "type number", "none", None),
        "RowId": (I, "Int64.Type", "none", "0")}),
}

MEASURES = [  # name, DAX, format
    ("Total Sales", "SUM(Sales[Sales])", "#,0"),
    ("Total Profit", "SUM(Sales[Profit])", "#,0"),
    ("Total Target", "SUM(Sales[Target])", "#,0"),
    ("Profit Ratio", "DIVIDE([Total Profit], [Total Sales])", "0.0%"),
    ("Attainment %", "DIVIDE([Total Sales], [Total Target])", "0.0%"),
    ("Orders", "COUNTROWS(Sales)", "#,0"),
]


def embed(rows, cols):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    for r in rows: w.writerow([r[c] for c in cols])
    co = zlib.compressobj(9, zlib.DEFLATED, -15)  # raw DEFLATE = M's Compression.Deflate
    data = co.compress(buf.getvalue().encode("utf-8")) + co.flush()
    return base64.b64encode(data).decode()


def m_query(name, rows, cols):
    b64 = embed(rows, list(cols))
    types = ", ".join(f'{{"{c}", {spec[1]}}}' for c, spec in cols.items())
    return [
        "let",
        f'    Source = Csv.Document(Binary.Decompress(Binary.FromText("{b64}", BinaryEncoding.Base64), Compression.Deflate), '
        f'[Delimiter=",", Columns={len(cols)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f'    Typed = Table.TransformColumnTypes(Promoted, {{{types}}}, "en-US")',
        "in",
        "    Typed",
    ]


# ======================================================================================
# 2. SEMANTIC MODEL (TMDL)
# ======================================================================================
def tmdl_name(n):
    return f"'{n}'" if any(ch in n for ch in " .=:'%") else n


def write_model():
    sm = OUT / f"{NAME}.SemanticModel"
    d = sm / "definition"
    (d / "tables").mkdir(parents=True)
    (sm / "definition.pbism").write_text(json.dumps({
        "$schema": f"{SCHEMA}/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {}}, indent=2))
    (sm / ".platform").write_text(json.dumps({
        "$schema": f"{SCHEMA}/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": tag("sm")}}, indent=2))
    (d / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1600\n\n")
    tables = list(TABLES) + ["_Measures"]
    model = ["model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
             "\tdiscourageImplicitMeasures", "\tsourceQueryCulture: en-US", "\tdataAccessOptions",
             "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
             "annotation __PBI_TimeIntelligenceEnabled = 0", "",
             f"annotation PBI_QueryOrder = {json.dumps(list(TABLES))}", ""]
    model += [f"ref table {tmdl_name(t)}" for t in tables]
    (d / "model.tmdl").write_text("\n".join(model) + "\n")

    for t, (rows, cols) in TABLES.items():
        L = [f"table {tmdl_name(t)}", f"\tlineageTag: {tag(t)}", ""]
        for c, (dtype, _, summ, fmt) in cols.items():
            L += [f"\tcolumn {tmdl_name(c)}", f"\t\tdataType: {dtype}"]
            if fmt: L.append(f"\t\tformatString: {fmt}")
            L += [f"\t\tlineageTag: {tag(t, c)}", f"\t\tsummarizeBy: {summ}", f"\t\tsourceColumn: {c}", "",
                  "\t\tannotation SummarizationSetBy = User", ""]
        L += [f"\tpartition {tmdl_name(t)} = m", "\t\tmode: import", "\t\tsource ="]
        L += ["\t\t\t\t" + line for line in m_query(t, rows, cols)]
        L += ["", "\tannotation PBI_ResultType = Table", ""]
        (d / "tables" / f"{t}.tmdl").write_text("\n".join(L))

    L = ["table _Measures", f"\tlineageTag: {tag('_Measures')}", ""]
    for n, dax, fmt in MEASURES:
        L += [f"\tmeasure {tmdl_name(n)} = {dax}", f"\t\tformatString: {fmt}", f"\t\tlineageTag: {tag('m', n)}", ""]
    L += ["\tcolumn Placeholder", "\t\tdataType: string", "\t\tisHidden", f"\t\tlineageTag: {tag('_Measures', 'p')}",
          "\t\tsummarizeBy: none", "\t\tsourceColumn: [Placeholder]", "",
          "\tpartition _Measures = calculated", "\t\tmode: import", '\t\tsource = ROW("Placeholder", "")', ""]
    (d / "tables" / "_Measures.tmdl").write_text("\n".join(L))


# ======================================================================================
# 3. DENEB SPECS
# ======================================================================================
TAB10 = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac"]
TABLEAU_CONFIG = {
    "autosize": {"type": "fit", "contains": "padding"},
    "view": {"stroke": None},
    "font": "Segoe UI",
    "axis": {"labelColor": "#666", "titleColor": "#333", "gridColor": "#eee", "domainColor": "#ccc", "tickColor": "#ccc",
             "labelFontSize": 11, "titleFontSize": 12, "titleFontWeight": "normal"},
    "legend": {"labelColor": "#555", "titleColor": "#333"},
    "range": {"category": TAB10},
}
VL = "https://vega.github.io/schema/vega-lite/v5.json"
SEL = {"test": "datum.__selected__ == 'off'", "value": 0.25}  # dim points not selected (cross-filter)


def hl(f):  # cross-highlight field name Deneb adds for measure f
    return f + "__highlight"


SPEC_HEAT = {
    "$schema": VL, "description": "Highlight table - click a cell to cross-filter; other visuals highlight it",
    "data": {"name": "dataset"},
    "transform": [{"joinaggregate": [{"op": "max", "field": "Total Sales", "as": "maxSales"}]}],
    "encoding": {"x": {"field": "Region", "type": "nominal", "axis": {"orient": "top", "title": None, "labelAngle": 0}},
                 "y": {"field": "SubCategory", "type": "nominal", "title": None}},
    "layer": [
        {"mark": {"type": "rect", "stroke": "white", "strokeWidth": 1.5},
         "encoding": {"color": {"field": hl("Total Sales"), "type": "quantitative", "title": "Sales",
                                "scale": {"scheme": "blues"}, "legend": {"format": "~s"}},
                      "opacity": {"condition": SEL, "value": 1},
                      "tooltip": [{"field": "Region"}, {"field": "SubCategory"},
                                  {"field": "Total Sales", "format": ",.0f"}, {"field": hl("Total Sales"), "title": "Highlighted", "format": ",.0f"}]}},
        {"mark": {"type": "text", "fontSize": 11},
         "encoding": {"text": {"field": hl("Total Sales"), "type": "quantitative", "format": ",.0f"},
                      "color": {"condition": {"test": "datum['Total Sales__highlight'] > datum.maxSales * 0.55", "value": "white"},
                                "value": "#333"},
                      "opacity": {"condition": SEL, "value": 1}}}],
}

SPEC_COMBO = {
    "$schema": VL, "description": "Dual axis: Sales bars (highlightable) + Profit Ratio line",
    "data": {"name": "dataset"},
    "encoding": {"x": {"field": "YearMonth", "type": "ordinal", "title": None,
                       "axis": {"labelAngle": -45, "labelExpr": "indexof(['01','04','07','10'], slice(datum.value, 5)) >= 0 ? datum.value : ''"}}},
    "layer": [
        {"layer": [
            {"mark": {"type": "bar", "color": "#4e79a7", "opacity": 0.3},
             "encoding": {"y": {"field": "Total Sales", "type": "quantitative", "title": "Sales",
                                "axis": {"titleColor": "#4e79a7", "format": "~s"}}}},
            {"mark": {"type": "bar", "color": "#4e79a7"},
             "encoding": {"y": {"field": hl("Total Sales"), "type": "quantitative"},
                          "opacity": {"condition": {"test": "datum.__selected__ == 'off'", "value": 0}, "value": 1},
                          "tooltip": [{"field": "YearMonth", "title": "Month"}, {"field": "Total Sales", "format": ",.0f"},
                                      {"field": "Profit Ratio", "format": ".1%"}]}}]},
        {"mark": {"type": "line", "color": "#f28e2b", "strokeWidth": 2.5, "point": {"filled": True, "color": "#f28e2b"}},
         "encoding": {"y": {"field": "Profit Ratio", "type": "quantitative", "title": "Profit ratio",
                            "axis": {"format": ".0%", "titleColor": "#f28e2b", "grid": False}},
                      "tooltip": [{"field": "YearMonth", "title": "Month"}, {"field": "Profit Ratio", "format": ".1%"}]}}],
    "resolve": {"scale": {"y": "independent"}},
}

SPEC_BULLET = {
    "$schema": VL, "description": "Bullet graph: grey bands = 60/80/100/120% of target, bar = actual, tick = target",
    "data": {"name": "dataset"},
    "transform": [{"calculate": f"datum['Total Target'] * {k}", "as": f"B{int(k * 100)}"} for k in (0.6, 0.8, 1.2)],
    "encoding": {"y": {"field": "Category", "type": "nominal", "title": None}},
    "layer": [
        {"mark": {"type": "bar", "color": "#e6e6e6", "size": 30}, "encoding": {"x": {"field": "B120", "type": "quantitative", "title": "Sales vs target", "axis": {"format": "~s"}}}},
        {"mark": {"type": "bar", "color": "#cfcfcf", "size": 30}, "encoding": {"x": {"field": "Total Target", "type": "quantitative"}}},
        {"mark": {"type": "bar", "color": "#b5b5b5", "size": 30}, "encoding": {"x": {"field": "B80", "type": "quantitative"}}},
        {"mark": {"type": "bar", "color": "#9e9e9e", "size": 30}, "encoding": {"x": {"field": "B60", "type": "quantitative"}}},
        {"mark": {"type": "bar", "color": "#4e79a7", "size": 12, "opacity": 0.35}, "encoding": {"x": {"field": "Total Sales", "type": "quantitative"}}},
        {"mark": {"type": "bar", "color": "#4e79a7", "size": 12},
         "encoding": {"x": {"field": hl("Total Sales"), "type": "quantitative"},
                      "opacity": {"condition": {"test": "datum.__selected__ == 'off'", "value": 0}, "value": 1},
                      "tooltip": [{"field": "Category"}, {"field": "Total Sales", "format": ",.0f"},
                                  {"field": "Total Target", "format": ",.0f"}, {"field": "Attainment %", "format": ".1%"}]}},
        {"mark": {"type": "tick", "color": "black", "thickness": 3, "size": 28}, "encoding": {"x": {"field": "Total Target", "type": "quantitative"}}}],
}

SPEC_SCATTER = {
    "$schema": VL, "description": "Scatter with trend line and average lines (quadrants)",
    "data": {"name": "dataset"},
    "layer": [
        {"mark": {"type": "point", "filled": True, "size": 110},
         "encoding": {"x": {"field": "Total Sales", "type": "quantitative", "title": "Sales", "axis": {"format": "~s"}},
                      "y": {"field": "Total Profit", "type": "quantitative", "title": "Profit", "axis": {"format": "~s"}},
                      "color": {"field": "Category", "type": "nominal"},
                      "shape": {"field": "Region", "type": "nominal"},
                      "opacity": {"condition": [SEL, {"test": "datum['Total Sales__highlightStatus'] == 'off'", "value": 0.25}], "value": 0.9},
                      "tooltip": [{"field": "SubCategory"}, {"field": "Region"}, {"field": "Total Sales", "format": ",.0f"},
                                  {"field": "Total Profit", "format": ",.0f"}]}},
        {"mark": {"type": "line", "color": "#777", "strokeDash": [4, 3]},
         "transform": [{"regression": "Total Profit", "on": "Total Sales"}],
         "encoding": {"x": {"field": "Total Sales", "type": "quantitative"}, "y": {"field": "Total Profit", "type": "quantitative"}}},
        {"mark": {"type": "rule", "color": "#bbb"}, "encoding": {"x": {"aggregate": "mean", "field": "Total Sales", "type": "quantitative"}}},
        {"mark": {"type": "rule", "color": "#bbb"}, "encoding": {"y": {"aggregate": "mean", "field": "Total Profit", "type": "quantitative"}}}],
}

SPEC_BARINBAR = {
    "$schema": VL, "description": "Bar-in-bar: target (wide, light) vs actual (narrow, coloured by status)",
    "data": {"name": "dataset"},
    "transform": [{"calculate": "datum['Total Sales'] >= datum['Total Target'] ? 'Met' : 'Missed'", "as": "Status"}],
    "encoding": {"y": {"field": "SubCategory", "type": "nominal", "sort": "-x", "title": None}},
    "layer": [
        {"mark": {"type": "bar", "color": "#c7d6e8", "size": 22},
         "encoding": {"x": {"field": "Total Target", "type": "quantitative", "title": "Sales / Target", "axis": {"format": "~s"}}}},
        {"mark": {"type": "bar", "size": 10},
         "encoding": {"x": {"field": hl("Total Sales"), "type": "quantitative"},
                      "color": {"field": "Status", "type": "nominal", "title": None,
                                "scale": {"domain": ["Met", "Missed"], "range": ["#4e79a7", "#e15759"]}},
                      "opacity": {"condition": SEL, "value": 1},
                      "tooltip": [{"field": "SubCategory"}, {"field": "Total Sales", "format": ",.0f"},
                                  {"field": "Total Target", "format": ",.0f"}, {"field": "Attainment %", "format": ".1%"}]}}],
}


def vega_bubbles():
    s = json.loads((REPO / "deneb/08_packed_bubbles.vega.json").read_text(encoding="utf-8"))
    s.pop("width", None); s.pop("height", None)
    for d in s["data"]:
        if d.get("name") == "agg":  # Power BI already aggregates via the measure
            d["transform"] = [{"type": "formula", "expr": "datum['Total Sales']", "as": "Sales"}]
    s["description"] = "Tableau-style packed bubbles: size = Sales by SubCategory, colour = Category"
    u = s["marks"][0]["encode"]["update"]
    u["fillOpacity"] = {"signal": "datum.__selected__ == 'off' ? 0.3 : 1"}
    return s


def vega_treemap():
    s = json.loads((REPO / "deneb/09_treemap.vega.json").read_text(encoding="utf-8"))
    s.pop("width", None); s.pop("height", None)
    for d in s["data"]:
        if d.get("name") == "leaf":
            d["transform"] = [{"type": "formula", "expr": "datum['Total Sales']", "as": "Sales"},
                              {"type": "formula", "expr": "datum['Total Profit']", "as": "Profit"},
                              {"type": "formula", "expr": "datum.Category+'|'+datum.SubCategory", "as": "id"},
                              {"type": "formula", "expr": "datum.Category", "as": "parent"}]
    s["legends"][0]["title"] = "Profit"
    s["description"] = "Tableau-style treemap: Category > SubCategory, size = Sales, colour = Profit"
    s["marks"][2]["encode"]["update"]["fillOpacity"] = {"signal": "datum.__selected__ == 'off' ? 0.3 : 1"}
    return s


# ======================================================================================
# 4. REPORT (PBIR)
# ======================================================================================
def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def strlit(s):
    return lit("'" + s.replace("'", "''") + "'")


def col(table, column):
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}},
            "queryRef": f"{table}.{column}", "nativeQueryRef": column}


def meas(name):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": name}},
            "queryRef": f"_Measures.{name}", "nativeQueryRef": name}


def container(page, key, x, y, w, h, z, visual, title=None):
    v = {"$schema": f"{SCHEMA}/item/report/definition/visualContainer/2.8.0/schema.json",
         "name": hexid(page, key), "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
         "visual": visual}
    if title is not None:
        visual.setdefault("visualContainerObjects", {})["title"] = [{"properties": {
            "show": lit("true"), "text": strlit(title), "fontSize": lit("12D")}}]
    return v


def deneb(page, key, x, y, w, h, z, fields, spec, title, provider="vegaLite", config=None, interactive=True):
    return container(page, key, x, y, w, h, z, {
        "visualType": DENEB,
        "query": {"queryState": {"dataset": {"projections": fields}}},
        "objects": {"vega": [{"properties": {
            "provider": strlit(provider),
            "jsonSpec": strlit(json.dumps(spec, ensure_ascii=False, indent=2)),
            "jsonConfig": strlit(json.dumps(config or {}, indent=2)),
            "enableTooltips": lit("true"),
            "enableContextMenu": lit("true"),
            "enableSelection": lit("true" if interactive else "false"),
            "enableHighlight": lit("true" if interactive else "false"),
            "selectionMode": strlit("simple"),
            "selectionMaxDataPoints": lit("100D")}}]},
        "drillFilterOtherVisuals": True}, title)


def slicer(page, key, x, y, w, h, z, table, column, title):
    return container(page, key, x, y, w, h, z, {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [dict(col(table, column), active=True)]}}},
        "drillFilterOtherVisuals": True}, title)


def card(page, key, x, y, w, h, z, measure):
    return container(page, key, x, y, w, h, z, {
        "visualType": "card",
        "query": {"queryState": {"Values": {"projections": [meas(measure)]}}},
        "drillFilterOtherVisuals": True})


def bar(page, key, x, y, w, h, z, table, column, measure, title):
    return container(page, key, x, y, w, h, z, {
        "visualType": "clusteredBarChart",
        "query": {"queryState": {"Category": {"projections": [dict(col(table, column), active=True)]},
                                 "Y": {"projections": [meas(measure)]}},
                  "sortDefinition": {"sort": [{"field": meas(measure)["field"], "direction": "Descending"}]}},
        "drillFilterOtherVisuals": True}, title)


def textbox(page, key, x, y, w, h, z, paragraphs):
    paras = []
    for p in paragraphs:
        runs = p if isinstance(p, list) else [p]
        paras.append({"textRuns": [{"value": r[0], "textStyle": r[1]} if isinstance(r, tuple) else {"value": r} for r in runs]})
    return container(page, key, x, y, w, h, z, {
        "visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": paras}}]},
        "drillFilterOtherVisuals": True})


BOLD = {"fontWeight": "bold"}
H1 = {"fontWeight": "bold", "fontSize": "18pt"}


def pages():
    P = {}
    # ---------------- Page 1: Tableau-style interactive -------------------------------------
    p = "tableau1"
    P[p] = ("1. Tableau-style (interactive)", [
        textbox(p, "t", 20, 8, 900, 62, 1, [
            [("Deneb + Power BI: Tableau-style charts", H1)],
            "Try it: click a cell / bar / category in any chart (Ctrl+click for multi-select), use the slicers, "
            "or click a Segment bar to cross-highlight. Edit a chart: select it > ... > Edit."]),
        slicer(p, "sy", 940, 8, 150, 120, 2, "Sales", "Year", "Year"),
        slicer(p, "sr", 1100, 8, 160, 120, 3, "Sales", "Region", "Region"),
        card(p, "c1", 20, 78, 220, 70, 4, "Total Sales"),
        card(p, "c2", 250, 78, 220, 70, 5, "Profit Ratio"),
        card(p, "c3", 480, 78, 220, 70, 6, "Attainment %"),
        deneb(p, "heat", 20, 160, 480, 330, 10,
              [col("Sales", "Region"), col("Sales", "SubCategory"), meas("Total Sales")],
              SPEC_HEAT, "Highlight table: Sales by Region x Sub-category", config=TABLEAU_CONFIG),
        bar(p, "seg", 20, 500, 480, 200, 11, "Sales", "Segment", "Total Sales", "Native bar: click to cross-highlight Deneb"),
        deneb(p, "combo", 515, 160, 745, 330, 12,
              [col("Sales", "YearMonth"), meas("Total Sales"), meas("Profit Ratio")],
              SPEC_COMBO, "Dual axis: monthly Sales and Profit Ratio", config=TABLEAU_CONFIG),
        deneb(p, "bullet", 515, 500, 745, 200, 13,
              [col("Sales", "Category"), meas("Total Sales"), meas("Total Target"), meas("Attainment %")],
              SPEC_BULLET, "Bullet graph: Sales vs Target by Category", config=TABLEAU_CONFIG),
    ])
    # ---------------- Page 2: Tableau-style more ---------------------------------------------
    p = "tableau2"
    P[p] = ("2. Tableau-style (more)", [
        slicer(p, "sc", 1100, 8, 160, 110, 1, "Sales", "Category", "Category"),
        textbox(p, "t", 20, 8, 1060, 50, 2, [[("Scatter, bar-in-bar (Vega-Lite) - packed bubbles & treemap (Vega)", H1)]]),
        deneb(p, "scatter", 20, 70, 620, 320, 10,
              [col("Sales", "SubCategory"), col("Sales", "Region"), col("Sales", "Category"), meas("Total Sales"), meas("Total Profit")],
              SPEC_SCATTER, "Scatter with trend & average lines", config=TABLEAU_CONFIG),
        deneb(p, "barinbar", 650, 125, 610, 265, 11,
              [col("Sales", "SubCategory"), meas("Total Sales"), meas("Total Target"), meas("Attainment %")],
              SPEC_BARINBAR, "Bar-in-bar: Sales vs Target", config=TABLEAU_CONFIG),
        deneb(p, "bubbles", 20, 400, 620, 310, 12,
              [col("Sales", "Category"), col("Sales", "SubCategory"), meas("Total Sales")],
              vega_bubbles(), "Packed bubbles (Vega)", provider="vega"),
        deneb(p, "treemap", 650, 400, 610, 310, 13,
              [col("Sales", "Category"), col("Sales", "SubCategory"), meas("Total Sales"), meas("Total Profit")],
              vega_treemap(), "Treemap: size = Sales, colour = Profit (Vega)", provider="vega"),
    ])
    # ---------------- Page 3: NYT-style charts -------------------------------------------------
    p = "nyt1"
    note = ("Illustrative, randomly generated data", {"fontStyle": "italic", "color": "#777777"})
    P[p] = ("3. NYT-style charts", [
        textbox(p, "t", 20, 8, 1240, 50, 1, [[("NYT-style charts in Deneb", H1)], [note]]),
        deneb(p, "streak", 20, 60, 470, 650, 10,
              [col("Streaks", c) for c in ("Product", "Period", "PeriodsAgo", "Result", "Note")],
              nyt.streak, "Quarters since each product line last beat target"),
        deneb(p, "balance", 510, 60, 750, 650, 11,
              [col("Balance", c) for c in ("Year", "Margin", "Projected")],
              nyt.balance, "Margin vs target by year ($k)"),
    ])
    p = "nyt2"
    P[p] = ("4. NYT-style US route map", [
        deneb(p, "usmap", 20, 10, 1240, 700, 10,
              [col("Routes", c) for c in TABLES["Routes"][1]],
              nyt.us_map(), "Cancelled shipments (illustrative data)", provider="vega", interactive=False),
    ])
    p = "nyt3"
    P[p] = ("5. NYT-style globe", [
        deneb(p, "globe", 20, 10, 1240, 700, 10,
              [col("Tankers", c) for c in TABLES["Tankers"][1]],
              nyt.globe(), None, provider="vega", interactive=False),
    ])
    return P


def write_report():
    rp = OUT / f"{NAME}.Report"
    d = rp / "definition"
    d.mkdir(parents=True)
    (rp / "definition.pbir").write_text(json.dumps({
        "$schema": f"{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}}, indent=2))
    (rp / ".platform").write_text(json.dumps({
        "$schema": f"{SCHEMA}/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": tag("report")}}, indent=2))
    theme_dir = rp / "StaticResources/SharedResources/BaseThemes"
    theme_dir.mkdir(parents=True)
    shutil.copy(ROOT / "assets/CY24SU10.json", theme_dir / "CY24SU10.json")
    (d / "version.json").write_text(json.dumps({
        "$schema": f"{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"}, indent=2))
    (d / "report.json").write_text(json.dumps({
        "$schema": f"{SCHEMA}/item/report/definition/report/3.2.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": {"visual": "1.8.97", "report": "2.0.97", "page": "1.3.97"},
                                          "type": "SharedResources"}},
        "publicCustomVisuals": [DENEB],
        "resourcePackages": [{"name": "SharedResources", "type": "SharedResources",
                              "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True,
                     "allowChangeFilterTypes": True, "useEnhancedTooltips": True}}, indent=2))
    P = pages()
    (d / "pages").mkdir()
    (d / "pages/pages.json").write_text(json.dumps({
        "$schema": f"{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": list(P), "activePageName": list(P)[0]}, indent=2))
    for pid, (title, visuals) in P.items():
        pd = d / "pages" / pid
        (pd / "visuals").mkdir(parents=True)
        page = {"$schema": f"{SCHEMA}/item/report/definition/page/2.1.0/schema.json",
                "name": pid, "displayName": title, "displayOption": "FitToPage", "height": 720, "width": 1280}
        if pid.startswith("nyt"):
            page["objects"] = {"background": [{"properties": {"color": {"solid": {"color": strlit("#F4F4F4")}},
                                                              "transparency": lit("0D")}}]}
        (pd / "page.json").write_text(json.dumps(page, indent=2))
        for v in visuals:
            (pd / "visuals" / v["name"]).mkdir()
            (pd / "visuals" / v["name"] / "visual.json").write_text(json.dumps(v, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / f"{NAME}.pbip").write_text(json.dumps({
        "$schema": f"{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0",
        "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}}, indent=2))
    (OUT / ".gitignore").write_text("**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
    write_model()
    write_report()
    n = sum(1 for _ in OUT.rglob("*") if _.is_file())
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1024
    print(f"Wrote {OUT} ({n} files, {size:.0f} KB)")


if __name__ == "__main__":
    main()
