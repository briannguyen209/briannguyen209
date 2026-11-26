# Power BI Python visual — Values: OrderDate, Sales, Profit. Dual axis kiểu Tableau.
import pandas as pd, matplotlib.pyplot as plt, matplotlib.ticker as mt
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "axes.spines.top": False})
df = dataset.copy(); df["Month"] = pd.to_datetime(df["OrderDate"]).dt.to_period("M").dt.to_timestamp()
m = df.groupby("Month")[["Sales", "Profit"]].sum(); m["Margin"] = m.Profit / m.Sales
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(m.index, m.Sales, width=25, color="#4e79a7", alpha=.85); ax.set_ylabel("Doanh số", color="#4e79a7")
ax.yaxis.set_major_formatter(mt.StrMethodFormatter("{x:,.0f}")); ax.grid(axis="y", color="#eee")
ax2 = ax.twinx(); ax2.plot(m.index, m.Margin, color="#f28e2b", marker="o", lw=2.5)
ax2.set_ylabel("Tỷ suất LN", color="#f28e2b"); ax2.yaxis.set_major_formatter(mt.PercentFormatter(1.0)); ax2.set_ylim(0)
for s in ("top",): ax2.spines[s].set_visible(False)
plt.tight_layout(); plt.show()
