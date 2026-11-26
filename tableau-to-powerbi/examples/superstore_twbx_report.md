# Phân tích workbook Tableau: `geocoding.twbx`

- Phiên bản Tableau: 18.1  ·  Worksheet: 22  ·  Dashboard: 6
- Dashboard: Commission Model, Customers, Order Details, Overview, Product, Shipping
- File đóng gói kèm (.twbx): Data/Superstore/Sales Commission.csv, Data/Superstore/Sales Target (US).xlsx, Data/Superstore/Sample - Superstore.xls, Data/1wxu94q1kekjvw19apavn0qb7c5l/Clipboard_20201022T150351.xls, TwbxExternalCache/TwbxLQResultsCacheV3/1097411106/.bin, TwbxExternalCache/TwbxLQResultsCacheV3/1097411106/.key, TwbxExternalCache/TwbxLQTimestampsCacheV3/217959933/.bin, TwbxExternalCache/TwbxLQTimestampsCacheV3/217959933/.key, Local Data/Airport.tds, Local Data/GeocodingData.hyper ...

## Worksheet → gợi ý Power BI

| Sheet | Mark | Rows | Columns | Encoding | Loại chart (đoán) | Dựng lại trong Power BI |
|---|---|---|---|---|---|---|
| CommissionProjection | Automatic | Rank over 3, Sales Person | - | color: Measure Names; lod: Achieved Quota, MAX(OTE (Variable)) [đo], SUM(Achievement (estimated)) [đo], Total Compensation [đo] | Crosstab / text table | Visual gốc: Matrix / Table (+ conditional formatting) |
| CustomerOverview | Automatic | Region | Measure Names | lod: COUNTD(Customer Name) [đo], Profit Ratio [đo], SUM(Profit) [đo], SUM(Quantity) [đo], SUM(Sales) [đo], Sales per Customer [đo] | Crosstab / text table | Visual gốc: Matrix / Table (+ conditional formatting) |
| CustomerRank | Automatic | Customer Name | SUM(Sales) [đo] | color: Profit Ratio [đo]; tooltip: SUM(Profit) [đo]; lod:  | Bar | Visual gốc: Clustered/Stacked bar |
| CustomerScatter | Automatic | SUM(Profit) [đo] | SUM(Sales) [đo] | color: Profit Ratio [đo]; lod: Customer Name, Profit Ratio [đo] | Scatter | Visual gốc: Scatter; có trend line + quadrant: deneb/06_scatter_quadrant.json |
| DaystoShip | Automatic | Product Name | Order Date [thời gian] | color: Ship Status; size: SUM(Days to Ship Actual) [đo]; lod: Customer Name, Order ID, Ship Mode | Gantt | Deneb: bar với x=ngày bắt đầu, x2=ngày kết thúc (hoặc visual Gantt miễn phí trên AppSource) |
| Forecast | Automatic | Segment | MONTH(trunc)(Order Date) [thời gian] | color: Forecast Indicator, Segment | Line | Visual gốc: Line chart |
| OTE | Automatic | Measure Names | - | text:  | Crosstab / text table | Visual gốc: Matrix / Table (+ conditional formatting) |
| Performance | Bar | YEAR(Order Date), MONTH(Order Date), Segment | Category, SUM(Sales) [đo] | color: Sales above Target?; lod: Calculation_5144658905056067585 [đo], SUM(Sales Target) [đo] | Bar | Visual gốc: Clustered/Stacked bar |
| Product Detail Sheet | Automatic | Order ID, Customer Name, Order Date, Ship Date, Ship Mode | Measure Names | text:  | Crosstab / text table | Visual gốc: Matrix / Table (+ conditional formatting) |
| ProductDetails | Circle | Category, Sub-Category | Segment, SUM(Sales) [đo] | color: Profit Ratio [đo]; lod: Category, Product Name, SUM(Profit) [đo] | Dot plot / strip | Visual gốc: Scatter (trục phân loại); hoặc Deneb mark point |
| ProductView | Square | Category, YEAR(Order Date) | MONTH(Order Date) | color: SUM(Sales) [đo]; text: SUM(Sales) [đo]; tooltip: SUM(Profit) [đo] | Highlight table / heatmap | Deneb: deneb/01_highlight_table.json; hoặc Matrix + conditional formatting (gốc) |
| QuotaAttainment | Automatic | Rank over 3, Sales Person | SUM(Achievement (estimated)) [đo] | text: % of quota achieved [đo]; color: Achieved Quota; lod: MAX(OTE (Variable)) [đo], New Quota, Total Compensation [đo] | Bar | Visual gốc: Clustered/Stacked bar |
| Sale Map | Multipolygon | Latitude (generated) | Longitude (generated) | color: Profit Ratio [đo]; lod: State; geometry: Geometry (generated) | Bản đồ | Visual gốc: Map / Filled map / Azure Maps |
| Sales | Automatic | Measure Names | - | text:  | Crosstab / text table | Visual gốc: Matrix / Table (+ conditional formatting) |
| Sales by Product | Area | Category, SUM(Sales) [đo] | MONTH(trunc)(Order Date) [thời gian] | color: Order Profitable?; tooltip: SUM(Profit) [đo] | Area small multiples | Visual gốc: Area (small multiples); hoặc deneb/07_trellis_area.json |
| Sales by Segment | Area | Segment, SUM(Sales) [đo] | MONTH(trunc)(Order Date) [thời gian] | color: Order Profitable?; tooltip: SUM(Profit) [đo] | Area small multiples | Visual gốc: Area (small multiples); hoặc deneb/07_trellis_area.json |
| Sheet 22 | Automatic | Latitude (generated) | Longitude (generated) | lod: Random Location | Bản đồ | Visual gốc: Map / Filled map / Azure Maps |
| ShipSummary | Automatic | - | - | color: Ship Status; text: Ship Status | Text / KPI | Visual gốc: Card / Multi-row card |
| ShippingTrend | Area | __tableau_internal_object_id__, COUNT(Orders_6D2EF74F348B46BDA976A7AEEA6FB5C9) [đo] | YEAR(Order Date), WEEK(trunc)(Order Date) [thời gian] | color: Ship Status | Area small multiples | Visual gốc: Area (small multiples); hoặc deneb/07_trellis_area.json |
| Tooltip: Profit Ratio by City | Automatic | City | Profit Ratio [đo] | color: Profit Ratio [đo] | Bar | Visual gốc: Clustered/Stacked bar |
| Total Sales | Automatic | - | Measure Names | text:  | Crosstab / text table | Visual gốc: Matrix / Table (+ conditional formatting) |
| What If Forecast | Automatic | Region, Segment, Measure Names | QUARTER(Order Date), MONTH(Order Date) | color: Measure Names; text: ; lod: Calculation_9330126204734562 [đo], SUM(Sales Forecast) [đo], SUM(Sales) [đo] | Crosstab / text table | Visual gốc: Matrix / Table (+ conditional formatting) |

## Calculated field (cần viết lại bằng DAX)

| Tên | Công thức Tableau |
|---|---|
| Base Salary | `50000` |
| Commission Rate | `18.399999999999999` |
| New Quota | `500000` |
| Sort by | `"Names"` |
| New Business Growth | `0.59999999999999998` |
| Churn Rate | `0.064000000000000001` |
| Achievement (estimated) | `[Sales]` |
| Achieved Quota | `if SUM([Achievement (copy)]) >= [Parameters].[New Quota] then "100% +" elseif SUM([Achievement (copy)]) >= 0.75 * [Parameters].[New Quota] then "75-100%" elseif SUM([Achievement (copy)]) >= 0.5 * [Parameters].[New Quota] then "50-75%" else "Below 50%" end` |
| Base (Variable) | `[Parameters].[Base Salary]` |
| % of quota achieved | `AVG([Achievement (copy)])/[Parameters].[New Quota]` |
| Rank over 3 | `ROUND(INDEX() / 3 - 0.6,0) + 1` |
| Sort by field | `if [Parameters].[Parameter 1 1]="Names" then 0 elseif [Parameters].[Parameter 1 1]="% quota descending" then -[Calculation_0440925131659539] else [Calculation_0440925131659539] end` |
| Commission (Variable) | `([Parameters].[Commission Rate]*[Sales])/100` |
| Estimate Compensation label | `"Estimated Compensation:"` |
| OTE (Variable) | `[Parameters].[Base Salary] + ([Parameters].[Commission Rate]*[Parameters].[New Quota])/100` |
| Total Compensation | `MIN([Base (Variable)]) + SUM([Commission (Variable)])` |
| Total Sales label | `"Total Sales:"` |
| Days to Ship Actual | `DATEDIFF('day',[Order Date],[Ship Date])` |
| Sales Forecast | `[Sales]*(1-[Parameters].[Parameter 2])*(1+[Parameters].[Parameter 1])` |
| Ship Status | `if [Calculation_0831103151444568]> [Calculation_6861103170623145] then "Shipped Late" elseIF [Calculation_0831103151444568]= [Calculation_6861103170623145] then "Shipped On Time" Else "Shipped Early" end` |
| Days to Ship Scheduled | `CASE [Ship Mode] WHEN "Same Day" THEN 0 WHEN "First Class" THEN 1 WHEN "Second Class" THEN 3 WHEN "Standard Class" THEN 6 END` |
| Order Profitable? | `{fixed [Order ID]:sum([Profit])}>0 // calculates the profit at the order level` |
| Sales per Customer | `Sum([Sales])/countD([Customer Name])` |
| Profit Ratio | `sum([Profit])/sum([Sales])` |
| Sales above Target? | `If Sum([Sales])>SUM([federated.0hgpf0j1fdpvv316shikk0mmdlec].[Sales Target]) then "Above Target" else "Below Target" end` |
| Units estimate | `ROUND([Quantity]*(1-[Parameters].[Parameter 2])*(1+[Parameters].[Parameter 1]),0)` |
| Profit per Order | `Sum([Profit])/countD([Order ID])` |
