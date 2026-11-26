"""Build NYT-style Deneb specs (Vega-Lite + Vega) and render PNG previews.

Every spec reads its data from Deneb's `dataset` (the fields you drop into the
visual in Power BI). Map outlines are embedded inline because certified
visuals such as Deneb cannot download files at runtime.

Usage: python nyt-style/build_specs.py        (needs: pip install vl-convert-python)
Outputs: nyt-style/specs/*.json  and  renders/nyt_*.png
"""
import csv, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
SPECS, GEO, DATA = HERE / "specs", HERE / "geo", HERE / "data"
RENDERS = HERE.parent / "renders"
SPECS.mkdir(exist_ok=True)
SANS = "Segoe UI"
SERIF = "Georgia"
GREY = "#8a8a8a"
BG = "#f4f4f4"

# --------------------------------------------------------------------------------------
# 1. Streak tiles (Vega-Lite)  — fields: Product, Period, PeriodsAgo, Result, Note
# --------------------------------------------------------------------------------------
streak = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": "NYT-style streak tiles: periods since each product last beat its target",
    "data": {"name": "dataset"},
    "background": BG,
    "padding": {"left": 10, "right": 10, "top": 6, "bottom": 6},
    "transform": [
        {"joinaggregate": [{"op": "max", "field": "PeriodsAgo", "as": "streakLen"}], "groupby": ["Product"]},
        {"calculate": "datum.Period + datum.Note", "as": "label"},
    ],
    "encoding": {
        "x": {"field": "Product", "type": "nominal", "title": None,
              "sort": {"field": "PeriodsAgo", "op": "max", "order": "ascending"},
              "scale": {"paddingInner": 0.1, "paddingOuter": 0.02},
              "axis": {"orient": "top", "domain": False, "ticks": False, "labelAngle": 0, "labelPadding": 6,
                       "labelFontSize": 12, "labelColor": "#222", "labelFont": SANS}},
        "y": {"field": "PeriodsAgo", "type": "ordinal", "axis": None,
              "scale": {"paddingInner": 0.14, "paddingOuter": 0}},
    },
    "layer": [
        {"mark": {"type": "rect", "cornerRadius": 2},
         "encoding": {
             "color": {"field": "Result", "type": "nominal", "legend": None,
                       "scale": {"domain": ["Beat", "Missed"], "range": ["#2f73b8", "#df7a7a"]}},
             "opacity": {"condition": {"test": "datum.__selected__ == 'off'", "value": 0.3}, "value": 1},
             "tooltip": [{"field": "Product"}, {"field": "Period"}, {"field": "Result"}]}},
        {"mark": {"type": "text", "fontSize": 11, "font": SANS},
         "encoding": {"text": {"field": "label"},
                      "color": {"value": "white"},
                      "opacity": {"condition": {"test": "datum.Result == 'Beat'", "value": 1}, "value": 0.85},
                      "fontWeight": {"condition": {"test": "datum.Result == 'Beat'", "value": "bold"}, "value": "normal"}}},
        # Annotations: the three longest streaks, written to the left of the tile that ended them
        {"transform": [{"filter": "datum.PeriodsAgo == datum.streakLen && datum.Result == 'Beat' && datum.streakLen >= 3"},
                       {"window": [{"op": "dense_rank", "as": "rk"}], "sort": [{"field": "streakLen", "order": "descending"}]},
                       {"filter": "datum.rk <= 3"},
                       {"calculate": "[(datum.streakLen - 1) + ' consecutive', 'missed quarters', 'for ' + datum.Product]", "as": "note"}],
         "mark": {"type": "text", "align": "right", "baseline": "bottom", "dx": -46, "dy": 4, "fontSize": 11,
                  "lineHeight": 13, "font": SANS, "color": "#222"},
         "encoding": {"text": {"field": "note"}}},
        # Serif headline placed in the empty lower-left area (edit or delete freely)
        {"data": {"values": [{"t": ["The 7 Product Lines", "That Finally", "Beat Their Target"]}]},
         "mark": {"type": "text", "align": "left", "baseline": "top", "font": SERIF, "fontSize": 30,
                  "fontWeight": "bold", "fontStyle": "italic", "lineHeight": 38, "color": "#111"},
         "encoding": {"text": {"field": "t"}, "x": {"value": 0}, "y": {"value": {"expr": "height * 0.55"}}}},
    ],
    "config": {"view": {"stroke": None}, "font": SANS},
}

# --------------------------------------------------------------------------------------
# 2. Diverging "balance of power" bars (Vega-Lite) — fields: Year, Margin, Projected
# --------------------------------------------------------------------------------------
balance = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": "NYT-style diverging bars: margin above/below target by year",
    "data": {"name": "dataset"},
    "background": BG,
    "padding": {"left": 10, "right": 20, "top": 34, "bottom": 6},
    "transform": [
        {"calculate": "datum.Projected == 'Yes' ? 'Projected' : (datum.Margin < 0 ? 'Below' : 'Above')", "as": "Side"},
        {"calculate": "abs(datum.Margin)", "as": "absMargin"},
        {"window": [{"op": "lag", "field": "Margin", "as": "prev"}, {"op": "lead", "field": "Margin", "as": "next"}],
         "sort": [{"field": "Year"}]},
        {"window": [{"op": "row_number", "as": "absRank"}], "sort": [{"field": "absMargin", "order": "descending"}]},
        {"calculate": "datum.Projected == 'Yes' || datum.Margin == 0 || datum.absRank == 1"
                      " || (datum.absMargin >= 10 && datum.absMargin > abs(datum.prev || 0) && datum.absMargin >= abs(datum.next || 0)"
                      " && datum.Margin * (datum.prev || datum.Margin) > 0)", "as": "showLabel"},
        {"calculate": "datum.Margin == 0 ? 'Even' : (datum.Projected == 'Yes' ? 'At least +' + datum.absMargin + 'k (projected)'"
                      " : '+' + datum.absMargin + (datum.absRank == 1 ? 'k' : ''))", "as": "label"},
    ],
    "encoding": {
        "y": {"field": "Year", "type": "ordinal", "title": None,
              "scale": {"paddingInner": 0.06},
              "axis": {"domain": False, "ticks": False, "labelColor": GREY, "labelFontSize": 13, "labelPadding": 14,
                       "labelExpr": "datum.value % 10 == 0 || datum.value == 2026 ? datum.label : ''"}},
    },
    "layer": [
        {"mark": {"type": "bar"},
         "encoding": {
             "x": {"field": "Margin", "type": "quantitative", "title": None,
                   "scale": {"domain": [-45, 45]},
                   "axis": {"orient": "top", "values": [-40, -30, -20, -10, 0, 10, 20, 30, 40], "domain": False, "ticks": False,
                            "grid": True, "gridColor": "#dddddd", "labelColor": GREY, "labelFontSize": 13,
                            "labelExpr": "datum.value == 0 ? 'Even' : '+' + abs(datum.value)"}},
             "color": {"field": "Side", "type": "nominal", "legend": None,
                       "scale": {"domain": ["Below", "Above", "Projected"], "range": ["#5394cf", "#e07a7a", "#9dc3e6"]}},
             "opacity": {"condition": {"test": "datum.__selected__ == 'off'", "value": 0.3}, "value": 1},
             "tooltip": [{"field": "Year"}, {"field": "Margin", "title": "Margin ($k)"}]}},
        {"mark": {"type": "rule", "color": "#111", "strokeWidth": 2},
         "encoding": {"x": {"datum": 0}}},
        {"transform": [{"filter": "datum.showLabel && datum.Margin < 0"}],
         "mark": {"type": "text", "fontSize": 13, "color": GREY, "font": SANS, "align": "right", "dx": -5},
         "encoding": {"x": {"field": "Margin", "type": "quantitative"}, "text": {"field": "label"}}},
        {"transform": [{"filter": "datum.showLabel && datum.Margin >= 0"}],
         "mark": {"type": "text", "fontSize": 13, "color": GREY, "font": SANS, "align": "left", "dx": 5},
         "encoding": {"x": {"field": "Margin", "type": "quantitative"}, "text": {"field": "label"}}},
        {"data": {"values": [{"x": -30, "t": "Below target"}, {"x": 30, "t": "Above target"}]},
         "mark": {"type": "text", "fontSize": 13, "color": GREY, "dy": -30, "font": SANS},
         "encoding": {"x": {"field": "x", "type": "quantitative"}, "y": {"value": 0}, "text": {"field": "t"}}},
    ],
    "config": {"view": {"stroke": None}, "font": SANS},
}


# --------------------------------------------------------------------------------------
# 3. US route map (Vega) — fields: Origin, OriginName, OriginLon, OriginLat,
#                                   Dest, DestName, DestLon, DestLat, Cancelled
# --------------------------------------------------------------------------------------
def us_map():
    topo = json.loads((GEO / "us_states.json").read_text())
    end = lambda p: [  # noqa: E731 - origin/destination -> one airport row
        {"type": "formula", "expr": f"datum.{p}", "as": "code"},
        {"type": "formula", "expr": f"datum.{p}Name", "as": "name"},
        {"type": "formula", "expr": f"datum.{p}Lon", "as": "lon"},
        {"type": "formula", "expr": f"datum.{p}Lat", "as": "lat"}]
    return {
        "$schema": "https://vega.github.io/schema/vega/v5.json",
        "description": "NYT-style bubble + route map (albersUsa). US state outlines embedded (us-atlas, simplified).",
        "background": "white",
        "padding": 5,
        "autosize": "none",
        "signals": [{"name": "top", "update": "90"}],
        "data": [
            {"name": "dataset"},
            {"name": "states", "values": topo, "format": {"type": "topojson", "feature": "states"}},
            {"name": "o", "source": "dataset", "transform": end("Origin")},
            {"name": "d", "source": "dataset", "transform": end("Dest")},
            {"name": "airports", "source": ["o", "d"], "transform": [
                {"type": "aggregate", "groupby": ["code", "name", "lon", "lat"], "fields": ["Cancelled"], "ops": ["sum"], "as": ["n"]},
                {"type": "geopoint", "projection": "proj", "fields": ["lon", "lat"]},
                {"type": "window", "sort": {"field": "n", "order": "descending"}, "ops": ["row_number"], "as": ["rank"]},
                {"type": "collect", "sort": {"field": "n", "order": "ascending"}}]},
            {"name": "routes", "source": "dataset", "transform": [
                {"type": "geopoint", "projection": "proj", "fields": ["OriginLon", "OriginLat"], "as": ["x1", "y1"]},
                {"type": "geopoint", "projection": "proj", "fields": ["DestLon", "DestLat"], "as": ["x2", "y2"]}]},
            {"name": "kpi", "source": "airports", "transform": [
                {"type": "aggregate", "fields": ["code", "n"], "ops": ["count", "sum"], "as": ["airports", "ends"]}]},
            {"name": "kpi2", "source": "dataset", "transform": [
                {"type": "aggregate", "fields": ["Cancelled", "Cancelled"], "ops": ["count", "sum"], "as": ["routes", "total"]}]},
        ],
        "projections": [{"name": "proj", "type": "albersUsa",
                         "fit": {"signal": "data('states')"}, "extent": {"signal": "[[20, top], [width - 20, height - 10]]"}}],
        "scales": [{"name": "size", "type": "linear", "domain": {"data": "airports", "field": "n"}, "zero": True, "range": [0, 4200]}],
        "marks": [
            {"type": "shape", "from": {"data": "states"},
             "encode": {"enter": {"fill": {"value": "#e4e4e4"}, "stroke": {"value": "white"}, "strokeWidth": {"value": 1}}},
             "transform": [{"type": "geoshape", "projection": "proj"}]},
            {"type": "rule", "from": {"data": "routes"},
             "encode": {"update": {"x": {"field": "x1"}, "y": {"field": "y1"}, "x2": {"field": "x2"}, "y2": {"field": "y2"},
                                   "stroke": {"value": "#7d7d7d"}, "strokeOpacity": {"value": 0.3}, "strokeWidth": {"value": 0.7}}}},
            {"type": "symbol", "name": "dots", "from": {"data": "airports"},
             "encode": {"update": {
                 "x": {"field": "x"}, "y": {"field": "y"}, "size": {"scale": "size", "field": "n"},
                 "fill": {"value": "#f4b46a"}, "fillOpacity": {"value": 0.55},
                 "stroke": [{"test": "datum.rank <= 7", "value": "#111"}, {"value": "#e8892c"}],
                 "strokeWidth": [{"test": "datum.rank <= 7", "value": 2}, {"value": 0.8}],
                 "tooltip": {"signal": "{'Airport': datum.name, 'Cancelled': datum.n}"}}}},
            {"type": "text", "from": {"data": "airports"},
             "encode": {"update": {
                 "x": {"field": "x"}, "y": {"signal": "datum.y + sqrt(scale('size', datum.n) / PI) + 11"},
                 "text": {"signal": "datum.rank <= 7 ? datum.name : ''"}, "align": {"value": "center"},
                 "font": {"value": SANS}, "fontWeight": {"value": "bold"}, "fontSize": {"value": 12}, "fill": {"value": "#111"},
                 "stroke": {"value": "white"}, "strokeWidth": {"value": 0}}}},
            {"type": "text", "from": {"data": "airports"},
             "encode": {"update": {
                 "x": {"field": "x"}, "y": {"signal": "datum.y + sqrt(scale('size', datum.n) / PI) + 25"},
                 "text": {"signal": "datum.rank <= 7 ? datum.n : ''"}, "align": {"value": "center"},
                 "font": {"value": SANS}, "fontSize": {"value": 12}, "fill": {"value": "#333"}}}},
            # KPI header
            {"type": "group", "from": {"data": "kpi"},
             "marks": [{"type": "text", "from": {"data": "kpi"}, "encode": {"update": {
                 "x": {"signal": "width * 0.33"}, "y": {"value": 14}, "align": {"value": "center"}, "fontSize": {"value": 11},
                 "fill": {"value": "#555"}, "font": {"value": SANS}, "text": {"value": "AFFECTED AIRPORTS"}}}},
                 {"type": "text", "from": {"data": "kpi"}, "encode": {"update": {
                     "x": {"signal": "width * 0.33"}, "y": {"value": 52}, "align": {"value": "center"}, "fontSize": {"value": 32},
                     "fontWeight": {"value": "bold"}, "font": {"value": SANS}, "text": {"field": "airports"}}}}]},
            {"type": "group", "from": {"data": "kpi2"},
             "marks": [{"type": "text", "from": {"data": "kpi2"}, "encode": {"update": {
                 "x": {"signal": "width * 0.5"}, "y": {"value": 14}, "align": {"value": "center"}, "fontSize": {"value": 11},
                 "fill": {"value": "#555"}, "font": {"value": SANS}, "text": {"value": "AFFECTED ROUTES"}}}},
                 {"type": "text", "from": {"data": "kpi2"}, "encode": {"update": {
                     "x": {"signal": "width * 0.5"}, "y": {"value": 52}, "align": {"value": "center"}, "fontSize": {"value": 32},
                     "fontWeight": {"value": "bold"}, "font": {"value": SANS}, "text": {"field": "routes"}}}},
                 {"type": "text", "from": {"data": "kpi2"}, "encode": {"update": {
                     "x": {"signal": "width * 0.67"}, "y": {"value": 14}, "align": {"value": "center"}, "fontSize": {"value": 11},
                     "fill": {"value": "#555"}, "font": {"value": SANS}, "text": {"value": "CANCELLED SHIPMENTS"}}}},
                 {"type": "text", "from": {"data": "kpi2"}, "encode": {"update": {
                     "x": {"signal": "width * 0.67"}, "y": {"value": 52}, "align": {"value": "center"}, "fontSize": {"value": 32},
                     "fontWeight": {"value": "bold"}, "font": {"value": SANS}, "text": {"field": "total"}}}}]},
            {"type": "text", "encode": {"update": {
                "x": {"signal": "width - 60"}, "y": {"signal": "top + 6"}, "align": {"value": "right"}, "fontSize": {"value": 12},
                "fill": {"value": "#555"}, "font": {"value": SANS}, "lineHeight": {"value": 15},
                "text": {"value": ["Circles are sized by the number", "of cancelled shipments. Lines are", "the routes that were cancelled."]}}}},
        ],
    }


# --------------------------------------------------------------------------------------
# 4. Globe with routes + positions (Vega, orthographic) — fields: Kind, Id, Seq, Lon, Lat
# --------------------------------------------------------------------------------------
def globe():
    topo = json.loads((GEO / "world_countries.json").read_text())
    places = [  # label, lon, lat, kind (city / country / sea / key)
        ("Strait of Hormuz", 56.4, 26.6, "key"), ("Suez Canal", 32.5, 30.4, "key"),
        ("Kuwait City", 47.98, 29.37, "city"), ("Doha", 51.53, 25.29, "city"), ("Muscat", 58.4, 23.6, "city"),
        ("Karachi", 67.0, 24.86, "city"), ("Mumbai", 72.88, 19.08, "city"), ("Chennai", 80.27, 13.08, "city"),
        ("Colombo", 79.86, 6.93, "city"), ("Bangkok", 100.5, 13.75, "city"), ("Singapore", 103.82, 1.35, "city"),
        ("Hong Kong", 114.17, 22.32, "city"), ("Manila", 120.98, 14.6, "city"), ("Mombasa", 39.67, -4.04, "city"),
        ("Dar es Salaam", 39.28, -6.79, "city"),
        ("TURKEY", 35, 39, "country"), ("IRAQ", 43.5, 33, "country"), ("IRAN", 54, 32.5, "country"),
        ("SAUDI", 45, 24.5, "country"), ("ARABIA", 45, 22.8, "country"), ("EGYPT", 29.5, 26.5, "country"),
        ("YEMEN", 47.5, 15.8, "country"), ("OMAN", 56.5, 20.5, "country"), ("PAKISTAN", 69, 29.5, "country"),
        ("INDIA", 78.5, 21.5, "country"), ("CHINA", 100, 34, "country"), ("THAILAND", 101, 16, "country"),
        ("MALAYSIA", 102, 3.8, "country"), ("INDONESIA", 114, -1, "country"), ("KENYA", 37.8, 0.5, "country"),
        ("TANZANIA", 35, -6.5, "country"), ("SOUTH AFRICA", 24.5, -30.5, "country"),
        ("Arabian Sea", 64.5, 14, "sea"), ("Bay of Bengal", 88.5, 14, "sea"), ("Indian Ocean", 80, -18, "sea"),
        ("South China Sea", 114, 12, "sea"), ("Pacific Ocean", 135, 25, "sea"),
    ]
    style = {"key": ("#111", "bold", 12, "normal"), "city": ("#222", "normal", 11, "normal"),
             "country": ("#8a8a8a", "normal", 10, "normal"), "sea": ("#7a7a7a", "normal", 11, "italic")}
    return {
        "$schema": "https://vega.github.io/schema/vega/v5.json",
        "description": "NYT-style orthographic globe with sea routes and positions. Country outlines embedded (world-atlas 110m, simplified).",
        "background": "white",
        "autosize": "none",
        "signals": [
            {"name": "centerLon", "value": 76},
            {"name": "centerLat", "value": 10},
            {"name": "zoom", "update": "width * 0.56"},
        ],
        "data": [
            {"name": "dataset"},
            {"name": "world", "values": topo, "format": {"type": "topojson", "feature": "countries"}},
            {"name": "graticule", "transform": [{"type": "graticule", "step": [15, 15]}]},
            {"name": "sphere", "values": [{"type": "Sphere"}]},
            {"name": "routes", "source": "dataset", "transform": [
                {"type": "filter", "expr": "datum.Kind == 'Route'"},
                {"type": "collect", "sort": {"field": ["Id", "Seq"]}},
                {"type": "geopoint", "projection": "proj", "fields": ["Lon", "Lat"]}]},
            {"name": "positions", "source": "dataset", "transform": [
                {"type": "filter", "expr": "datum.Kind == 'Position'"},
                {"type": "geopoint", "projection": "proj", "fields": ["Lon", "Lat"]}]},
            {"name": "places", "values": [{"t": p[0], "lon": p[1], "lat": p[2], "k": p[3]} for p in places],
             "transform": [{"type": "geopoint", "projection": "proj", "fields": ["lon", "lat"]}]},
        ],
        "projections": [{"name": "proj", "type": "orthographic", "scale": {"signal": "zoom"},
                         "rotate": [{"signal": "-centerLon"}, {"signal": "-centerLat"}, 0],
                         "translate": [{"signal": "width / 2"}, {"signal": "height * 0.62"}]}],
        "marks": [
            {"type": "shape", "from": {"data": "sphere"}, "transform": [{"type": "geoshape", "projection": "proj"}],
             "encode": {"update": {"fill": {"value": {"gradient": "radial", "x1": 0.5, "y1": 0.5, "r1": 0.35,
                                                       "x2": 0.5, "y2": 0.5, "r2": 0.5,
                                                       "stops": [{"offset": 0, "color": "#eef0f2"}, {"offset": 1, "color": "#cfd5da"}]}}}}},
            {"type": "shape", "from": {"data": "graticule"}, "transform": [{"type": "geoshape", "projection": "proj"}],
             "encode": {"update": {"stroke": {"value": "#e3e6e8"}, "strokeWidth": {"value": 0.5}, "fill": {"value": None}}}},
            {"type": "shape", "from": {"data": "world"}, "transform": [{"type": "geoshape", "projection": "proj"}],
             "encode": {"update": {"fill": {"value": "#ffffff"}, "stroke": {"value": "#b9b9b9"}, "strokeWidth": {"value": 0.6}}}},
            {"type": "group", "from": {"facet": {"name": "routeSeg", "data": "routes", "groupby": "Id"}},
             "marks": [{"type": "line", "from": {"data": "routeSeg"},
                        "encode": {"update": {"x": {"field": "x"}, "y": {"field": "y"}, "interpolate": {"value": "basis"},
                                              "stroke": {"value": "#f2b300"}, "strokeOpacity": {"value": 0.16},
                                              "strokeWidth": {"value": 1.6}}}}]},
            {"type": "symbol", "from": {"data": "positions"},
             "encode": {"update": {"x": {"field": "x"}, "y": {"field": "y"}, "size": {"value": 9},
                                   "fill": {"value": "#e8342b"}, "fillOpacity": {"value": 0.85},
                                   "tooltip": {"signal": "{'Lon': datum.Lon, 'Lat': datum.Lat}"}}}},
            {"type": "symbol", "from": {"data": "places"},
             "encode": {"update": {"x": {"field": "x"}, "y": {"field": "y"}, "size": {"value": 10}, "fill": {"value": "#222"},
                                   "opacity": {"signal": "datum.k == 'city' || datum.k == 'key' ? 1 : 0"}}}},
            {"type": "text", "from": {"data": "places"},
             "encode": {"update": {
                 "x": {"field": "x"}, "y": {"field": "y"}, "text": {"field": "t"}, "font": {"value": SANS},
                 "dx": {"signal": "datum.k == 'city' || datum.k == 'key' ? (datum.lon < 60 ? -5 : 5) : 0"},
                 "dy": {"signal": "datum.k == 'key' ? -14 : 0"},
                 "align": {"signal": "datum.k == 'city' || datum.k == 'key' ? (datum.lon < 60 ? 'right' : 'left') : 'center'"},
                 "baseline": {"value": "middle"},
                 "fill": {"signal": json.dumps({k: v[0] for k, v in style.items()}) + "[datum.k]"},
                 "fontWeight": {"signal": json.dumps({k: v[1] for k, v in style.items()}) + "[datum.k]"},
                 "fontSize": {"signal": json.dumps({k: v[2] for k, v in style.items()}) + "[datum.k]"},
                 "fontStyle": {"signal": json.dumps({k: v[3] for k, v in style.items()}) + "[datum.k]"},
                 "stroke": {"value": "white"}, "strokeWidth": {"value": 0}}}},
            # Legend box
            {"type": "text", "encode": {"update": {"x": {"signal": "width / 2"}, "y": {"value": 24}, "align": {"value": "center"},
                                                   "font": {"value": SANS}, "fontWeight": {"value": "bold"}, "fontSize": {"value": 14},
                                                   "text": {"value": "Where tankers were (illustrative data)"}}}},
            {"type": "symbol", "encode": {"update": {"x": {"signal": "width / 2 - 90"}, "y": {"value": 46}, "size": {"value": 60},
                                                     "fill": {"value": "#e8342b"}}}},
            {"type": "text", "encode": {"update": {"x": {"signal": "width / 2 - 80"}, "y": {"value": 50}, "font": {"value": SANS},
                                                   "fontSize": {"value": 12}, "text": {"value": "Position"}}}},
            {"type": "rule", "encode": {"update": {"x": {"signal": "width / 2 + 10"}, "x2": {"signal": "width / 2 + 40"},
                                                   "y": {"value": 46}, "stroke": {"value": "#f2b300"}, "strokeWidth": {"value": 2.5}}}},
            {"type": "text", "encode": {"update": {"x": {"signal": "width / 2 + 46"}, "y": {"value": 50}, "font": {"value": SANS},
                                                   "fontSize": {"value": 12}, "text": {"value": "Route"}}}},
        ],
    }


SPEC_FILES = {  # spec file -> (spec, preview data csv, preview size)
    "nyt_01_streak_tiles.json": (streak, "streaks.csv", (440, 760)),
    "nyt_02_diverging_balance.json": (balance, "balance.csv", (640, 700)),
    "nyt_03_us_route_map.vega.json": (us_map(), "routes.csv", (1000, 700)),
    "nyt_04_globe_routes.vega.json": (globe(), "tankers.csv", (1100, 760)),
}


def load_csv(name):
    rows = list(csv.DictReader(open(DATA / name, encoding="utf-8")))
    for r in rows:
        for k, v in r.items():
            try: r[k] = float(v) if "." in v else int(v)
            except ValueError: pass
    return rows


def render():
    import vl_convert as vlc
    for d in ("/usr/share/fonts", "C:/Windows/Fonts"):
        try: vlc.register_font_directory(d)
        except Exception: pass
    sub = {SANS: "DejaVu Sans", SERIF: "DejaVu Serif"}
    ok = True
    for fname, (spec, data, (w, h)) in SPEC_FILES.items():
        s = json.dumps(spec)
        for a, b in sub.items(): s = s.replace(a, b)
        s = json.loads(s)
        rows = load_csv(data)
        out = RENDERS / (fname.split(".")[0] + ".png")
        try:
            if fname.endswith(".vega.json"):
                s["width"], s["height"] = w, h
                for d in s["data"]:
                    if d["name"] == "dataset": d["values"] = rows
                png = vlc.vega_to_png(s, scale=1.5)
            else:
                s["width"], s["height"] = w, h
                s["data"] = {"values": rows}
                png = vlc.vegalite_to_png(s, vl_version="5.21", scale=1.5)
            out.write_bytes(png); print("OK  ", fname, "->", out.name)
        except Exception as e:
            ok = False; print("FAIL", fname, str(e)[:800])
    return ok


if __name__ == "__main__":
    for fname, (spec, _, _) in SPEC_FILES.items():
        (SPECS / fname).write_text(json.dumps(spec, ensure_ascii=False, indent=1 if "vega.json" not in fname else None), encoding="utf-8")
        print("wrote", fname, f"{(SPECS / fname).stat().st_size / 1024:.0f} KB")
    sys.exit(0 if render() else 1)
