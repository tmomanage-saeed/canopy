"""
Run this inside ArcGIS Pro's Python window.

Standalone re-export of ONLY Additional_Trees_Canopy -> additional_trees_data/
as real polygon/multipolygon shapes (same logic as export_largepark_data.py),
so there is a fresh, unambiguous file written right now.
"""
import arcpy, json, os

GDB = r"C:\Users\saeed\Documents\ArcGIS\Projects\plantable\plantable.gdb"
OUT_DIR = r"C:\Users\saeed\Downloads\Aa_Canopy"
wgs84 = arcpy.SpatialReference(4326)


def polygon_to_geojson_geometry(geom84):
    # Use arcpy's own __geo_interface__ instead of manually walking parts/points --
    # the hand-rolled version produced degenerate 2-point (zero-area) rings, which
    # is why this rendered as a tiny point instead of the real shape.
    return dict(geom84.__geo_interface__)


out_dir = os.path.join(OUT_DIR, "additional_trees_data")
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

fields = ["SHAPE@", "ProjectNam"]
by_park = {}
with arcpy.da.SearchCursor(os.path.join(GDB, "Additional_Trees_Canopy"), fields) as cursor:
    for geom, park_name in cursor:
        if not park_name:
            continue
        geom84 = geom.projectAs(wgs84)
        geometry = polygon_to_geojson_geometry(geom84)
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
