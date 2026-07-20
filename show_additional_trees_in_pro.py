"""
Run this inside ArcGIS Pro's Python window, with a map view open in the
current project.

Adds Additional_Trees_Canopy straight from plantable.gdb to the active map
(so you can see with your own eyes, in ArcGIS Pro itself, exactly what this
layer's shapes look like), and prints per-feature diagnostics: how many
disjoint parts each park's feature has, and its bounding box size, so we can
tell whether it's genuinely lots of small scattered patches (which would
LOOK like dots even though it's real polygon data) or something is actually
wrong.
"""
import arcpy

GDB = r"C:\Users\saeed\Documents\ArcGIS\Projects\plantable\plantable.gdb"
FC = "Additional_Trees_Canopy"

# 1. Add the layer to the current map so you can look at it directly in Pro.
aprx = arcpy.mp.ArcGISProject("CURRENT")
m = aprx.activeMap
if m is None:
    print("No active map open -- open a map view in ArcGIS Pro first, then rerun.")
else:
    lyr = m.addDataFromPath(GDB + "\\" + FC)
    print("Added layer '{}' to map '{}'. Look at it in the map view now.".format(lyr.name, m.name))

# 2. Print diagnostics per feature.
fields = ["OID@", "SHAPE@", "ProjectNam"]
with arcpy.da.SearchCursor(FC, fields) as cursor:
    for oid, geom, park_name in cursor:
        num_parts = geom.partCount
        extent = geom.extent
        width_m = extent.width
        height_m = extent.height
        print("OID {} ({}): parts={}, area={:.2f} m2, bbox={:.1f} x {:.1f} m".format(
            oid, park_name, num_parts, geom.area, width_m, height_m))
