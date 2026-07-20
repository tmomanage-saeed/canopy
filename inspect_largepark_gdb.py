"""
Run this inside ArcGIS Pro's Python window.

Just INSPECTS plantable.gdb's 6 feature classes -- prints field names,
geometry type, and feature count for each, plus a couple of sample rows.
No files are written. This is so we can see the real schema before writing
the actual export script (same careful approach used for the wadi boundaries).
"""
import arcpy

GDB = r"C:\Users\saeed\Documents\ArcGIS\Projects\plantable\plantable.gdb"

FEATURE_CLASSES = [
    "Additional_Trees_Canopy",
    "Current_Canopy",
    "Mature_Canopy",
    "Plantable_Area",
    "Projects_Boundaries",
    "Tree_species",
]

arcpy.env.workspace = GDB

for fc in FEATURE_CLASSES:
    print("=" * 60)
    print(fc)
    try:
        desc = arcpy.Describe(fc)
        print("  Shape type:", desc.shapeType)
        count = int(arcpy.management.GetCount(fc)[0])
        print("  Feature count:", count)
        fields = [f.name for f in arcpy.ListFields(fc)]
        print("  Fields:", fields)

        # Print up to 3 sample rows (attributes only, no geometry)
        with arcpy.da.SearchCursor(fc, fields) as cursor:
            for i, row in enumerate(cursor):
                if i >= 3:
                    break
                print("  Sample row:", dict(zip(fields, row)))
    except Exception as e:
        print("  ERROR:", e)

print("=" * 60)
print("Done.")
