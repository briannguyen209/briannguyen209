"""Kiểm thử spec Deneb ngoài Power BI: thay data 'dataset' bằng CSV rồi render PNG bằng vl-convert.
Dùng: python tools/render_deneb_specs.py   (cần: pip install vl-convert-python pandas)"""
import json, pathlib, sys, pandas as pd, vl_convert as vlc
for d in ["/usr/share/fonts", "C:/Windows/Fonts"]:
    try: vlc.register_font_directory(d)
    except Exception: pass
FALLBACK = "DejaVu Sans"  # Segoe UI không có trên Linux -> thay khi render thử
root = pathlib.Path(__file__).resolve().parent.parent
rows = json.loads(pd.read_csv(root/"data/superstore_sample.csv").to_json(orient="records"))
ok = True
for f in sorted((root/"deneb").glob("*.json")):
    spec = json.loads(f.read_text(encoding="utf-8").replace("Segoe UI", FALLBACK))
    is_vega = f.name.endswith(".vega.json")
    if is_vega:
        spec.setdefault("config", {}).update({"text": {"font": FALLBACK}, "legend": {"labelFont": FALLBACK, "titleFont": FALLBACK}, "axis": {"labelFont": FALLBACK, "titleFont": FALLBACK}})
        for d in spec["data"]:
            if d.get("name") == "dataset": d["values"] = rows
    else:
        spec["data"] = {"values": rows}
        spec.setdefault("config", {}).setdefault("font", FALLBACK)
    out = root/"renders"/(f.name.replace(".vega.json","").replace(".json","")+"_deneb.png")
    try:
        png = vlc.vega_to_png(spec, scale=2) if is_vega else vlc.vegalite_to_png(spec, vl_version="5.21", scale=2)
        out.write_bytes(png); print("OK  ", f.name, "->", out.name)
    except Exception as e:
        ok = False; print("FAIL", f.name, e)
sys.exit(0 if ok else 1)
