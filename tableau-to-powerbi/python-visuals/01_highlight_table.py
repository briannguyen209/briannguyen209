# Power BI Python visual — kéo các field: Region, SubCategory, Sales vào ô Values.
# Power BI tự tạo biến `dataset` (pandas DataFrame). Phần "theme" lấy từ tableau_style.py.
import matplotlib.pyplot as plt, seaborn as sns
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"]})
pv = dataset.pivot_table(index="SubCategory", columns="Region", values="Sales", aggfunc="sum")
fig, ax = plt.subplots(figsize=(7, 5))
sns.heatmap(pv, annot=True, fmt=",.0f", cmap="Blues", linewidths=1, linecolor="white", cbar_kws={"label": "Doanh số"}, ax=ax)
ax.xaxis.tick_top(); ax.set_xlabel(""); ax.set_ylabel(""); plt.yticks(rotation=0)
plt.tight_layout(); plt.show()
