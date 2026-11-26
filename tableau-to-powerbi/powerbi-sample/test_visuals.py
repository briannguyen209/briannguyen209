"""Offline test of every Deneb visual in the generated .pbip.

For each Deneb visual.json it:
  1. decodes the spec/config exactly as stored in the report (Power BI string literal),
  2. builds the dataset Deneb would receive: one row per combination of the projected
     columns, measures evaluated per row (mirrors the DAX), plus Deneb's support fields
     __row__, __selected__, <measure>__highlight and <measure>__highlightStatus,
  3. renders it twice with vl-convert: "normal" and "interacting"
     (cross-highlight from Segment = 'Consumer' + one data point selected).

Usage: python powerbi-sample/test_visuals.py      -> renders/pbip_<page>_<visual>_<state>.png
"""
import json, pathlib, sys
import pandas as pd
import vl_convert as vlc

HERE = pathlib.Path(__file__).resolve().parent
REPORT = HERE / "DenebShowcase/DenebShowcase.Report/definition/pages"
RENDERS = HERE.parent / "renders"
sys.path.insert(0, str(HERE))
import build_pbip as b  # noqa: E402

for d in ("/usr/share/fonts",):
    try: vlc.register_font_directory(d)
    except Exception: pass

TABLES = {t: pd.DataFrame(rows) for t, (rows, _) in b.TABLES.items()}
for t, (_, cols) in b.TABLES.items():
    for c, spec in cols.items():
        if spec[0] in ("int64", "double"): TABLES[t][c] = pd.to_numeric(TABLES[t][c])

MEASURES = {
    "Total Sales": lambda g: g["Sales"].sum(), "Total Profit": lambda g: g["Profit"].sum(),
    "Total Target": lambda g: g["Target"].sum(),
    "Profit Ratio": lambda g: g["Profit"].sum() / g["Sales"].sum(),
    "Attainment %": lambda g: g["Sales"].sum() / g["Target"].sum(),
}


def unlit(v):  # Power BI literal "'...'" with '' escaping -> python str
    s = v["expr"]["Literal"]["Value"]
    assert s[0] == s[-1] == "'"
    return s[1:-1].replace("''", "'")


def dataset(projs, interacting):
    cols = [p["field"]["Column"]["Property"] for p in projs if "Column" in p["field"]]
    meas = [p["field"]["Measure"]["Property"] for p in projs if "Measure" in p["field"]]
    tables = {p["field"][k]["Expression"]["SourceRef"]["Entity"] for p in projs for k in p["field"]}
    tables.discard("_Measures")
    df = TABLES[(tables or {"Sales"}).pop()]
    if not meas:
        out = df[cols].drop_duplicates().reset_index(drop=True)
    else:
        rows = []
        for key, g in df.groupby(cols, sort=True):
            key = key if isinstance(key, tuple) else (key,)
            r = dict(zip(cols, key))
            hg = g[g["Segment"] == "Consumer"]
            for m in meas:
                r[m] = float(MEASURES[m](g))
                hv = float(MEASURES[m](hg)) if (interacting and len(hg)) else (None if interacting else r[m])
                r[m + "__highlight"] = hv
                r[m + "__highlightStatus"] = ("on" if hv is not None else "off") if interacting else "neutral"
            rows.append(r)
        out = pd.DataFrame(rows)
    out["__row__"] = range(len(out))
    out["__selected__"] = "neutral"
    if interacting and len(out) > 1:
        out["__selected__"] = "off"; out.loc[1, "__selected__"] = "on"
    return json.loads(out.to_json(orient="records"))


def render(vis, state, path):
    o = vis["visual"]["objects"]["vega"][0]["properties"]
    provider, spec, config = unlit(o["provider"]), json.loads(unlit(o["jsonSpec"])), json.loads(unlit(o["jsonConfig"]))
    w, h = vis["position"]["width"], vis["position"]["height"] - 30
    rows = dataset(vis["visual"]["query"]["queryState"]["dataset"]["projections"], state == "interacting")
    spec = json.loads(json.dumps(spec).replace("Segoe UI", "DejaVu Sans").replace("Georgia", "DejaVu Serif"))
    config = json.loads(json.dumps(config).replace("Segoe UI", "DejaVu Sans"))
    spec["width"], spec["height"] = w, h
    if provider == "vega":
        for d in spec["data"]:
            if d["name"] == "dataset": d["values"] = rows
        spec["config"] = {**config, **spec.get("config", {})}
        png = vlc.vega_to_png(spec, scale=1)
    else:
        spec["data"] = {"values": rows}
        spec["config"] = {**config, **spec.get("config", {})}
        png = vlc.vegalite_to_png(spec, vl_version="5.21", scale=1)
    path.write_bytes(png)
    return len(rows)


ok = True
for vf in sorted(REPORT.glob("*/visuals/*/visual.json")):
    vis = json.loads(vf.read_text(encoding="utf-8"))
    if vis["visual"]["visualType"] != b.DENEB: continue
    page = vf.parts[-4]
    title = vis["visual"].get("visualContainerObjects", {}).get("title", [{}])[0].get("properties", {}).get("text")
    name = unlit(title) if title else "globe"
    slug = "".join(ch for ch in name.lower().split(":")[0] if ch.isalnum() or ch == " ").strip().replace(" ", "_")[:28]
    states = ("normal", "interacting") if page.startswith("tableau") else ("normal",)
    for st in states:
        out = RENDERS / f"pbip_{page}_{slug}_{st}.png"
        try:
            n = render(vis, st, out); print(f"OK   {page:9s} {name[:45]:45s} {st:11s} rows={n}")
        except Exception as e:
            ok = False; print(f"FAIL {page} {name} {st}: {str(e)[:600]}")
sys.exit(0 if ok else 1)
