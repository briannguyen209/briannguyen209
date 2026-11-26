"""Đọc file Tableau .twb / .twbx (KHÔNG cần cài/mua Tableau) và liệt kê từng worksheet:
loại mark, field trên Rows/Columns, encoding (màu/size/label...), calculated field,
rồi gợi ý cách dựng lại trong Power BI (visual có sẵn / template Deneb trong repo này / custom visual).

Dùng:  python tools/twb_inspector.py workbook.twbx [-o report.md]
Chỉ dùng thư viện chuẩn Python.  File .twbx là zip chứa .twb + extract dữ liệu (.hyper).
"""
import argparse, re, sys, zipfile, pathlib, xml.etree.ElementTree as ET

AGG = {"sum": "SUM", "avg": "AVG", "cnt": "COUNT", "ctd": "COUNTD", "min": "MIN", "max": "MAX", "med": "MEDIAN",
       "attr": "ATTR", "yr": "YEAR", "qr": "QUARTER", "mn": "MONTH", "tmn": "MONTH(trunc)", "tyr": "YEAR(trunc)", "tqr": "QUARTER(trunc)",
       "twk": "WEEK(trunc)", "tdy": "DAY(trunc)", "dy": "DAY", "usr": "", "none": "", "pcto": "% of total"}
FIELD_RE = re.compile(r"\[([a-z]*):([^:\]]+)(?::([a-z]+))?\]|\]\.\[([^:\]\[]+)\]")
DATE_AGG = {"yr", "qr", "mn", "tmn", "tyr", "tqr", "twk", "tdy", "dy"}

def load_twb(path):
    p = pathlib.Path(path)
    if p.suffix.lower() == ".twbx":
        with zipfile.ZipFile(p) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".twb"))
            return ET.fromstring(z.read(name)), [n for n in z.namelist() if not n.lower().endswith(".twb")]
    return ET.parse(p).getroot(), []

def pretty(expr, captions):
    """'[ds].[sum:Sales:qk] / [ds].[none:Region:nk]' -> ['SUM(Sales)', 'Region']"""
    out = []
    for agg, name, kind, plain in FIELD_RE.findall(expr or ""):
        if plain:  # dạng [ds].[Field] không có tiền tố aggregation
            name, agg, kind = plain, "none", "nk"
        name = captions.get(name, name)
        if name.startswith("Multiple Values") or name.startswith("federated."): continue
        a = AGG.get(agg, agg.upper())
        label = f"{a}({name})" if a else name
        if agg in DATE_AGG or (kind.startswith("q") and agg in ("none", "")) and "Date" in name:
            label += " [thời gian]" if kind.startswith("q") else ""   # ngày liên tục, không phải measure
        elif kind.startswith("q"):
            label += " [đo]"
        out.append(label)
    return out

def is_measure(lst): return any(x.endswith("[đo]") for x in lst)

def classify(mark, rows, cols, enc, n_panes, has_box):
    """Đoán loại biểu đồ Tableau & gợi ý Power BI."""
    m = mark.lower(); rm, cm = is_measure(rows), is_measure(cols)
    rd = [x for x in rows if not x.endswith("[đo]")]; cd = [x for x in cols if not x.endswith("[đo]")]
    if has_box: return "Box-and-whisker", "Deneb: deneb/05_box_whisker.json (Power BI không có box plot gốc)"
    if m == "map" or "Latitude" in " ".join(rows + cols): return "Bản đồ", "Visual gốc: Map / Filled map / Azure Maps"
    if n_panes > 1 and rm and (cd or "MONTH" in " ".join(cols) or "YEAR" in " ".join(cols)):
        return "Dual axis / combo", "Visual gốc: Line and clustered column chart; bản giống Tableau hơn: deneb/03_dual_axis_combo.json"
    if not rows and not cols:
        if m == "circle" and "size" in enc: return "Packed bubbles", "Deneb (Vega): deneb/08_packed_bubbles.vega.json"
        if m in ("square", "automatic") and "size" in enc: return "Treemap", "Visual gốc: Treemap; hoặc deneb/09_treemap.vega.json"
        if m == "text" or "text" in enc: return "Text / KPI", "Visual gốc: Card / Multi-row card"
        if m == "pie": return "Pie", "Visual gốc: Pie / Donut"
        return "Không trục", "Kiểm tra thủ công"
    timeaxis = any(x.endswith("[thời gian]") for x in rows + cols)
    if timeaxis and "size" in enc and m in ("automatic", "gantt bar", "ganttbar"):
        return "Gantt", "Deneb: bar với x=ngày bắt đầu, x2=ngày kết thúc (hoặc visual Gantt miễn phí trên AppSource)"
    if m == "square" and "color" in enc and not rm and not cm: return "Highlight table / heatmap", "Deneb: deneb/01_highlight_table.json; hoặc Matrix + conditional formatting (gốc)"
    if m in ("text", "automatic") and not rm and not cm and not timeaxis:
        return "Crosstab / text table", "Visual gốc: Matrix / Table (+ conditional formatting)"
    if m == "circle" and (rm or cm) and not (rm and cm): return "Dot plot / strip", "Visual gốc: Scatter (trục phân loại); hoặc Deneb mark point"
    if m == "gantt bar" or m == "ganttbar": return "Gantt", "Deneb (tự viết bar với x/x2) hoặc visual AppSource miễn phí loại Gantt"
    if m == "pie": return "Pie", "Visual gốc: Pie / Donut"
    if rm and cm: return "Scatter", "Visual gốc: Scatter; có trend line + quadrant: deneb/06_scatter_quadrant.json"
    if m == "area": return ("Area small multiples" if (rd and cd) else "Area"), "Visual gốc: Area (small multiples); hoặc deneb/07_trellis_area.json"
    if m == "line" or (m == "automatic" and timeaxis):
        return "Line", "Visual gốc: Line chart"
    if m in ("bar", "automatic") and (rm or cm):
        if "size" in enc or n_panes > 1: return "Bar-in-bar / bullet", "deneb/02_bar_in_bar.json, deneb/04_bullet_chart.json hoặc custom visual tableauBulletVisual"
        return "Bar", "Visual gốc: Clustered/Stacked bar"
    return mark or "?", "Kiểm tra thủ công"

def inspect(path):
    root, packaged = load_twb(path)
    captions, calcs = {}, []
    for ds in root.iter("datasource"):
        for col in ds.iter("column"):
            name = (col.get("name") or "").strip("[]"); cap = col.get("caption")
            if cap: captions[name] = cap
            calc = col.find("calculation")
            if calc is not None and (cap or name) in {c[0] for c in calcs}: continue
            if calc is not None and calc.get("formula") and calc.get("class", "tableau") == "tableau":
                calcs.append((cap or name, calc.get("formula")))
    sheets = []
    for ws in root.iter("worksheet"):
        tbl = ws.find("table")
        if tbl is None: continue
        rows = pretty(tbl.findtext("rows"), captions); cols = pretty(tbl.findtext("cols"), captions)
        panes = tbl.findall("./panes/pane")
        marks = sorted({(p.find("mark").get("class") if p.find("mark") is not None else "Automatic") for p in panes}) or ["Automatic"]
        enc = {}
        for p in panes:
            e = p.find("encodings")
            if e is None: continue
            for child in e:
                enc.setdefault(child.tag, set()).update(pretty(child.get("column"), captions))
        has_box = any("boxplot" in (rl.get("boxplot-style", "") + rl.get("style", "") + rl.tag).lower() or rl.tag == "reference-line" and rl.get("boxplot-whisker-type")
                      for rl in ws.iter() if rl.tag in ("reference-line", "boxplot"))
        mark = next((x for x in marks if x != "Automatic"), marks[0])
        kind, pbi = classify(mark, rows, cols, enc, len(panes), has_box)
        sheets.append(dict(name=ws.get("name"), mark="/".join(marks), rows=rows, cols=cols,
                           enc={k: sorted(v) for k, v in enc.items()}, kind=kind, pbi=pbi))
    dashboards = [d.get("name") for d in root.iter("dashboard")]
    return dict(version=root.get("version"), sheets=sheets, calcs=calcs, dashboards=dashboards, packaged=packaged)

def to_markdown(path, info):
    L = [f"# Phân tích workbook Tableau: `{pathlib.Path(path).name}`", "",
         f"- Phiên bản Tableau: {info['version']}  ·  Worksheet: {len(info['sheets'])}  ·  Dashboard: {len(info['dashboards'])}"]
    if info["dashboards"]: L.append(f"- Dashboard: {', '.join(info['dashboards'])}")
    if info["packaged"]: L.append(f"- File đóng gói kèm (.twbx): {', '.join(info['packaged'][:10])}" + (" ..." if len(info["packaged"]) > 10 else ""))
    L += ["", "## Worksheet → gợi ý Power BI", "", "| Sheet | Mark | Rows | Columns | Encoding | Loại chart (đoán) | Dựng lại trong Power BI |", "|---|---|---|---|---|---|---|"]
    for s in info["sheets"]:
        enc = "; ".join(f"{k}: {', '.join(v)}" for k, v in s["enc"].items()) or "-"
        L.append(f"| {s['name']} | {s['mark']} | {', '.join(s['rows']) or '-'} | {', '.join(s['cols']) or '-'} | {enc} | {s['kind']} | {s['pbi']} |")
    if info["calcs"]:
        L += ["", "## Calculated field (cần viết lại bằng DAX)", "", "| Tên | Công thức Tableau |", "|---|---|"]
        for n, f in info["calcs"]:
            L.append(f"| {n} | `{' '.join(f.split()).replace('|', '¦')}` |")
    return "\n".join(L) + "\n"

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workbook"); ap.add_argument("-o", "--output")
    a = ap.parse_args()
    md = to_markdown(a.workbook, inspect(a.workbook))
    if a.output: pathlib.Path(a.output).write_text(md, encoding="utf-8"); print("Đã ghi", a.output)
    else: sys.stdout.write(md)
