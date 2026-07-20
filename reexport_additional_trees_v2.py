"""
Run this inside ArcGIS Pro's Python window.

Re-exports Additional_Trees_Canopy from the ORIGINAL source gdb (not the
plantable.gdb copy used before, which apparently had corrupted/degenerate
geometry for this one feature class) -> additional_trees_data/<Park>.geojson.

First prints the schema/sample rows so we can confirm the park-name field
before exporting (it may not be called "ProjectNam" in this gdb).
"""
import arcpy, json, os

SRC_GDB = r"D:\BPLA Dropbox\BPLA dropbox\BPLA Dropbox\03 Planning\1232-T2-TM2_1-GIS-Remote-Sensing\06_GIS-Data\35_Projects Review\large_park\Large_Parks.gdb"
FC = "Additional_Trees_Canopy"
OUT_DIR = r"C:\Users\saeed\Downloads\Aa_Canopy"
wgs84 = arcpy.SpatialReference(4326)

fc_path = os.path.join(SRC_GDB, FC)

print("=" * 60)
print("Schema of", fc_path)
desc = arcpy.Describe(fc_path)
print("Shape type:", desc.shapeType)
count = int(arcpy.management.GetCount(fc_path)[0])
print("Feature count:", count)
fields = [f.name for f in arcpy.ListFields(fc_path)]
print("Fields:", fields)

with arcpy.da.SearchCursor(fc_path, fields) as cursor:
    for i, row in enumerate(cursor):
        if i >= 3:
            break
        print("Sample row:", dict(zip(fields, row)))
print("=" * 60)

# Guess the park-name field: prefer an exact "ProjectNam" match, else the
# first text field whose name looks like a project/park identifier.
name_field = None
if "ProjectNam" in fields:
    name_field = "ProjectNam"
else:
    for candidate in fields:
        low = candidate.lower()
        if "project" in low or "park" in low or "name" in low:
            name_field = candidate
            break

if not name_field:
    print("Could NOT find a park-name field automatically. Fields were:", fields)
    print("Stopping -- tell me which field holds the park name and I'll fix the script.")
else:
    print("Using name field:", name_field)
    out_dir = os.path.join(OUT_DIR, "additional_trees_data")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    by_park = {}
    with arcpy.da.SearchCursor(fc_path, ["SHAPE@", name_field]) as cursor:
        for geom, park_name in cursor:
            if not park_name:
                continue
            # Each "tree" is a true circular curve (2 control points + curve
            # metadata) -- densify BEFORE reprojecting so we get the real
            # circle outline instead of a degenerate 2-point ring.
            if getattr(geom, 'hasCurves', False):
                geom = geom.densify("DISTANCE", 0.5, 0)
            geom84 = geom.projectAs(wgs84)
            geometry = dict(geom84.__geo_interface__)
            feature = {"type": "Feature", "properties": {}, "geometry": geometry}
            by_park.setdefault(park_name, []).append(feature)

    for park_name, feats in by_park.items():
        geojson = {"type": "FeatureCollection", "features": feats}
        out_path = os.path.join(out_dir, park_name + ".geojson")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f)
        print("{}: {} feature(s), geometry type(s): {} -> {}".format(
            park_name, len(feats), set(ft["geometry"]["type"] for ft in feats), out_path))

print("Done.")
