# Power BI Python visual — Values: Category, SubCategory, Sales. Packed bubbles kiểu Tableau (thuật toán xếp vòng tròn đơn giản).
import numpy as np, matplotlib.pyplot as plt
TABLEAU10 = ["#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f","#edc948","#b07aa1","#ff9da7","#9c755f","#bab0ac"]
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"]})
d = dataset.groupby(["Category","SubCategory"], as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
r = np.sqrt(d["Sales"].to_numpy() / np.pi); r = r / r.max()
pos = []
for i, ri in enumerate(r):  # đặt lần lượt từng bubble ở vị trí gần tâm nhất mà không chồng lên bubble trước
    if i == 0: pos.append((0.0, 0.0)); continue
    best = None
    for ang in np.linspace(0, 2*np.pi, 180, endpoint=False):
        for dist in np.linspace(0, 6, 300):
            x, y = dist*np.cos(ang), dist*np.sin(ang)
            if all(np.hypot(x-px, y-py) >= ri + r[j] + 0.02 for j, (px, py) in enumerate(pos)):
                if best is None or dist < best[0]: best = (dist, x, y)
                break
    pos.append((best[1], best[2]))
colors = {c: TABLEAU10[k] for k, c in enumerate(d["Category"].unique())}
fig, ax = plt.subplots(figsize=(7, 6))
for (x, y), ri, (_, row) in zip(pos, r, d.iterrows()):
    ax.add_patch(plt.Circle((x, y), ri, color=colors[row.Category], ec="white"))
    if ri > 0.3: ax.text(x, y, row.SubCategory, ha="center", va="center", color="white", fontsize=9 + 4*ri)
ax.set_aspect("equal"); ax.autoscale_view(); ax.axis("off")
ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", color=c, label=k, markersize=10) for k, c in colors.items()], loc="upper left", frameon=False)
plt.tight_layout(); plt.show()
