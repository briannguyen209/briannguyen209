"""Generate ILLUSTRATIVE (fictional) datasets for the NYT-style Deneb charts.

None of these numbers are real. Entity names are generic or sample-data names;
airport and port coordinates are real places so the maps look right, but every
count / route / position is randomly generated.

Usage: python nyt-style/make_data.py   -> writes nyt-style/data/*.csv
"""
import csv, math, pathlib, random

OUT = pathlib.Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)
rnd = random.Random(7)


def write(name, rows):
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


# 1) Streak tiles: "Quarters since each product line last beat its target" -------------
# Each entity: latest quarter (beat target, blue) on top, then N consecutive misses (red),
# then the last quarter it beat target (blue) at the bottom of the column.
streaks = {"Phones": 0, "Binders": 1, "Chairs": 5, "Printers": 5, "Paper": 8, "Tables": 13, "Bookcases": 31}
special = {("Paper", 3), ("Bookcases", 9), ("Bookcases", 22), ("Tables", 7)}  # footnote markers
rows = []
for ent, n in streaks.items():
    q = 2026 * 4 + 1  # 2026 Q2 (index)
    for i in range(n + 2 if n else 1):
        y, qq = divmod(q - i, 4)
        status = "Beat" if i == 0 or i == n + 1 else "Missed"
        if n == 0 and i == 0: status = "Beat"
        rows.append({"Product": ent, "Period": f"{y} Q{qq + 1}", "PeriodsAgo": i, "Result": status,
                     "Note": "*" if (ent, i) in special else ""})
    if n == 0:  # first column also shows the previous beat, like "Maine 2024"
        y, qq = divmod(q - 1, 4)
        rows.append({"Product": ent, "Period": f"{y} Q{qq + 1}", "PeriodsAgo": 1, "Result": "Beat", "Note": "†"})
write("streaks.csv", rows)

# 2) Diverging bars: "Sales vs target by year (margin, $k)" -------------------------------
rows, v = [], -28.0
for yr in range(1990, 2027):
    v = max(-40, min(14, v * 0.75 + rnd.gauss(0, 9)))
    if yr in (2010, 2020): v = 0.0
    elif round(v) == 0: v = rnd.choice([-2.0, 2.0])
    rows.append({"Year": yr, "Margin": round(v), "Projected": "Yes" if yr == 2026 else "No"})
rows[-1]["Margin"] = -8
write("balance.csv", rows)

# 3) US route map: "Cancelled shipments by route" -----------------------------------------
airports = {  # code: (name, lon, lat, weight)
    "ATL": ("Atlanta", -84.43, 33.64, 9), "ORD": ("Chicago O'Hare", -87.90, 41.98, 9), "DEN": ("Denver", -104.67, 39.86, 9),
    "IAH": ("Houston", -95.34, 29.98, 6), "SFO": ("San Francisco", -122.38, 37.62, 6), "SEA": ("Seattle", -122.31, 47.45, 6),
    "LGA": ("LaGuardia", -73.87, 40.78, 6), "BOS": ("Boston", -71.01, 42.37, 4), "DFW": ("Dallas", -97.04, 32.90, 4),
    "LAX": ("Los Angeles", -118.41, 33.94, 4), "PHX": ("Phoenix", -112.01, 33.43, 3), "MSP": ("Minneapolis", -93.22, 44.88, 3),
    "DTW": ("Detroit", -83.35, 42.21, 3), "CLT": ("Charlotte", -80.94, 35.21, 3), "MCO": ("Orlando", -81.31, 28.43, 3),
    "MIA": ("Miami", -80.29, 25.80, 3), "SLC": ("Salt Lake City", -111.98, 40.79, 2), "LAS": ("Las Vegas", -115.15, 36.08, 3),
    "SAN": ("San Diego", -117.19, 32.73, 2), "PDX": ("Portland", -122.60, 45.59, 2), "BNA": ("Nashville", -86.68, 36.12, 2),
    "AUS": ("Austin", -97.67, 30.19, 2), "MSY": ("New Orleans", -90.26, 29.99, 2), "STL": ("St. Louis", -90.37, 38.75, 2),
    "MCI": ("Kansas City", -94.71, 39.30, 1), "OMA": ("Omaha", -95.89, 41.30, 1), "DSM": ("Des Moines", -93.66, 41.53, 1),
    "BOI": ("Boise", -116.22, 43.56, 1), "BIL": ("Billings", -108.54, 45.81, 1), "FAR": ("Fargo", -96.82, 46.92, 1),
    "ABQ": ("Albuquerque", -106.61, 35.04, 1), "OKC": ("Oklahoma City", -97.60, 35.39, 1), "MEM": ("Memphis", -89.98, 35.04, 1),
    "IND": ("Indianapolis", -86.29, 39.72, 2), "CMH": ("Columbus", -82.89, 39.99, 1), "PIT": ("Pittsburgh", -80.23, 40.49, 1),
    "PHL": ("Philadelphia", -75.24, 39.87, 2), "DCA": ("Washington", -77.04, 38.85, 3), "RDU": ("Raleigh", -78.79, 35.88, 2),
    "JAX": ("Jacksonville", -81.69, 30.49, 1), "TPA": ("Tampa", -82.53, 27.98, 2), "BUF": ("Buffalo", -78.73, 42.94, 1),
    "PWM": ("Portland ME", -70.31, 43.65, 1), "ANC": ("Anchorage", -149.99, 61.17, 1), "HNL": ("Honolulu", -157.92, 21.32, 2),
    "OGG": ("Maui", -156.43, 20.90, 1), "SMF": ("Sacramento", -121.59, 38.70, 1), "TUS": ("Tucson", -110.94, 32.12, 1),
    "ELP": ("El Paso", -106.38, 31.81, 1), "SAT": ("San Antonio", -98.47, 29.53, 1), "LIT": ("Little Rock", -92.22, 34.73, 1),
    "BHM": ("Birmingham", -86.75, 33.56, 1), "SAV": ("Savannah", -81.20, 32.13, 1), "RIC": ("Richmond", -77.32, 37.51, 1),
    "BTV": ("Burlington", -73.15, 44.47, 1), "GRR": ("Grand Rapids", -85.52, 42.88, 1), "MKE": ("Milwaukee", -87.90, 42.95, 1),
    "RAP": ("Rapid City", -103.06, 44.05, 1), "GEG": ("Spokane", -117.53, 47.62, 1), "JAC": ("Jackson Hole", -110.74, 43.61, 1),
}
codes = list(airports)
weights = [airports[c][3] for c in codes]
routes = {}
while len(routes) < 420:
    a, b = rnd.choices(codes, weights)[0], rnd.choices(codes, weights)[0]
    if a == b: continue
    key = tuple(sorted((a, b)))
    routes[key] = routes.get(key, 0) + 1
rows = []
for (a, b), n in sorted(routes.items()):
    rows.append({"Origin": a, "OriginName": airports[a][0], "OriginLon": airports[a][1], "OriginLat": airports[a][2],
                 "Dest": b, "DestName": airports[b][0], "DestLon": airports[b][1], "DestLat": airports[b][2],
                 "Cancelled": n})
write("routes.csv", rows)

# 4) Globe: "Where tankers were" — waypoints of sea lanes (lon, lat), all from the Gulf ------
GULF = [(48.3, 29.2), (50.3, 27.6), (52.6, 26.1), (55.2, 26.4), (56.6, 26.4), (57.8, 25.0), (59.0, 23.2)]
lanes = {
    "East Asia": GULF + [(62, 21), (67, 17), (72, 11), (77, 6.8), (80.5, 5.6), (86, 5.8), (92, 6.2), (96.5, 5.8), (99.5, 3.4),
                         (102.5, 1.6), (104.2, 1.3), (105.5, 3.5), (108.5, 8), (111.2, 12.5), (114, 17.5), (117, 21.3),
                         (120.5, 23.5), (123.5, 28), (127, 31.5), (130.5, 33.2), (134.5, 33.4), (138.5, 34.6)],
    "South China": GULF + [(62, 21), (67, 17), (72, 11), (77, 6.8), (80.5, 5.6), (86, 5.8), (92, 6.2), (96.5, 5.8), (99.5, 3.4),
                           (102.5, 1.6), (104.2, 1.3), (106.5, 5), (109.5, 11), (112, 16.5), (114, 21.5)],
    "Korea": GULF + [(62, 21), (67, 17), (72, 11), (77, 6.8), (80.5, 5.6), (86, 5.8), (92, 6.2), (96.5, 5.8), (99.5, 3.4),
                     (102.5, 1.6), (104.2, 1.3), (106, 4.5), (110, 11.5), (115, 19), (119.5, 22.5), (122.5, 27), (124.5, 32), (127, 34.6)],
    "India West": GULF + [(61, 23.5), (65, 23.0), (68.5, 21.5), (71.5, 19.5), (72.7, 18.9)],
    "Karachi": GULF + [(61, 24.2), (64, 24.6), (66.9, 24.7)],
    "Bay of Bengal": GULF + [(62, 21), (67, 17), (72, 11), (77, 6.8), (80.5, 5.6), (82.5, 7.5), (81.5, 11), (80.5, 13.1)],
    "Suez": GULF[:6] + [(58.3, 23.5), (57.5, 19.5), (54, 15.5), (50, 13.5), (46, 12.3), (43.5, 12.6), (42, 14.5), (39.8, 18.5),
                        (37.5, 22.5), (35.2, 26.5), (33.6, 28.6), (32.6, 29.7)],
    "Cape": GULF[:6] + [(58.3, 23.5), (59, 18), (57, 10), (53, 2), (47.5, -6), (43, -14), (40.5, -20), (36.5, -26),
                        (32, -31), (26, -34.8), (19.5, -35.5), (14, -31), (8, -24), (2, -14)],
    "East Africa": GULF[:6] + [(58.3, 23.5), (58.5, 18), (55, 10), (49.5, 2), (43, -3), (40.2, -4.6), (39.6, -6.5)],
    "Australia": GULF + [(62, 21), (67, 17), (72, 11), (77, 6.8), (82, 2), (92, -6), (103, -14), (110, -22), (114.8, -28)],
    "Gulf local": [(48.3, 29.2), (49.5, 28.3), (50.6, 26.8), (51.6, 25.6), (53.5, 25.6), (55.2, 26.4)],
}
share = {"East Asia": 60, "South China": 40, "Korea": 30, "India West": 30, "Karachi": 15, "Bay of Bengal": 15,
         "Suez": 25, "Cape": 18, "East Africa": 10, "Australia": 8, "Gulf local": 20}
rows, rid = [], 0
for lane, n in share.items():
    pts = lanes[lane]
    for _ in range(n):
        rid += 1
        phase, amp = rnd.uniform(0, 6.28), rnd.uniform(0.1, 0.9)
        for s, (lon, lat) in enumerate(pts):
            taper = min(s, len(pts) - 1 - s, 3) / 3  # converge at both ends
            j = amp * taper * math.sin(phase + s * 0.7)
            rows.append({"Kind": "Route", "Id": rid, "Seq": s, "Lane": lane,
                         "Lon": round(lon + j * 0.7, 3), "Lat": round(lat + j, 3)})
        # one current position somewhere along the lane, biased to the Gulf
        s = min(int(rnd.betavariate(0.7, 2.2) * (len(pts) - 1)), len(pts) - 2)
        t = rnd.random()
        (x1, y1), (x2, y2) = pts[s], pts[s + 1]
        rows.append({"Kind": "Position", "Id": rid, "Seq": 0, "Lane": lane,
                     "Lon": round(x1 + (x2 - x1) * t + rnd.gauss(0, 0.15), 3), "Lat": round(y1 + (y2 - y1) * t + rnd.gauss(0, 0.15), 3)})
for _ in range(160):  # crowding at the strait and in the Gulf
    lon, lat = rnd.choice(GULF[1:6])
    rows.append({"Kind": "Position", "Id": 0, "Seq": 0, "Lane": "Gulf", "Lon": round(lon + rnd.gauss(0, 0.3), 3),
                 "Lat": round(lat + rnd.gauss(0, 0.15), 3)})
write("tankers.csv", rows)
