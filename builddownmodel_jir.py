## written by marissa fichera, optimized by jake ross

import arcpy
import os
from arcpy import env
from arcpy.sa import *
import sys

# version number for output files
VERSION = 'v1000000'
# name your geodatabase where your files live and will be created
gdbname = 'qcoutputs_{}'.format(VERSION)

# arc environment settings
arcpy.CheckOutExtension("Spatial")
env.outputCoordinateSystem = arcpy.SpatialReference("NAD 1983 UTM Zone 13N")
arcpy.env.snapRaster = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\BASEMAP.gdb\z_snapraster'
arcpy.env.overwriteOutput = True

# setup config variables
## USER INPUT - WORKSPACE - WHERE LOCAL GDB WILL BE CREATED
CONFIG = {'ROOT': 'E:\DelawareBasin\DelawareBasin_geodata\workingdata'}
## USER INPUT - WORKSPACE - WHERE NETWORK GDB WILL BE CREATED (need to create this folder ahead of time)
CONFIG_FIN_V = {'ROOT': r'W:\regional\3d_delaware_basin\de_data\de_geodata\working_data\geosurfaces_v12_12082021'}


def set_default_workspace(name):
    env.workspace = make_gdb_name(name)


def make_network_gdb_name(name, create=True):
    basename = '{}.gdb'.format(name)
    name = os.path.join(CONFIG_FIN_V['ROOT'], basename)
    if create:
        # if does not exist create it
        if not arcpy.Exists(name):
            arcpy.CreateFileGDB_management(CONFIG_FIN_V['ROOT'], basename)
    return name


def make_gdb_name(name, create=True):
    basename = '{}.gdb'.format(name)
    name = os.path.join(CONFIG['ROOT'], basename)
    if create:
        # if does not exist create it
        if not arcpy.Exists(name):
            arcpy.CreateFileGDB_management(CONFIG['ROOT'], basename)
    return name


def copy_to_version_folder(versionrasters, extension):
    print('COPYING VERSIONS TO NETWORK VERSION FOLDER!! YOU ARE ALMOST THERE!!!')
    output_location = make_network_gdb_name('{}'.format(VERSION))

    version_names = ['landsurf', 'alvb', 'udb', 'srt', 'ldb', 'dlb',
                     'uob', 'lob', 'artb', 'capb']
    prefixes = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09']
    for surf, prefix, name in zip(versionrasters, prefixes, version_names):
        print('...copying', surf, 'to', output_location, '---- as ----',
              'M{}_{}_{}_{}'.format(prefix, name, extension, VERSION))
        name = r'{}\M{}_{}_{}_{}'.format(output_location, prefix, name, extension, VERSION)
        arcpy.CopyRaster_management(surf, name, '', '', '-3.402823e38',
                                    'NONE', 'NONE', '32_BIT_FLOAT', '', '')

    print('MISSION COMPLETE!!!!!!')


def mask_ras_with_geo_outcrop(inRasters, maskdata):
    print('BEGIN masking applicable rasters with geomask')
    for raster in inRasters:
        print('...masking', raster, 'with', maskdata)
        outExtractByMask = ExtractByMask(raster, maskdata)
        outExtractByMask.save(
            r'{}\step07_EXBYMASK_GEO_{}_discext_{}'.format(env.workspace, raster, VERSION))

    print('FINISHED masking applicable rasters with geomask')
    print('DONE')


def ebm_modelbound(rasters, extension, unitnames):
    print('BEGIN masking rasters to model boundary')
    # USER INPUT - STUDY BOUNDARY RASTER
    mask = 'dbasin_modelextras'
    print('Model boundary raster used for clipping = {}'.format(mask))
    inRasters = rasters
    exts_modelext = []

    for raster, unitname in zip(inRasters, unitnames):
        print('...masking', raster, 'with', mask, 'unitname ==== {}'.format(unitname))
        outExtractByMask = ExtractByMask(raster, mask)
        outExtractByMask.save(r'{}\step07_EXBYMASK_{}_{}_{}'.format(env.workspace, unitname, extension, VERSION))
        exts_modelext.append('step07_EXBYMASK_{}_{}_{}'.format(unitname, extension, VERSION))
        print('Masked {} with {} and output file = {}_{}'.format(raster, mask, unitname, extension))

    print('FINISHED masking {} extents with model ext bdry'.format(extension))
    return exts_modelext


def extract_by_mask(inRasters, maskdata, unitnames):
    print('BEGIN masking full extent rasters to discrete extent')
    inMaskData = maskdata
    inRasters = inRasters[1:]
    disc_exts = ['R00_land_resample']

    for raster, mask, unitname in zip(inRasters, inMaskData, unitnames[1:]):
        print('...masking', raster, 'with', mask, '= {}'.format(unitname))
        outExtractByMask = ExtractByMask(raster, mask)
        outExtractByMask.save(r'{}\step06_EXBYMASK_{}_discext_{}'.format(env.workspace, unitname, VERSION))
        disc_exts.append('step06_EXBYMASK_{}_discext_{}'.format(unitname, VERSION))
        print('...masked {} with {} ----- unitname = {}'.format(raster, mask, unitname))

    print('FINISHED masking full extent rasters to discrete extent')
    return disc_exts


def reclassify(rasters, unitnames):
    print('BEGIN reclassifying negative thickness values to NoData')
    reclassField = 'VALUE'
    inRasters = rasters
    remap = RemapRange([[-100000, 0, 'NoData']])

    reclass_rasters = []

    for ras, unitname in zip(inRasters, unitnames[1:]):
        print('...reclassifying', ras, '=', unitname)
        outReclass = Reclassify(ras, reclassField, remap)
        name = 'step05_RECLASSIFY_{}'.format(unitname)
        outReclass.save(name)
        reclass_rasters.append(name)
        print('Reclassified negative thickness values for {} = {}'.format(ras, unitname))

    maskdata = reclass_rasters
    print('FINISHED reclassifying negative thickness values to NoData')
    return maskdata


def minus(rasters, unitnames):
    print('BEGIN calculating full extent unit thicknesses')
    # set_default_workspace()

    output_rasters = []

    for upper_unit, lower_unit, unitname in zip(rasters, rasters[1:], unitnames[1:]):
        print('...calculating', upper_unit, 'minus', lower_unit)
        outMinus = Minus(upper_unit, lower_unit)
        name = 'step04_MINUS_{}_thickness'.format(unitname)
        outMinus.save(name)
        output_rasters.append(name)
        print('...calculated thickness of', lower_unit, '...should be same as...', unitname)

    thickness_ras = output_rasters
    print('FINISHED calculating full extent unit thicknesses')
    return thickness_ras


# def mosaic_min_ls(rasters, unitnames):
#     print('BEGIN mosaicking rasters with land surface to create fullext rasters snapped to land surface')
#     output_location = make_gdb_name('QCoutputs_v12_2_fullextents')
#     ls_mosaic_rasters = ['R00_land_resample']
#     landras = 'R00_land_resample'
#
#     for lower_unit, unitname in zip(rasters[1:], unitnames[1:]):
#         name = 'step03_MOSAIC_MIN02_LS_{}_fullextent'.format(unitname)
#
#         print('...mosaicking', landras, 'with', lower_unit, 'MINIMUM', 'name', name)
#
#         arcpy.MosaicToNewRaster_management('{};{}'.format(landras, lower_unit), output_location,
#                                            name, env.outputCoordinateSystem,
#                                            '32_BIT_FLOAT', '1000', '1', 'MINIMUM', '')
#         ls_mosaic_rasters.append(name)
#
#     # full extents of units underlying alluvium should be mosaicked with the alluvium base, not land surf
#
#     alvb_mosaic_rasters = ['R00_land_resample', 'step03_MOSAIC_MIN02_LS_R01_alvb_fullextent']
#
#     for lower_unit, unitname in zip(rasters[2:], unitnames[2:]):
#         alvb = 'step03_MOSAIC_MIN02_LS_R01_alvb_fullextent'
#         name = 'step03_MOSAIC_MIN02_alvb_{}_fullextent'.format(unitname)
#
#         print('...mosaicking', alvb, 'with', lower_unit, 'MINIMUM', 'name', name)
#
#         arcpy.MosaicToNewRaster_management('{};{}'.format(alvb, lower_unit), output_location,
#                                            name, env.outputCoordinateSystem,
#                                            '32_BIT_FLOAT', '1000', '1', 'MINIMUM', '')
#         alvb_mosaic_rasters.append(name)
#
#     print('FINISHED creating full extent rasters')
#     # fe_ras = ls_mosaic_rasters
#     fe_ras = alvb_mosaic_rasters
#     return fe_ras


def mosaic_min(rasters, unitnames):
    print('BEGIN mosaicking upper/lower surfaces and taking minimum')
    output_location = env.workspace
    fullext_rasters = ['R00_land_resample']

    # create alluvium base full extent:
    name_alv_fe = 'step02_MOSAIC_MIN01_UNITS_{}_fullextent'.format(unitnames[1])
    print('...mosaicking', rasters[0], 'with', rasters[1], 'MINIMUM', 'name', name_alv_fe)

    arcpy.MosaicToNewRaster_management('{};{}'.format(rasters[0], rasters[1]), output_location,
                                       name_alv_fe, env.outputCoordinateSystem,
                                       '32_BIT_FLOAT', '1000', '1', 'MINIMUM', '')

    fullext_rasters.append(name_alv_fe)

    i = 1
    for lower_ras, unitname in zip(rasters[2:], unitnames[2:]):
        # now mosaic output fullext_raster with underlying unit
        fe_upper_ras = fullext_rasters[i]

        name_fullext = 'step02_MOSAIC_MIN01_UNITS_{}_fullextent'.format(unitname)
        print('...mosaicking', fe_upper_ras, 'with', lower_ras, 'MINIMUM', 'out_name', name_fullext)

        arcpy.MosaicToNewRaster_management('{};{}'.format(fe_upper_ras, lower_ras), output_location,
                                           name_fullext, env.outputCoordinateSystem,
                                           '32_BIT_FLOAT', '1000', '1', 'MINIMUM', '')

        name = 'step02_MOSAIC_MIN01_UNITS_{}_fullextent'.format(unitname)


        fullext_rasters.append(name_fullext)
        i = i+1

    mosaic_ras = fullext_rasters
    print('FINISHED mosaicking upper/lower surfaces and taking minimum')
    return mosaic_ras


def resample(surfaces, size='1000', kind='NEAREST'):
    # USER INPUT CELL SIZE
    size_label = '{}x{}m'.format(size, size)
    print('BEGIN resampling rasters to {}'.format(size_label))
    set_default_workspace()

    resampled_rasters = ['{}_resample'.format(r) for r in surfaces]
    for surface, output in zip(surfaces, resampled_rasters):
        print('...resampling', surface)
        arcpy.Resample_management(surface, output, size, kind)

    res_ras = resampled_rasters
    print('FINISHED resampling rasters to {}'.format(size_label))
    return res_ras


def main():
    set_default_workspace(gdbname)

    ls_ras = 'R00_land'
    og_pva_base = 'R01_alvb'
    sr_top = 'R03_srt'
    udockum_base = 'R02_udb'
    ldockum_base = 'R04_ldb'
    dl_base = 'R05_dlb'
    uochoan_base = 'R06_uob'
    lochoan_base = 'R07_lob'
    artesia_base = 'R08_artb'
    # capitan_top = 'R09_capitantop'
    capitan_base = 'R09_capb'

    db_surfaces = [ls_ras, og_pva_base, udockum_base, sr_top, ldockum_base, dl_base, uochoan_base, lochoan_base,
                   artesia_base, capitan_base]

    res_ras = resample(db_surfaces)

    # mosaic_ras = mosaic_min(res_ras, db_surfaces)
    fe_ras = mosaic_min(res_ras, db_surfaces)

    # fe_ras = mosaic_min_ls(mosaic_ras, db_surfaces)

    thickness_ras = minus(fe_ras, db_surfaces)

    maskdata = reclassify(thickness_ras, db_surfaces)

    disc_exts = extract_by_mask(fe_ras, maskdata, db_surfaces)

    #### clips to model extent #####
    exts_modelext_full = ebm_modelbound(fe_ras, 'fullext', db_surfaces)
    exts_modelext_disc = ebm_modelbound(disc_exts, 'discext', db_surfaces)


    ########## copies to network ##############
    ########## NMBG specific and user input req'd ###########

    # type 'yes' as copy_command between the quotes if you want to copy to network
    # type 'no' between the quotes if you don't
    copy_command = 'no'
    if copy_command == 'yes':
        print('COPYING TO NETWORK FOLDER')
        copy_to_version_folder(exts_modelext_disc, 'discext')
        copy_to_version_folder(exts_modelext_full, 'fullext')
        print('COPIED TO NETWORK FOLDER')
    elif copy_command == 'no':
        print('DID NOT COPY TO NETWORK')
    else:
        print('variable that dictates whether or not these surfaces get copied is screwed up')


if __name__ == '__main__':
    main()
