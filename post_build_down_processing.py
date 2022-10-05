import os
import re
import numpy as np
from numpy import array, dstack
import pandas as pd
import arcpy
from arcpy import env
from arcpy.sa import *

env.workspace = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\v12_finalprocessing.gdb'
env.outputCoordinateSystem = arcpy.SpatialReference("NAD 1983 UTM Zone 13N")
arcpy.env.snapRaster = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\BASEMAP.gdb\z_snapraster'
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

# setup my config variables
CONFIG = {'ROOT': 'E:\DelawareBasin\DelawareBasin_geodata\workingdata'}
CONFIG_FIN_V = {'ROOT': r'W:\regional\3d_delaware_basin\de_data\de_geodata\working_data\geosurfaces_v12_12082021'}

def make_network_gdb_name(name, create=True):
    basename = '{}.gdb'.format(name)
    name = os.path.join(CONFIG_FIN_V['ROOT'], basename)
    if create:
        # if does not exist create it
        if not arcpy.Exists(name):
            arcpy.CreateFileGDB_management(CONFIG_FIN_V['ROOT'], basename)
    return name

def copy_raster(rasters):
    int_rasters = []

    for raster in rasters:
        name = r'INT{}'.format(raster)
        arcpy.CopyRaster_management(raster, name, '', '', '-2147483648',
                                    'NONE', 'NONE', '32_BIT_SIGNED', '', '')
        int_rasters.append(name)


def reclassify(rasters):
    print('BEGIN reclassifying all values to 1')
    reclassField = 'VALUE'
    # inRasters = rasters
    remap = RemapRange([[-100000, 100000, 1]])

    reclass_rasters = []

    for ras in rasters:
        in_name = r'INT{}'.format(ras)
        print('...reclassifying', in_name)
        outReclass = Reclassify(in_name, reclassField, remap)
        name = 'RECLASSIFY_{}'.format(in_name)
        outReclass.save(name)
        reclass_rasters.append(name)

    return reclass_rasters


def region_group(rasters):
    print('begin region group analysis')

    for raster in rasters:
        out_name = 'RG_{}'.format(raster)
        outRegionGrp = RegionGroup(raster, 'FOUR', 'WITHIN', '', '')
        outRegionGrp.save(out_name)
        print('RG done, output as {}'.format(out_name))

        inRasForClip = out_name
        maskdata = r'E:\3D_spatial_general\3d mapping areas\Delaware_Basin.shp'
        outExtractByMask = ExtractByMask(inRasForClip, maskdata)
        out_clipped_raster = 'ModelExtRG_{}'.format(raster)
        outExtractByMask.save(out_clipped_raster)
        print('Clipped to Model Extent -- {}'.format(out_clipped_raster))


def set_null(rasters_32float):
    # cutoff values for different formations
    # santa rosa not included because it's bueno
    print('begin removing rogue pixels from rasters')

    alv_co = 25
    art_cap_co = 145
    dl_co = 60
    ldock_co = 100
    lochoan_cap_co = 25
    udock_co = 10
    uochoan_co = 140
    sr_co = 1

    cutoffs = [alv_co, udock_co, sr_co, ldock_co, dl_co, uochoan_co, lochoan_cap_co, art_cap_co]

    for raster32, coval in zip(rasters_32float, cutoffs):
        RGraster = 'ModelExtRG_RECLASSIFY_INT{}'.format(raster32)
        out_name = 'SetNullOutput32fl_{}'.format(raster32)
        outSetNull = SetNull(RGraster, raster32, 'COUNT < {}'.format(coval))
        outSetNull.save(out_name)
        print('Removed rogue pixel values from {}, output as {}'.format(RGraster, out_name))


def copy_version_to_final_resting_place(rasters):

    print('COPYING VERSIONS TO NETWORK VERSION FOLDER!! YOU ARE ALMOST THERE!!!')
    output_location = make_network_gdb_name('geosurfaces_v12_12082021')

    version_names = ['alvbase', 'udockumbase', 'srtop', 'ldockumbase', 'deweylakebase',
                     'uochoanbase', 'lochoanbase', 'artesiabase']
    prefixes = ['01', '02', '03', '04', '05', '06', '07', '08']

    for raster, prefix, name in zip(rasters, prefixes, version_names):
        in_raster = 'SetNullOutput32fl_{}'.format(raster)
        print('...copying', in_raster, 'to', output_location, '---- as ----',
              'M{}_{}_discext_v12'.format(prefix, name))
        network_name = r'{}\M{}_{}_discext_v12'.format(output_location, prefix, name)
        arcpy.CopyRaster_management(in_raster, network_name, '', '', '-3.402823e38',
                                    'NONE', 'NONE', '32_BIT_FLOAT', '', '')

        personal_loc = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\FINAL_DelBasinGeoSurfaces_discexts.gdb'
        personal_loc_name = r'{}\M{}_{}_discext_v12'.format(personal_loc, prefix, name)
        arcpy.CopyRaster_management(in_raster, personal_loc_name, '', '', '-3.402823e38',
                                    'NONE', 'NONE', '32_BIT_FLOAT', '', '')


    print('MISSION COMPLETE!')


def mask_alluvium(alv):
    maskdata = 'kelley_alv_top'
    out_name = 'm{}'.format(alv)
    outExtractByMask = ExtractByMask(alv, maskdata)
    outExtractByMask.save(out_name)
    print('masked alluvium to top extent, output -- {}'.format(out_name))

def main():
    ext = '_discext_v12'
    # mask_alluvium('R01_alvb{}'.format(ext))

    rasters = ['mR01_alvb{}'.format(ext), 'R02_udb{}'.format(ext), 'R03_srt{}'.format(ext), 'R04_ldb{}'.format(ext),
               'R05_dlb{}'.format(ext), 'R06_uob{}'.format(ext), 'R07_lob{}'.format(ext), 'R08_artb{}'.format(ext)]

    # # copy the rasters to integer type
    # copy_raster(rasters)
    #
    # # reclassify to all same value
    # reclass_rasters = reclassify(rasters)
    #
    # # perform region group analysis
    # region_group(reclass_rasters)
    # print('CONFIGURE COUNT CUTOFFS BEFORE PROCEEDING')

    # set cutoff from COUNTs (configured by hand) as true, return original 32float raster if false
    # set_null(rasters)
    #
    copy_version_to_final_resting_place(rasters)

if __name__ == '__main__':
    main()