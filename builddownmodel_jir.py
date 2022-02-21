## written by marissa fichera, revised for efficiency by jake ross

import arcpy
import os
from arcpy import env
from arcpy.sa import *
import sys

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

def make_gdb_name(name, create=True):
    basename = '{}.gdb'.format(name)
    name = os.path.join(CONFIG['ROOT'], basename)
    if create:
        # if does not exist create it
        if not arcpy.Exists(name):
            arcpy.CreateFileGDB_management(CONFIG['ROOT'], basename)
    return name


def set_workspace(name_workspace):
    env.workspace = make_gdb_name(name_workspace)


def set_default_workspace():
    set_workspace('QCoutputs_v12_2_fullextents')

# Set environment settings
set_default_workspace()

env.outputCoordinateSystem = arcpy.SpatialReference("NAD 1983 UTM Zone 13N")

arcpy.env.snapRaster = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\BASEMAP.gdb\z_snapraster'
arcpy.env.overwriteOutput = True

def copy_to_version_folder(versionrasters, extension):
    print('COPYING VERSIONS TO NETWORK VERSION FOLDER!! YOU ARE ALMOST THERE!!!')
    output_location = make_network_gdb_name('v12_2')

    version_names = ['landsurf', 'alvb', 'udb', 'srt', 'ldb', 'dlb',
                     'uob', 'lob', 'artb', 'capb']
    prefixes = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09']
    for surf, prefix, name in zip(versionrasters, prefixes, version_names):
        print('...copying', surf, 'to', output_location, '---- as ----', 'M{}_{}_{}_v12_2'.format(prefix, name, extension))
        name = r'{}\M{}_{}_{}_v12_2'.format(output_location, prefix, name, extension)
        arcpy.CopyRaster_management(surf, name, '', '', '-3.402823e38',
                                    'NONE', 'NONE', '32_BIT_FLOAT', '', '')

    print('MISSION COMPLETE!!!!!!')


def mask_ras_with_geo_outcrop(inRasters, maskdata):
    print('BEGIN masking applicable rasters with geomask')
    for raster in inRasters:
        print('...masking', raster, 'with', maskdata)
        outExtractByMask = ExtractByMask(raster, maskdata)
        outExtractByMask.save(
            r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\QCoutputs_v12_2_fullextents.gdb\step07_EXBYMASK_GEO_{}_discext_v12_2'.format(
                raster))

    print('FINISHED masking applicable rasters with geomask')
    print('DONE')

def ebm_modelbound(rasters, extension, unitnames):
    print('BEGIN masking rasters to model boundary')
    mask = 'dbasin_modelextras'
    inRasters = rasters
    exts_modelext = []

    for raster, unitname in zip(inRasters, unitnames):
        print('...masking', raster, 'with', mask, 'unitname ==== {}'.format(unitname))
        outExtractByMask = ExtractByMask(raster, mask)
        outExtractByMask.save(
            r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\QCoutputs_v12_2_fullextents.gdb\step07_EXBYMASK_{}_{}_v12_2'.format(
                unitname, extension))
        exts_modelext.append('step07_EXBYMASK_{}_{}_v12_2'.format(unitname, extension))
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
        outExtractByMask.save(
            r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\QCoutputs_v12_2_fullextents.gdb\step06_EXBYMASK_{}_discext_v12_2'.format(
                unitname))
        disc_exts.append('step06_EXBYMASK_{}_discext_v12_2'.format(unitname))
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
    set_default_workspace()

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

def mosaic_min_ls(rasters, unitnames):
    print('BEGIN mosaicking rasters with land surface to create fullext rasters snapped to land surface')
    output_location = make_gdb_name('QCoutputs_v12_2_fullextents')
    ls_mosaic_rasters = ['R00_land_resample']
    landras = 'R00_land_resample'



    for lower_unit, unitname in zip(rasters[1:], unitnames[1:]):
        name = 'step03_MOSAIC_MIN02_LS_{}_fullextent'.format(unitname)

        print('...mosaicking', landras, 'with', lower_unit, 'MINIMUM', 'name', name)

        arcpy.MosaicToNewRaster_management('{};{}'.format(landras, lower_unit), output_location,
                                           name, env.outputCoordinateSystem,
                                           '32_BIT_FLOAT', '1000', '1', 'MINIMUM', '')
        ls_mosaic_rasters.append(name)

    # full extents of units underlying alluvium should be mosaicked with the alluvium base, not land surf

    alvb_mosaic_rasters = ['R00_land_resample', 'step03_MOSAIC_MIN02_LS_R01_alvb_fullextent']

    for lower_unit, unitname in zip(rasters[2:], unitnames[2:]):
        alvb = 'step03_MOSAIC_MIN02_LS_R01_alvb_fullextent'
        name = 'step03_MOSAIC_MIN02_alvb_{}_fullextent'.format(unitname)

        print('...mosaicking', alvb, 'with', lower_unit, 'MINIMUM', 'name', name)

        arcpy.MosaicToNewRaster_management('{};{}'.format(alvb, lower_unit), output_location,
                                           name, env.outputCoordinateSystem,
                                           '32_BIT_FLOAT', '1000', '1', 'MINIMUM', '')
        alvb_mosaic_rasters.append(name)

    print('FINISHED creating full extent rasters')
    # fe_ras = ls_mosaic_rasters
    fe_ras = alvb_mosaic_rasters
    return fe_ras


def mosaic_min(rasters, unitnames):
    print('BEGIN mosaicking upper/lower surfaces and taking minimum')
    output_location = make_gdb_name('QCoutputs_v12_2_fullextents')
    fullext_rasters = ['R00_land_resample']

    for upper_unit, lower_unit, unitname in zip(rasters, rasters[1:], unitnames[1:]):
        name = 'step02_MOSAIC_MIN01_UNITS_{}_fullextent'.format(unitname)

        print('...mosaicking', upper_unit, 'with', lower_unit, 'MINIMUM', 'name', name)

        arcpy.MosaicToNewRaster_management('{};{}'.format(upper_unit, lower_unit), output_location,
                                           name, env.outputCoordinateSystem,
                                           '32_BIT_FLOAT', '1000', '1', 'MINIMUM', '')
        # fullext_rasters.append(name)
        # second process mosaicking the mosaic of uochoan-lochoan min with cap base ##
        if upper_unit == rasters[6]:
            name2 = 'step02_MOSAIC_MIN01_lochoanbase_capbasemosaic'
            arcpy.MosaicToNewRaster_management('{};{}'.format(name, rasters[9]), output_location,
                                               name2, env.outputCoordinateSystem,
                                               '32_BIT_FLOAT', '1000', '1', 'LAST', '')
            fullext_rasters.append(name2)
        # second process mosaicking the mosaic of lochoan-artesia min with cap base ##
        elif upper_unit == rasters[7]:
            name2 = 'step02_MOSAIC_MIN01_artbase_capbasemosaic'
            arcpy.MosaicToNewRaster_management('{};{}'.format(name, rasters[9]), output_location,
                                               name2, env.outputCoordinateSystem,
                                               '32_BIT_FLOAT', '1000', '1', 'LAST', '')
            fullext_rasters.append(name2)
        else:
            fullext_rasters.append(name)


    mosaic_ras = fullext_rasters
    print('FINISHED mosaicking upper/lower surfaces and taking minimum')
    return mosaic_ras


def resample(surfaces, size='1000', kind='NEAREST'):
    size_label = '{}x{}m'.format(size,size)
    print('BEGIN resampling rasters to {}'.format(size_label))
    set_default_workspace()

    resampled_rasters = ['{}_resample'.format(r) for r in surfaces]
    for surface, output in zip(surfaces, resampled_rasters):
        print('...resampling', surface)
        arcpy.Resample_management(surface, output, size, kind)

    res_ras = resampled_rasters
    print('FINISHED resampling rasters to {}'.format(size_label))
    return res_ras


def mosaic_ctc(db_surfs, ps_surfs):
    print('BEGIN Mosaicking Pecos Slope surfaces to Del. Basin surfaces')
    output_location = make_gdb_name('QCoutputs_v12_2_fullextents')
    # db_ps_surfs = [[db_surfs, ps_surfs]]
    db_and_ps_ext_rasters = []
    labels = ['R01_alvbase', 'R02_udockum_base', 'R04_ldockum_base', 'R06_uochoan_base', 'R07_lochoan_base', 'R08_artesia_base']
    print('del basin surfs = ', db_surfs)
    print('ps surfs = ', ps_surfs)
    print('labels = ', labels)

    # sys.exit('look at the three lists above and see if that shit makes sense')

    for name, colin, mar in zip(labels, ps_surfs, db_surfs):
        print('...mosaicking', colin, 'with', mar, '...MEAN')
        arcpy.MosaicToNewRaster_management('{};{}'.format(colin, mar), output_location,
                                           '{}_dbpsextent'.format(name), env.outputCoordinateSystem,
                                           '32_BIT_FLOAT', '1000', '1', 'MEAN', '')
        db_and_ps_ext_rasters.append('{}_dbpsextent'.format(name))

    mos1 = db_and_ps_ext_rasters
    print('FINISHED Mosaicking Pecos Slope surfaces to Del. Basin surfaces')
    return mos1


def copy_raster():
    env.workspace = r'F:\NMBG\Pecos Slope\COLIN FINAL\__FINAL_MODEL\PecosSlope_3D_Rasters.gdb'
    colinsurfs = ['R03_Ogallala_basediscext', 'R07_UDockum_basediscext', 'R08_LDockum_basediscext',
                  'R09_UOchoan_basediscext', 'R10_LOchoan_basediscext', 'R11_Artesia_basediscext']
    # output_location = r'E:\Delaware Basin\DelawareBasin_geodata\workingdata\QCoutputs_v3.gdb'
    output_location = make_gdb_name('QCoutputs_v12_2_fullextents')
    colincopies = []

    for surf in colinsurfs:
        name = r'{}\{}_ctc_copy_float'.format(output_location, surf)
        arcpy.CopyRaster_management(surf, name, '', '', '-3.402823e38',
                                    'NONE', 'NONE', '32_BIT_FLOAT', '', '')
        colincopies.append(name)

    if colincopies:
        ps_surfs = colincopies
    else:
        ps_surfs = colinsurfs

    return ps_surfs


def mask_v12_rasters():
    env.workspace = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\v12_2_finalmasking.gdb'
    v12_masks = ['alvb', 'udb', 'srt', 'ldb', 'dlb', 'uob', 'lob', 'artb']
    v12_old = ['alvbase', 'udockumbase', 'srtop', 'ldockumbase', 'deweylakebase', 'uochoanbase', 'lochoanbase', 'artesiabase']

    i = 1
    for masksurf, raster in zip(v12_masks, v12_old):
        mask = 'step07_EXBYMASK_R0{}_{}_discext_v12_2'.format(i, masksurf)
        ras = 'M0{}_{}_discext_v12'.format(i, raster)
        outExtractByMask = ExtractByMask(ras, mask)
        outExtractByMask.save(
            r'{}\M0{}_{}_discext_v12_2'.format(env.workspace, i, masksurf))
        i = i+1
        # disc_exts.append('step06_EXBYMASK_{}_discext_v12_2'.format(unitname))


def main():
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

    mosaic_ras = mosaic_min(res_ras, db_surfaces)

    fe_ras = mosaic_min_ls(mosaic_ras, db_surfaces)

    thickness_ras = minus(fe_ras, db_surfaces)

    # maskdata = reclassify(thickness_ras, db_surfaces)

    # disc_exts = extract_by_mask(fe_ras, maskdata, db_surfaces)


    #### clips to model extent #####
    exts_modelext_full = ebm_modelbound(fe_ras, 'fullext', db_surfaces)
    # exts_modelext_disc = ebm_modelbound(disc_exts, 'discext', db_surfaces)

    ########### when finished with version, run this as standalone!! #########
    ########## copies to network ##############

    copy_command = 'yes'
    if copy_command == 'yes':
        print('COPYING TO NETWORK FOLDER')
        # copy_to_version_folder(exts_modelext_disc, 'discext')
        copy_to_version_folder(exts_modelext_full, 'fullext')
        print('COPIED TO NETWORK FOLDER')
    elif copy_command == 'no':
        print('DID NOT COPY TO NETWORK')
    else:
        print('variable that dictates whether or not these surfaces get copied is screwed up')

    # mask_v12_rasters()

if __name__ == '__main__':
    main()
