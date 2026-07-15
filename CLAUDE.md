# Green Riyadh Canopy Cover Review Dashboard

## Project
Interactive HTML dashboard for 15 road projects (KPI Report). Served via `python -m http.server 8080`.

## Main File
- KPI_Report_Template.html (11 slides)

## Data Sources
- roads_data.xlsx → EXCEL_DATA in HTML (hardcoded JS object)
- Projects_boundry.json → road boundaries with CENTER_LAT/CENTER_LNG
- GeoJSON folders: plantable_data/, canopy_current_data/, canopy_mature_data/, species_data/, additional_trees_data/
  - Files inside each folder are named `<safeName>.geojson`, one per road, where safeName matches the road's display name.

## Key Paths
- Dashboard: C:\Users\saeed\Downloads\Aa_Canopy\
- ArcGIS Pro GDB: C:\Users\saeed\Documents\ArcGIS\Projects\NEW_TEST\New_test3.gdb

## Slide Structure
1. Title (Canopy Cover Review)
2. Intro divider
3. Satellite comparison (3 synced Wayback maps)
4. Species table (dynamic per road)
5. Current Canopy divider
6. Current Canopy Cover (tables + 2 maps + legend)
7. Mature Canopy divider
8. Mature Canopy Cover (3 tables + 2 maps + legend)
9. Conclusion divider
10. Conclusion text + road photo
11. Thank You

## Important Rules
- NEVER change slide 1 title text
- ALL table data comes from EXCEL_DATA (from Excel), NOT from JSON attributes
- Road names: replace _ with space, Rd with Road (displayName function)
- Maps use CENTER_LAT/CENTER_LNG from Projects_boundry.json
- Notepad++ single-line find-and-replace for small changes
- Font: Poppins for body, NeoSansArabic for titles
