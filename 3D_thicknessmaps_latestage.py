
import arcpy
import os
from arcpy import env
from arcpy.sa import *
import sys

arcpy.CheckOutExtension("Spatial")

# Set environment settings
env.outputCoordinateSystem = arcpy.SpatialReference("NAD 1983 UTM Zone 13N")

arcpy.env.snapRaster = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\BASEMAP.gdb\z_snapraster'
arcpy.env.overwriteOutput = True
env.workspace = r'E:\DelawareBasin'


def main():
    ### 1. need to import/copy thickness rasters from final geodata model build folder
    ### 2. need to import/copy final elevation rasters from wherever they are into same folder
    ### 3. mask thickness rasters with final rasters using extract by mask
    ### 4. save result as isopach rasters

    units = ['alvb', 'udb', 'srt', 'ldb', 'dlb', 'uob', 'lob', 'artb']

    thickness_rasters =

    elev_rasters =

    for unitname, thras, elras in zip(units, thickness_rasters, elev_rasters):
        outExtractByMask = ExtractByMask(thras, elras)
        outExtractByMask.save('{}_isopach'.format(unitname))


if __name__ == '__main__':
    main()