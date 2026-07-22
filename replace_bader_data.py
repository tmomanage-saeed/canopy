"""
Run this inside ArcGIS Pro's Python window.

Replaces ONLY Bader's 4 data files (additional trees, mature canopy, current
canopy, species/trees) from a separate, dedicated source gdb -- boundary and
plantable area are untouched.

Source: C:\\Users\\saeed\\Downloads\\bader park\\New Folder\\TreeCanopy_Output.gdb
  - Badar_additional_tree          -> additional_trees_data/Bader.geojson
  - TreeCanopy_04_MatureNoOverlap  -> canopy_mature_data/Bader.geojson
  - TreeCanopy_02_CurrentNoOverlap -> canopy_current_data/Bader.geojson
  - TreeCanopy_00_Trees            -> species_data/Bader.geojson (points)

Uses the same reliable geometry conversion established for the other large
park exports: arcpy's own __geo_interface__ (not manual point/part walking),
plus densify for any true-curve geometry (circular tree buffers etc.).
"""
import arcpy, json, os

SRC_GDB = r"C:\Users\saeed\Downloads\bader park\New Folder\TreeCanopy_Output.gdb"
OUT_DIR = r"C:\Users\saeed\Downloads\Aa_Canopy"
wgs84 = arcpy.SpatialReference(4326)


def densify_if_curved(geom):
    if getattr(geom, 'hasCurves', False):
        return geom.densify("DISTANCE", 0.5, 0)
    return geom


def polygon_to_geojson_geometry(geom84):
    return dict(geom84.__geo_interface__)


def print_schema(fc_path, label):
    print("=" * 60)
    print(label, "->", fc_path)
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
    return fields


def export_single_polygon_feature(fc_name, out_path):
    fc_path = os.path.join(SRC_GDB, fc_name)
    print_schema(fc_path, fc_name)

    feats = []
    with arcpy.da.SearchCursor(fc_path, ["SHAPE@"]) as cursor:
        for (geom,) in cursor:
            geom = densify_if_curved(geom)
            geom84 = geom.projectAs(wgs84)
            geometry = polygon_to_geojson_geometry(geom84)
            feats.append({"type": "Feature", "properties": {}, "geometry": geometry})

    out_dir = os.path.dirname(out_path)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    geojson = {"type": "FeatureCollection", "features": feats}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f)
    print("Wrote {} feature(s) -> {}".format(len(feats), out_path))


def export_trees_as_points(fc_name, out_path):
    fc_path = os.path.join(SRC_GDB, fc_name)
    fields = print_schema(fc_path, fc_name)

    species_field = None
    for candidate in fields:
        low = candidate.lower()
        if low in ("species", "botanicalname", "species_1", "tree_species"):
            species_field = candidate
            break
    if not species_field:
        for candidate in fields:
            if "spec" in candidate.lower():
                species_field = candidate
                break

    if not species_field:
        print("Could NOT find a species field automatically. Fields were:", fields)
        print("Stopping -- tell me which field holds the species name and I'll fix the script.")
        return

    print("Using species field:", species_field)

    feats = []
    with arcpy.da.SearchCursor(fc_path, ["SHAPE@XY", species_field], spatial_reference=wgs84) as cursor:
        for (x, y), species in cursor:
            feats.append({
                "type": "Feature",
                "properties": {"species": species or "Unknown"},
                "geometry": {"type": "Point", "coordinates": [x, y]}
            })

    out_dir = os.path.dirname(out_path)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    geojson = {"type": "FeatureCollection", "features": feats}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f)
    print("Wrote {} tree(s) -> {}".format(len(feats), out_path))


export_single_polygon_feature("Badar_additional_tree", os.path.join(OUT_DIR, "additional_trees_data", "Bader.geojson"))
export_single_polygon_feature("TreeCanopy_04_MatureNoOverlap", os.path.join(OUT_DIR, "canopy_mature_data", "Bader.geojson"))
export_single_polygon_feature("TreeCanopy_02_CurrentNoOverlap", os.path.join(OUT_DIR, "canopy_current_data", "Bader.geojson"))
export_trees_as_points("TreeCanopy_00_Trees", os.path.join(OUT_DIR, "species_data", "Bader.geojson"))
print("Done.")
