"""
Run this inside ArcGIS Pro's Python window.

Just lists every ProjectNam value found in Projects_Boundaries (all 5 parks),
so we can build a correct name-mapping to the Excel display names.
"""
import arcpy

GDB = r"C:\Users\saeed\Documents\ArcGIS\Projects\plantable\plantable.gdb"
arcpy.env.workspace = GDB

with arcpy.da.SearchCursor("Projects_Boundaries", ["ProjectNam", "NAME_ENGLI", "GR_PROJECT"]) as cursor:
    for row in cursor:
        print(row)
