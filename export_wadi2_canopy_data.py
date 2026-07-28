"""
Run via ArcGIS Pro's bundled python (has arcpy):
  "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe" export_wadi2_canopy_data.py

Exports Current Canopy, Mature Canopy, Additional Trees and Species for
Wadi Gudwanah and Wadi Umm Qassar from the new TreeCanopy_Output.gdb into
the SAME folders roads/large-parks already use (canopy_current_data/,
canopy_mature_data/, additional_trees_data/, species_data/), following the
exact pattern established in export_largepark_data.py.

Boundaries are NOT touched here -- Wadis_boundary.json already has both
wadis' boundaries from the earlier export_wadi_boundaries.py run.

Source feature classes are split by PROJECT_ID, not by dataset -- both
wadis live in one flat gdb, distinguished by that field.
"""
import arcpy, json, os

GDB = r"C:\Users\saeed\Downloads\wadis_2.1 (1)\wadis_2.1\TreeCanopy_Output.gdb"
OUT_DIR = r"C:\Users\saeed\Downloads\Aa_Canopy"

# PROJECT_ID (as stored in the gdb) -> display name used everywhere else on
# the dashboard (matches export_wadi_boundaries.py's NAME_OVERRIDES targets)
NAME_MAP = {
    "Wadi_Ghuduwana": "Wadi Gudwanah",
    "Wadi_UmmQasr": "Wadi Umm Qassar",
}

wgs84 = arcpy.SpatialReference(4326)


def safe_name(display_name):
    """Matches the dashboard's JS: name.replace(/\\s+/g, '_')"""
    return display_name.replace(" ", "_")


def densify_if_curved(geom):
    if getattr(geom, 'hasCurves', False):
        return geom.densify("DISTANCE", 0.5, 0)
    return geom


def polygon_to_geojson_geometry(geom84):
    return dict(geom84.__geo_interface__)


def export_polygon_layer(fc_name, out_folder):
    print("Exporting {} -> {}/<Wadi>.geojson".format(fc_name, out_folder))
    out_dir = os.path.join(OUT_DIR, out_folder)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    fields = ["SHAPE@", "PROJECT_ID"]
    by_wadi = {}
    with arcpy.da.SearchCursor(os.path.join(GDB, fc_name), fields) as cursor:
        for geom, project_id in cursor:
            display_name = NAME_MAP.get(project_id)
            if not display_name:
                print("  WARNING: unmapped PROJECT_ID '{}', skipping feature".format(project_id))
                continue
            geom = densify_if_curved(geom)
            geom84 = geom.projectAs(wgs84)
            geometry = polygon_to_geojson_geometry(geom84)
            feature = {"type": "Feature", "properties": {}, "geometry": geometry}
            by_wadi.setdefault(display_name, []).append(feature)

    for display_name, feats in by_wadi.items():
        geojson = {"type": "FeatureCollection", "features": feats}
        out_path = os.path.join(out_dir, safe_name(display_name) + ".geojson")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f)
        print("  {}: {} feature(s) -> {}".format(display_name, len(feats), out_path))


def export_species():
    print("Exporting TreeCanopy_00_TreesProject -> species_data/<Wadi>.geojson")
    out_dir = os.path.join(OUT_DIR, "species_data")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    fields = ["SHAPE@XY", "PROJECT_ID", "Species"]
    by_wadi = {}
    with arcpy.da.SearchCursor(os.path.join(GDB, "TreeCanopy_00_TreesProject"), fields,
                                spatial_reference=wgs84) as cursor:
        for (x, y), project_id, species in cursor:
            display_name = NAME_MAP.get(project_id)
            if not display_name:
                continue
            feature = {
                "type": "Feature",
                "properties": {"species": species or "Unknown"},
                "geometry": {"type": "Point", "coordinates": [x, y]}
            }
            by_wadi.setdefault(display_name, []).append(feature)

    for display_name, feats in by_wadi.items():
        geojson = {"type": "FeatureCollection", "features": feats}
        out_path = os.path.join(out_dir, safe_name(display_name) + ".geojson")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f)
        print("  {}: {} tree(s) -> {}".format(display_name, len(feats), out_path))


export_polygon_layer("TreeCanopy_02_CurrentNoOverlap", "canopy_current_data")
export_polygon_layer("TreeCanopy_04_MatureNoOverlap", "canopy_mature_data")
export_polygon_layer("TreeCanopy_08_AdditionalNoOverlap", "additional_trees_data")
export_species()
print("Done.")
