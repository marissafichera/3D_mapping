# written by marissa m. fichera

import os
import re
import numpy as np
from numpy import array, dstack
import pandas as pd
import arcpy
from arcpy import env
from arcpy.sa import *

env.workspace = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\output_error_surfs'
env.outputCoordinateSystem = arcpy.SpatialReference("NAD 1983 UTM Zone 13N")
arcpy.env.snapRaster = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\BASEMAP.gdb\z_snapraster'
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

# setup config variables
## USER INPUT - WORKSPACE - WHERE LOCAL GDB WILL BE CREATED
CONFIG = {'ROOT': 'E:\DelawareBasin\DelawareBasin_geodata\workingdata'}
## USER INPUT - WORKSPACE - WHERE NETWORK GDB WILL BE CREATED (need to create this folder ahead of time)
CONFIG_FIN_V = {'ROOT': r'W:\regional\3d_delaware_basin\de_data\de_geodata\working_data\geosurfaces_v12_12082021'}

def make_network_gdb_name(name, create=True):
    basename = '{}.gdb'.format(name)
    name = os.path.join(CONFIG_FIN_V['ROOT'], basename)
    if create:
        # if does not exist create it
        if not arcpy.Exists(name):
            arcpy.CreateFileGDB_management(CONFIG_FIN_V['ROOT'], basename)
    return name

def copy_version_to_final_resting_place(rasters):
    print('COPYING VERSIONS TO NETWORK VERSION FOLDER!! YOU ARE ALMOST THERE!!!')
    output_location = make_network_gdb_name('geosurfaces_v11_10082021')

    version_names = ['alvbase', 'udockumbase', 'srtop', 'ldockumbase', 'deweylakebase',
                     'uochoanbase', 'lochoanbase', 'artesiabase']
    prefixes = ['01', '02', '03', '04', '05', '06', '07', '08']

    for raster, prefix, name in zip(rasters, prefixes, version_names):
        in_raster = 'SetNullOutput32fl_{}'.format(raster)
        print('...copying', in_raster, 'to', output_location, '---- as ----',
              'M{}_{}_discext_v10'.format(prefix, name))
        network_name = r'{}\M{}_{}_discext_v11'.format(output_location, prefix, name)
        arcpy.CopyRaster_management(in_raster, network_name, '', '', '-3.402823e38',
                                    'NONE', 'NONE', '32_BIT_FLOAT', '', '')

        personal_loc = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\FINAL_DelBasinGeoSurfaces_discexts.gdb'
        personal_loc_name = r'{}\M{}_{}_discext_v11'.format(personal_loc, prefix, name)
        arcpy.CopyRaster_management(in_raster, personal_loc_name, '', '', '-3.402823e38',
                                    'NONE', 'NONE', '32_BIT_FLOAT', '', '')


    print('MISSION COMPLETE!')


def copy_to_featureclass(units):
    env.workspace = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\output_error_surfs'
    ROOT = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\output_error_surfs'
    # errorsurfs = ['std_{}_1000.tif', 'std_srb_1000.tif', 'std_ldb_1000.tif', 'std_dlb_1000.tif', 'std_uochoanb_1000.tif',
    #               'std_lochoanb_1000.tif', 'std_artb_1000.tif']
    # units = ['udb', 'srtop', 'ldb', 'dlb', 'uochoanb', 'lochoanb', 'artb']

    uncert_fes = []
    for unit in units:
    # for surf, unit in zip(errorsurfs, units):
        errorsurf = 'std_{}_1000.tif'.format(unit)
        out_loc = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\uncertainty_maps.gdb'
        out_name = 'uncertainty_fullextent_{}'.format(unit)
        arcpy.CopyRaster_management(errorsurf, os.path.join(out_loc, out_name), '', '', '-3.402823e38',
                                    'NONE', 'NONE', '32_BIT_FLOAT', '', '')
        uncert_fes.append(os.path.join(out_loc, out_name))

    return uncert_fes

def extract_to_discrete_extents(errorsurfs, units):
    mask_model = 'dbasin_modelext'
    suffix = '_discext_v12'
    mask_surfs = ['M01_alvbase{}'.format(suffix), 'M02_udockumbase{}'.format(suffix), 'M03_srtop{}'.format(suffix), 'M04_ldockumbase{}'.format(suffix),
                  'M05_deweylakebase{}'.format(suffix), 'M06_uochoanbase{}'.format(suffix), 'M07_lochoanbase{}'.format(suffix),
                  'M08_artesiabase{}'.format(suffix)]
    # mask_surfs = ['M01_alvbase{}'.format(suffix)]
    uncert_discexts = []

    for surf, mask, unit in zip(errorsurfs, mask_surfs, units):
        error_discext = ExtractByMask(surf, mask)
        error_discext.save('uncertainty_discext_{}'.format(unit))
        uncert_discexts.append(error_discext)

    uncert_disc_modelexts = []
    for surf_disc, unit in zip(uncert_discexts, units):
        error_discext_modelext = ExtractByMask(surf_disc, mask_model)
        error_discext_modelext.save('uncertainty_disc_modelext_{}'.format(unit))
        uncert_disc_modelexts.append(error_discext_modelext)

# def clip_to_model_extent(errorsurfs, units):
#     mask = 'dbasin_modelext'
#
#     for surf, unit in zip(errorsurfs, units):
#         error_discext = ExtractByMask(surf, mask)
#         error_discext.save('uncertainty_discext_{}'.format(unit))


def main():
    errorsurfs = ['std_udb_1000.tif', 'std_srb_1000.tif', 'std_ldb_1000.tif', 'std_dlb_1000.tif', 'std_uochoanb_1000.tif',
                  'std_lochoanb_1000.tif', 'std_artb_1000.tif']
    units = ['alvb', 'udb', 'srt', 'ldb', 'dlb', 'uob', 'lob', 'artb']

    uncert_fes = copy_to_featureclass(units)

    env.workspace = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\uncertainty_maps.gdb'
    extract_to_discrete_extents(uncert_fes, units)


if __name__ == '__main__':
    main()