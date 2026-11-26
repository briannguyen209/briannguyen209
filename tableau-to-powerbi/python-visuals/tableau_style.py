# Đoạn "theme Tableau" — dán vào đầu mỗi Python visual trong Power BI (Power BI không import file cục bộ dễ dàng).
import matplotlib.pyplot as plt
TABLEAU10 = ["#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f","#edc948","#b07aa1","#ff9da7","#9c755f","#bab0ac"]
plt.rcParams.update({
    "axes.prop_cycle": plt.cycler(color=TABLEAU10), "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#cccccc", "axes.grid": True, "grid.color": "#eeeeee", "axes.axisbelow": True,
    "xtick.color": "#666666", "ytick.color": "#666666", "axes.labelcolor": "#333333", "font.size": 10,
    "font.family": ["Segoe UI", "DejaVu Sans"], "figure.dpi": 110})
