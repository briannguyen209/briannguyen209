"""Chạy thử các script Python visual ngoài Power BI: tạo biến `dataset` giống Power BI rồi lưu PNG thay vì plt.show()."""
import pathlib, runpy, sys, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
root = pathlib.Path(__file__).resolve().parent.parent
df = pd.read_csv(root/"data/superstore_sample.csv")
ok = True
for f in sorted((root/"python-visuals").glob("[0-9]*.py")):
    out = root/"renders"/(f.stem + "_python.png")
    plt.show = lambda out=out: plt.savefig(out, dpi=150, bbox_inches="tight")
    try:
        runpy.run_path(str(f), init_globals={"dataset": df.copy()}); plt.close("all"); print("OK  ", f.name, "->", out.name)
    except Exception as e:
        ok = False; print("FAIL", f.name, repr(e))
sys.exit(0 if ok else 1)
