import arcpy
from arcpy import env

# where all the feature classes are located
env.workspace = r'E:\map_packages\DelawareBasinGeology.gdb'

def main():
    # put path + name of feature class with metadata you want to copy here, example: E:\map_packages\DelawareBasinGeology.gdb\alvb_contour_100ft
    sourceMD = ''

    for fc in arcpy.ListFeatureClasses():
        arcpy.MetadataImporter_conversion(sourceMD, fc)
        print('Done importing metadata to {}'.format(fc))
    print('Done importing metadata to all feature classes')


if __name__ == '__main__':
    main()
