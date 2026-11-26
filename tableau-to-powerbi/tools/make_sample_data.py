"""Sinh dữ liệu mẫu kiểu 'Superstore' (giống dataset demo của Tableau) để thử nghiệm."""
import numpy as np, pandas as pd, pathlib
rng = np.random.default_rng(42)
regions = ["Miền Bắc", "Miền Trung", "Miền Nam", "Tây Nguyên"]
cats = {"Nội thất": ["Bàn", "Ghế", "Kệ sách"], "Văn phòng phẩm": ["Giấy", "Bút", "Bìa hồ sơ"], "Công nghệ": ["Điện thoại", "Máy in", "Phụ kiện"]}
segments = ["Cá nhân", "Doanh nghiệp", "Văn phòng tại gia"]
rows = []
dates = pd.date_range("2024-01-01", "2025-12-31", freq="D")
for i in range(4000):
    c = rng.choice(list(cats)); s = rng.choice(cats[c])
    base = {"Nội thất": 300, "Văn phòng phẩm": 60, "Công nghệ": 500}[c]
    sales = float(np.round(rng.lognormal(np.log(base), 0.8), 2))
    margin = rng.normal({"Nội thất": 0.03, "Văn phòng phẩm": 0.15, "Công nghệ": 0.18}[c], 0.2)
    d = rng.choice(dates)
    rows.append(dict(OrderID=f"DH-{10000+i}", OrderDate=pd.Timestamp(d).date().isoformat(),
                     ShipDays=int(rng.integers(1, 8)), Region=rng.choice(regions, p=[.35,.2,.35,.1]),
                     Segment=rng.choice(segments, p=[.5,.3,.2]), Category=c, SubCategory=s,
                     Sales=sales, Profit=float(np.round(sales*margin, 2)), Quantity=int(rng.integers(1, 10)),
                     Target=float(np.round(sales*rng.uniform(0.8,1.2), 2))))
out = pathlib.Path(__file__).resolve().parent.parent / "data" / "superstore_sample.csv"
pd.DataFrame(rows).to_csv(out, index=False)
print(out, len(rows))
