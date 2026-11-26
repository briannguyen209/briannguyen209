"""Helpers for the Deneb tutorial: Deneb-shaped data, step rendering, compact JSON, document blocks."""
import copy, json, pathlib, sys
import pandas as pd
import vl_convert as vlc

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
STEPS = HERE / "steps"
IMG = REPO / "renders" / "tutorial"
STEPS.mkdir(exist_ok=True); IMG.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO / "powerbi-sample")); sys.path.insert(0, str(REPO / "nyt-style"))
import build_pbip as B  # noqa: E402  (data tables, final specs, Tableau config)
import build_specs as N  # noqa: E402  (NYT-style final specs)

for d in ("/usr/share/fonts",):
    try: vlc.register_font_directory(d)
    except Exception: pass

VL = "https://vega.github.io/schema/vega-lite/v5.json"
VG = "https://vega.github.io/schema/vega/v5.json"

# ---------------------------------------------------------------- data like Deneb sends it
TABLES = {t: pd.DataFrame(rows) for t, (rows, _) in B.TABLES.items()}
for t, (_, cols) in B.TABLES.items():
    for c, spec in cols.items():
        if spec[0] in ("int64", "double"): TABLES[t][c] = pd.to_numeric(TABLES[t][c])
MEAS = {"Total Sales": lambda g: g["Sales"].sum(), "Total Profit": lambda g: g["Profit"].sum(),
        "Total Target": lambda g: g["Target"].sum(),
        "Profit Ratio": lambda g: g["Profit"].sum() / g["Sales"].sum(),
        "Attainment %": lambda g: g["Sales"].sum() / g["Target"].sum()}


def dataset(table, cols, meas=(), interacting=False):
    """One row per combination of `cols`, measures evaluated per row, plus Deneb support fields."""
    df = TABLES[table]
    if not meas:
        out = df[list(cols)].drop_duplicates().reset_index(drop=True)
    else:
        rows = []
        for key, g in df.groupby(list(cols), sort=True):
            key = key if isinstance(key, tuple) else (key,)
            r = dict(zip(cols, key)); hg = g[g["Segment"] == "Consumer"]
            for m in meas:
                r[m] = float(MEAS[m](g))
                hv = float(MEAS[m](hg)) if (interacting and len(hg)) else (None if interacting else r[m])
                r[m + "__highlight"] = hv
                r[m + "__highlightStatus"] = ("on" if hv is not None else "off") if interacting else "neutral"
            rows.append(r)
        out = pd.DataFrame(rows)
    out["__row__"] = range(len(out)); out["__selected__"] = "neutral"
    if interacting and len(out) > 1:
        out["__selected__"] = "off"; out.loc[1, "__selected__"] = "on"
    return json.loads(out.to_json(orient="records"))


FONT_SUB = {"Segoe UI": "DejaVu Sans", "Georgia": "DejaVu Serif"}


def render(spec, rows, name, w=520, h=300, config=None, scale=1.4):
    """Render a step spec (exactly as the reader will paste it) with `rows` as the dataset."""
    s = json.loads(json.dumps(spec))
    for a, b in FONT_SUB.items():
        s = json.loads(json.dumps(s).replace(a, b))
    cfg = json.loads(json.dumps(config or {}).replace("Segoe UI", "DejaVu Sans"))
    s["width"], s["height"] = w, h
    if s["$schema"] == VG:
        s.setdefault("background", "white")  # preview only; in Deneb the visual's background shows through
        for d in s["data"]:
            if d["name"] == "dataset": d["values"] = rows
        if cfg: s["config"] = {**cfg, **s.get("config", {})}
        png = vlc.vega_to_png(s, scale=scale)
    else:
        s["data"] = {"values": rows}
        s["config"] = {**cfg, **s.get("config", {})}
        png = vlc.vegalite_to_png(s, vl_version="5.21", scale=scale)
    p = IMG / f"{name}.png"; p.write_bytes(png)
    return p


# ---------------------------------------------------------------- compact JSON (readable code blocks)
def cjson(obj, indent=0, width=84, placeholder=None):
    """Pretty JSON that keeps short objects/arrays on one line."""
    pad = "  " * indent
    if placeholder and isinstance(obj, dict) and obj.get("type") == "Topology":
        return json.dumps(placeholder)
    one = json.dumps(obj, ensure_ascii=False)
    if len(one) + len(pad) <= width or not isinstance(obj, (dict, list)):
        return one
    inner = "  " * (indent + 1)
    if isinstance(obj, dict):
        items = [f'{inner}{json.dumps(k, ensure_ascii=False)}: {cjson(v, indent + 1, width, placeholder).lstrip()}' for k, v in obj.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    items = [inner + cjson(v, indent + 1, width, placeholder).lstrip() for v in obj]
    return "[\n" + ",\n".join(items) + "\n" + pad + "]"


def save_step(spec, name):
    (STEPS / f"{name}.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"tutorial/steps/{name}.json"


def get(obj, path):
    """get(spec, 'layer[1].encoding.color')"""
    cur = obj
    for part in path.replace("]", "").split("."):
        if "[" in part:
            k, i = part.split("[")
            cur = cur[k] if k else cur
            cur = cur[int(i)]
        else:
            cur = cur[part]
    return cur


# ---------------------------------------------------------------- document blocks
DOC = []


def h1(t): DOC.append({"t": "h1", "text": t})
def h2(t): DOC.append({"t": "h2", "text": t})
def h3(t): DOC.append({"t": "h3", "text": t})
def p(t): DOC.append({"t": "p", "text": t})
def bullets(items): DOC.append({"t": "bullets", "items": items})
def steps_list(items): DOC.append({"t": "numbered", "items": items})
def code(text, label=None): DOC.append({"t": "code", "text": text, "label": label})
def note(kind, text): DOC.append({"t": "note", "kind": kind, "text": text})
def table(headers, rows, widths): DOC.append({"t": "table", "headers": headers, "rows": rows, "widths": widths})
def image(path, width_in=5.2, caption=None): DOC.append({"t": "img", "path": str(path), "w": width_in, "caption": caption})
def pagebreak(): DOC.append({"t": "pagebreak"})


def step(chart, n, title, spec, rows, explain, show=None, w=520, h=300, config=None, caption=None,
         placeholder=None, after=None, img_w=5.0, interacting_rows=None):
    """One tutorial step: heading, what to do, code (full or selected parts), explanation, picture."""
    name = f"{chart}_step{n}"
    path = save_step(spec, name)
    h3(f"Step {n} — {title}")
    for para in explain.get("do", []): p(para)
    if show is None:
        code(cjson(spec, placeholder=placeholder), label=f"Full spec at this step  ·  {path}")
    else:
        for pth, lab in show:
            snippet = get(spec, pth) if pth else spec
            code(cjson(snippet, placeholder=placeholder), label=lab)
        p(f"The complete spec after this step is saved as **{path}** — paste that file if you get lost.")
    for para in explain.get("why", []): p(para)
    for kind, txt in explain.get("notes", []): note(kind, txt)
    img = render(spec, rows, name, w, h, config)
    image(img, img_w, caption or f"Result after step {n}")
    if interacting_rows is not None:
        img2 = render(spec, interacting_rows, name + "_interacting", w, h, config)
        image(img2, img_w, "Same step while interacting: one item selected (others dim) and a cross-highlight from Segment = Consumer")
    if after:
        for para in after: p(para)
    return spec


def deep(o): return copy.deepcopy(o)
