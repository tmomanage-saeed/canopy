"""
Run this inside ArcGIS Pro's Python window.

Exports everything needed for the Large Park section of the dashboard from
plantable.gdb:

  1. Projects_Boundaries -> LargePark_boundary.json (one combined Esri-JSON
     file, same format as Projects_boundry.json / Wadis_boundary.json)
  2. Additional_Trees_Canopy, Current_Canopy, Mature_Canopy, Plantable_Area
     -> split per park into GeoJSON files in the SAME folders roads/wadis
     already use (additional_trees_data/, canopy_current_data/,
     canopy_mature_data/, plantable_data/), named "<ParkName>.geojson" --
     real polygon shapes, unchanged. (Roads' additional_trees_data is also
     real polygons -- thousands of small per-tree canopy circles -- not
     points, so Large Park's single aggregate polygon per park is exported
     the same way rather than collapsed into a point.)
  3. Tree_species -> split per park into species_data/"<ParkName>.geojson"

Park names come straight from the GDB's ProjectNam field (Ar-Rimal2,
Al-Aziziyah, Taweeq3, Al-Arid2, Bader) -- these already match the names
used in KPI PARKS GR.xlsx exactly, so no renaming is needed this time.

Fix vs. earlier versions of this script: geometry conversion now uses arcpy's
own __geo_interface__ property instead of manually walking parts/points and
splitting on None separators. The hand-rolled version had a bug that produced
degenerate 2-point (zero-area) rings for some features -- valid GeoJSON type
("Polygon"/"MultiPolygon") but with no real shape, which is why Additional
Trees rendered as a tiny point instead of a visible shape even though the
data wasn't literally GeoJSON "Point" type.
"""
import arcpy, json, os

GDB = r"C:\Users\saeed\Documents\ArcGIS\Projects\plantable\plantable.gdb"
OUT_DIR = r"C:\Users\saeed\Downloads\Aa_Canopy"

wgs84 = arcpy.SpatialReference(4326)


def densify_if_curved(geom):
    """Some features (e.g. circular tree-canopy buffers) are stored as true
    curves -- a full circle can be just 2 control points plus curve metadata.
    GeoJSON has no curve support, and naive conversion (even via arcpy's own
    __geo_interface__) only grabs those 2 control points, producing a
    degenerate zero-area "ring" instead of the real circle. Densify replaces
    the curve with closely-spaced straight segments that approximate it, in
    the geometry's original (projected, metres) units -- do this BEFORE
    reprojecting to WGS84."""
    if getattr(geom, 'hasCurves', False):
        return geom.densify("DISTANCE", 0.5, 0)
    return geom


def polygon_to_geojson_geometry(geom84):
    """Convert an arcpy Polygon geometry (already reprojected to WGS84) into
    correct GeoJSON Polygon/MultiPolygon coordinates. Uses arcpy's own
    __geo_interface__ (Esri-maintained, spec-correct) instead of manually
    walking parts/points -- a hand-rolled version of this produced degenerate
    2-point rings for some layers, which is what was rendering as "points"
    instead of real shapes."""
    return dict(geom84.__geo_interface__)


def polygon_to_esri_rings(geom84):
    """Flatten a geometry's rings into the Esri-JSON 'rings' shape used by
    LargePark_boundary.json (matches Projects_boundry.json / Wadis_boundary.json),
    via the same reliable __geo_interface__ conversion."""
    gi = geom84.__geo_interface__
    if gi['type'] == 'Polygon':
        return [list(ring) for ring in gi['coordinates']]
    if gi['type'] == 'MultiPolygon':
        rings = []
        for poly in gi['coordinates']:
            for ring in poly:
                rings.append(list(ring))
        return rings
    return []


def export_boundaries():
    print("Exporting Projects_Boundaries -> LargePark_boundary.json")
    fields = ["SHAPE@", "ProjectNam", "NAME_ENGLI"]
    features_out = []
    oid = 1
    with arcpy.da.SearchCursor(os.path.join(GDB, "Projects_Boundaries"), fields) as cursor:
        for geom, project_nam, name_engli in cursor:
            geom = densify_if_curved(geom)
            geom84 = geom.projectAs(wgs84)
            centroid = geom84.centroid
            rings = polygon_to_esri_rings(geom84)
            name = project_nam or name_engli
            features_out.append({
                "attributes": {
                    "OBJECTID": oid,
                    "name_engli": name,
                    "CENTER_LAT": centroid.Y,
                    "CENTER_LNG": centroid.X
                },
                "geometry": {"rings": rings}
            })
            oid += 1

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
    out_path = os.path.join(OUT_DIR, "LargePark_boundary.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f)
    print("  Wrote {} parks to {}".format(len(features_out), out_path))


def export_polygon_layer(fc_name, name_field, out_folder):
    print("Exporting {} -> {}/<Park>.geojson".format(fc_name, out_folder))
    out_dir = os.path.join(OUT_DIR, out_folder)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    fields = ["SHAPE@", name_field]
    by_park = {}
    with arcpy.da.SearchCursor(os.path.join(GDB, fc_name), fields) as cursor:
        for geom, park_name in cursor:
            if not park_name:
                continue
            geom = densify_if_curved(geom)
            geom84 = geom.projectAs(wgs84)
            geometry = polygon_to_geojson_geometry(geom84)
            feature = {
                "type": "Feature",
                "properties": {},
                "geometry": geometry
            }
            by_park.setdefault(park_name, []).append(feature)

    for park_name, feats in by_park.items():
        geojson = {"type": "FeatureCollection", "features": feats}
        out_path = os.path.join(out_dir, park_name + ".geojson")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f)
        print("  {}: {} feature(s) -> {}".format(park_name, len(feats), out_path))


def export_species():
    print("Exporting Tree_species -> species_data/<Park>.geojson")
    out_dir = os.path.join(OUT_DIR, "species_data")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    fields = ["SHAPE@XY", "ProjectNam", "Species"]
    by_park = {}
    with arcpy.da.SearchCursor(os.path.join(GDB, "Tree_species"), fields,
                                spatial_reference=wgs84) as cursor:
        for (x, y), park_name, species in cursor:
            if not park_name:
                continue
            feature = {
                "type": "Feature",
                "properties": {"species": species or "Unknown"},
                "geometry": {"type": "Point", "coordinates": [x, y]}
            }
            by_park.setdefault(park_name, []).append(feature)

    for park_name, feats in by_park.items():
        geojson = {"type": "FeatureCollection", "features": feats}
        out_path = os.path.join(out_dir, park_name + ".geojson")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f)
        print("  {}: {} tree(s) -> {}".format(park_name, len(feats), out_path))


export_boundaries()
export_polygon_layer("Additional_Trees_Canopy", "ProjectNam", "additional_trees_data")
export_polygon_layer("Current_Canopy", "ProjectNam", "canopy_current_data")
export_polygon_layer("Mature_Canopy", "ProjectNam", "canopy_mature_data")
export_polygon_layer("Plantable_Area", "ProjectNam_1", "plantable_data")
export_species()
print("Done.")
