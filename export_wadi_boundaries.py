"""
Run this inside ArcGIS Pro's Python window (View > Python), or via arcpy
in an ArcGIS Pro-aware Python environment.

Exports every polygon feature class found in wadi_work.gdb into ONE
combined JSON file (Wadis_boundary.json) in the same Esri-JSON boundary
format the dashboard already uses for roads (Projects_boundry.json):
attributes + esriGeometryPolygon rings in WGS84.

Scope for now: ONLY boundary + name + centroid (CENTER_LAT/CENTER_LNG).
No plantable / current canopy / mature canopy / species / additional
trees attributes are added at this stage -- that comes later.
"""
import arcpy, json, os

GDB = r"C:\Users\saeed\Documents\ArcGIS\Projects\NEW_TEST\wadi_work.gdb"
OUT_FILE = r"C:\Users\saeed\Downloads\Aa_Canopy\Wadis_boundary.json"

# Feature classes to skip entirely (fill in after reviewing the printed
# list the first time you run this, e.g. {"airport_wadi"})
SKIP = set([])

# Manual renames for feature classes whose name doesn't read cleanly,
# e.g. "WadiAyusanKACSTPhase1": "Wadi Ayusan Phase 1"
NAME_OVERRIDES = {
    "airport_wadi": "Airport Wadi",
    "Wadi_Ayusan": "Wadi Al Laysan Linear Park",
    "Wadi_Ghuduwanah": "Wadi Gudwanah",
    "Wadi_UmmQaser": "Wadi Umm Qassar",
    "WadiAyusanKACSTPhase1": "Branch of Wadi Al Laysan Phase 1 (KACST)",
    "WadiAyusanKACSTPhase2": "Branch of Wadi Al Laysan Phase 2 (KACST)"
}


def clean_name(fc_name):
    if fc_name in NAME_OVERRIDES:
        return NAME_OVERRIDES[fc_name]
    return fc_name.replace('_', ' ').strip()


def list_all_polygon_fcs(gdb):
    result = []
    old_ws = arcpy.env.workspace
    arcpy.env.workspace = gdb
    for fc in arcpy.ListFeatureClasses(feature_type='Polygon') or []:
        result.append(fc)
    for ds in arcpy.ListDatasets(feature_type='Feature') or []:
        arcpy.env.workspace = os.path.join(gdb, ds)
        for fc in arcpy.ListFeatureClasses(feature_type='Polygon') or []:
            result.append(os.path.join(ds, fc))
        arcpy.env.workspace = gdb
    arcpy.env.workspace = old_ws
    return result


wgs84 = arcpy.SpatialReference(4326)
features_out = []
oid = 1

fc_list = list_all_polygon_fcs(GDB)
print("Found {} polygon feature class(es): {}".format(len(fc_list), fc_list))

for fc in fc_list:
    base_name = os.path.basename(fc)
    if base_name in SKIP:
        print("Skipping " + base_name)
        continue

    fc_path = os.path.join(GDB, fc)
    dissolved = "memory\\diss_{}".format(oid)
    if arcpy.Exists(dissolved):
        arcpy.management.Delete(dissolved)

    try:
        arcpy.management.Dissolve(fc_path, dissolved)
    except arcpy.ExecuteError:
        print("Dissolve failed for {}: {}".format(base_name, arcpy.GetMessages(2)))
        continue

    if not arcpy.Exists(dissolved):
        print("Dissolve produced no output for {}, skipping".format(base_name))
        continue

    with arcpy.da.SearchCursor(dissolved, ['SHAPE@']) as cursor:
        for row in cursor:
            geom = row[0]
            geom84 = geom.projectAs(wgs84)
            centroid = geom84.centroid

            rings = []
            for part in geom84:
                ring = [[pnt.X, pnt.Y] for pnt in part if pnt]
                rings.append(ring)

            features_out.append({
                "attributes": {
                    "OBJECTID": oid,
                    "name_engli": clean_name(base_name),
                    "CENTER_LAT": centroid.Y,
                    "CENTER_LNG": centroid.X
                },
                "geometry": {"rings": rings}
            })
            oid += 1

    arcpy.management.Delete(dissolved)

output = {
    "displayFieldName": "",
    "fieldAliases": {
        "OBJECTID": "OBJECTID",
        "name_engli": "NAME_ENGLI",
        "CENTER_LAT": "CENTER_LAT",
        "CENTER_LNG": "CENTER_LNG"
    },
    "geometryType": "esriGeometryPolygon",
    "spatialReference": {"wkid": 4326, "latestWkid": 4326},
    "features": features_out
}

with open(OUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f)

print("Exported {} wadi boundarie(s) to {}".format(len(features_out), OUT_FILE))
