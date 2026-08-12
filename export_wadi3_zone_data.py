"""
Run via ArcGIS Pro's bundled python (has arcpy):
  "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe" export_wadi3_zone_data.py

Source: wadi_3.1 batch, C:\\Users\\saeed\\Downloads\\wadi_3.1\\wadi_3.1\\TreeCanopy_Output.gdb.
This batch splits each wadi into 3 zones (Top/Slope/Bed) at the source, unlike
the earlier wadi_2.3 batch (export_wadi2_canopy_data.py) which had one polygon
per wadi. Two things happen here:

1. Current/Mature/Additional NoOverlap layers -- same target folders as before
   (canopy_current_data/, canopy_mature_data/, additional_trees_data/), but now
   each wadi's 3 zone features are merged into that one <Wadi>.geojson (matches
   how the dashboard already renders these as a single-color layer, zone-blind).

2. NEW: TreeCanopy_00_AllBoundaries -> wadi_zone_boundaries/<Wadi>.geojson, kept
   as 3 SEPARATE features per wadi (each tagged properties.zone = top/slope/bed)
   so the dashboard can draw 3 distinctly-colored boundary LINES instead of one.

PROJECT_ID / Layer naming is inconsistent within this single gdb (e.g.
"Wadi_Ghuduwana||TOP" vs "Wadi_Ghuduwanah_Slop||SLOPE" vs "WadiUmm_Qasr_Bed" for
what are only 2 real wadis) -- matched by loose substring on a normalized
(lowercased, underscores stripped) form instead of an exact dict lookup.
"""
import arcpy, json, os

GDB = r"C:\Users\saeed\Downloads\wadi_3.1\wadi_3.1\TreeCanopy_Output.gdb"
OUT_DIR = r"C:\Users\saeed\Downloads\Aa_Canopy"

wgs84 = arcpy.SpatialReference(4326)


def match_wadi(raw_name):
    n = (raw_name or "").lower().replace("_", "").replace(" ", "")
    if "ghuduwan" in n or "gudwan" in n:
        return "Wadi Gudwanah"
    if "ummqasr" in n or "ummqassar" in n:
        return "Wadi Umm Qassar"
    return None


def safe_name(display_name):
    """Matches the dashboard's JS: name.replace(/\\s+/g, '_')"""
    return display_name.replace(" ", "_")


def densify_if_curved(geom):
    if getattr(geom, 'hasCurves', False):
        return geom.densify("DISTANCE", 0.5, 0)
    return geom


def to_geojson_geometry(geom84):
    return dict(geom84.__geo_interface__)


def export_merged_polygon_layer(fc_name, out_folder):
    """Current/Mature/Additional NoOverlap -- PROJECT_ID is 'rawbase||ZONETYPE'.
    All zones for a wadi get merged into one FeatureCollection (zone-blind),
    same shape as before this batch."""
    print("Exporting {} -> {}/<Wadi>.geojson (merged zones)".format(fc_name, out_folder))
    out_dir = os.path.join(OUT_DIR, out_folder)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    by_wadi = {}
    with arcpy.da.SearchCursor(os.path.join(GDB, fc_name), ["SHAPE@", "PROJECT_ID"]) as cursor:
        for geom, project_id in cursor:
            raw_base = (project_id or "").split("||")[0]
            display_name = match_wadi(raw_base)
            if not display_name:
                print("  WARNING: unmatched PROJECT_ID '{}', skipping feature".format(project_id))
                continue
            geom = densify_if_curved(geom)
            geom84 = geom.projectAs(wgs84)
            feature = {"type": "Feature", "properties": {}, "geometry": to_geojson_geometry(geom84)}
            by_wadi.setdefault(display_name, []).append(feature)

    for display_name, feats in by_wadi.items():
        geojson = {"type": "FeatureCollection", "features": feats}
        out_path = os.path.join(out_dir, safe_name(display_name) + ".geojson")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f)
        print("  {}: {} feature(s) -> {}".format(display_name, len(feats), out_path))


def export_zone_boundaries():
    """TreeCanopy_00_AllBoundaries -> wadi_zone_boundaries/<Wadi>.geojson, 3
    features per wadi, each tagged properties.zone = 'top'/'slope'/'bed'."""
    fc_name = "TreeCanopy_00_AllBoundaries"
    out_folder = "wadi_zone_boundaries"
    print("Exporting {} -> {}/<Wadi>.geojson (3 zone features each)".format(fc_name, out_folder))
    out_dir = os.path.join(OUT_DIR, out_folder)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    by_wadi = {}
    fields = ["SHAPE@", "Layer", "AREA_TYPE"]
    with arcpy.da.SearchCursor(os.path.join(GDB, fc_name), fields) as cursor:
        for geom, layer_name, area_type in cursor:
            display_name = match_wadi(layer_name)
            if not display_name:
                print("  WARNING: unmatched Layer '{}', skipping feature".format(layer_name))
                continue
            zone = (area_type or "").replace("WADI_", "").strip().lower()  # TOP/SLOPE/WADI_BED -> top/slope/bed
            geom = densify_if_curved(geom)
            geom84 = geom.projectAs(wgs84)
            feature = {
                "type": "Feature",
                "properties": {"zone": zone},
                "geometry": to_geojson_geometry(geom84)
            }
            by_wadi.setdefault(display_name, []).append(feature)

    for display_name, feats in by_wadi.items():
        geojson = {"type": "FeatureCollection", "features": feats}
        out_path = os.path.join(out_dir, safe_name(display_name) + ".geojson")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f)
        zones_found = sorted(set(f["properties"]["zone"] for f in feats))
        print("  {}: {} feature(s) [{}] -> {}".format(display_name, len(feats), ", ".join(zones_found), out_path))


export_merged_polygon_layer("TreeCanopy_02_CurrentNoOverlap", "canopy_current_data")
export_merged_polygon_layer("TreeCanopy_04_MatureNoOverlap", "canopy_mature_data")
export_merged_polygon_layer("TreeCanopy_08_AdditionalNoOverlap", "additional_trees_data")
export_zone_boundaries()
print("Done.")
