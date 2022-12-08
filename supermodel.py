## written by marissa m. fichera

# Import system modules
import arcpy
from arcpy import env
from arcpy.sa import *
import os
import pandas as pd

# Set environment settings - USER SPECIFIC
arcpy.env.snapRaster = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\BASEMAP.gdb\z_snapraster'
arcpy.env.overwriteOutput = True
env.outputCoordinateSystem = arcpy.SpatialReference("NAD 1983 UTM Zone 13N")
arcpy.CheckOutExtension('Spatial')

working_geodb = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\working_geodb_and_folders_ex\working_geodb_example.gdb'
working_folder = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\working_geodb_and_folders_ex\working_folder_example'
env.workspace = working_folder
stepwise_output_folder = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\working_geodb_and_folders_ex\b001'

## USER INPUT - WORKSPACE - WHERE NETWORK GDB WILL BE CREATED (need to create this folder ahead of time)
CONFIG_FIN_V = {'ROOT': r'W:\statewide\aqua_map3D\am_references\MarsMapMethods\tutorial\example_network_output'}

v = '001'

def topo_to_raster(fc, i, elev_ID, unit):
    print(fc, i, elev_ID, unit)
    env.workspace = working_geodb

    # Set local variables
    inPointElevations = TopoPointElevation([[fc, '{}'.format(elev_ID)]])
    # inPointElevations = TopoPointElevation([[shapefile, '{}_elev'.format(unitname)]])
    # inBoundary = TopoBoundary([r'feature_classes\dbasin_bdry_buffer10km.shp'])
    # inContours = TopoContour([['contours.shp', 'spot_meter']])
    # inLake = TopoLake(['lakes.shp'])
    # inSinks = TopoSink([['sink1.shp', 'elevation'], ['sink2.shp', 'none']])
    # inStream = TopoStream(['streams.shp'])
    inCliff = TopoCliff(['cbp_f', 'gm_f'])
    # inCoast = TopoCoast(['coast.shp'])
    # inExclusion = TopoExclusion(['ignore.shp'])

    inFeatures = ([inPointElevations, inCliff])

    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")

    # Execute TopoToRaster
    # arcpy.env.extent = r'E:\BASEMAP\dbasin_spadtm_resamp_ft.tif'
    outTTR = TopoToRaster(inFeatures, "1000", Extent(485690, 3530089, 693190, 3627589), "20", "#", "#", "ENFORCE",
                          "SPOT",
                          "20", "#", "1", "0", "0", "200", '#', '#', 'ERROR_FILE{}.txt'.format(unit), '#', '#', '#',
                          'ERROR_PTS_{}'.format(unit))

    b001002r = r'{}\b001002r{}{}.tif'.format(stepwise_output_folder, unit, i)
    outTTR.save(b001002r)
    print(i, 't2r done')
    return b001002r

    # sys.exit('CHECK IF T2R WAS DONE CORRECTLY WITH CLIFF')
    # sys.exit('CHECK DIAGNOSTIC FILE')


def extract_vals_to_pts(fc, raster, i, unit):
    print('extracting values from', raster, 'to', fc)
    # Name: ExtractMultiValuesToPoints_Ex02.py
    # Description: Extracts the cells of multiple rasters as attributes in
    #    an output point feature class.  This example takes a multiband IMG
    #    and two GRID files as input.
    # Requirements: Spatial Analyst Extension
    env.workspace = working_geodb
    # Set local variables
    inPointFeatures = fc
    inRasterList = [[raster, 'ei{}'.format(i)]]

    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")

    # Execute ExtractValuesToPoints
    ExtractMultiValuesToPoints(inPointFeatures, inRasterList, 'NONE')

    print(i, 'extract multi values to pts done')


def calc_sigma(fc, i, elev_ID):
    arcpy.AddField_management(fc, "sigmae_{}".format(i), "DOUBLE")
    arcpy.CalculateField_management(fc, "sigmae_{}".format(i),
                                    'abs(!{}! - !ei{}!)'.format(elev_ID, i), "PYTHON")
    print(i, 'calculate sigma done')


def query_by_sigma(fc, i, unit):
    print('input file name = ', fc)
    table = fc
    out_table = 'b001003fc_{}_{}_result_table'.format(unit, i)
    in_key_field_option = 'USE_KEY_FIELDS'
    in_key_field = ''
    in_field = ''
    where_clause = 'sigmae_{} < 100'.format(i)

    in_features = arcpy.MakeQueryTable_management(table, out_table, in_key_field_option, in_key_field, in_field,
                                                  where_clause)
    out_shapefile = r'{}\b001003{}{}.shp'.format(working_folder, unit, i)
    out_feature_class = r'{}\b001003{}{}'.format(working_geodb, unit, i)
    arcpy.CopyFeatures_management(in_features, out_shapefile)
    arcpy.CopyFeatures_management(in_features, out_feature_class)

    print(i, 'query done and shapefile output')


def copy_master_to_working(unit):
    in_workspace = working_geodb
    arcpy.FeatureClassToFeatureClass_conversion('{}\{}_data_all_orig'.format(in_workspace, unit), in_workspace,
                                                '{}_data_all_working'.format(unit))

    working_fc = '{}_data_all_working'.format(unit)

    return working_fc


def copy_final(raster, unit):
    name = r'{}\b001002r{}.tif'.format(working_folder, unit)
    arcpy.CopyRaster_management(raster, name, 'TIFF', '', '-3.402823e38',
                                'NONE', 'NONE', '32_BIT_FLOAT', '', '')

    return name


def ebm_modelbound(rasters, n, unitnames):
    print('BEGIN masking rasters to model boundary')
    # USER INPUT - STUDY BOUNDARY RASTER
    mask = r'E:\3D_spatial_general\3d mapping areas\Delaware_Basin.shp'
    print('Model boundary raster or polygon used for clipping = {}'.format(mask))
    inRasters = rasters
    outRasters = []

    for raster, unitname in zip(inRasters, unitnames):
        print('...masking', raster, 'with', mask, 'unitname ==== {}'.format(unitname))
        outExtractByMask = ExtractByMask(raster, mask)
        name = r'b00200{}r{}.tif'.format(n, unitname)
        outExtractByMask.save(name)
        outRasters.append(name)
        print('Masked {} with {} and output file = {}'.format(raster, mask, name))

    print('FINISHED masking b00200{}r extents with model ext bdry'.format(n))
    return outRasters

def extract_by_mask(inRasters, maskdata, unitnames):
    print('BEGIN masking full extent rasters to discrete extent')
    print('inRasters = ', inRasters)
    print('inRasters[1:] = ', inRasters[1:])
    print('inRasters[0] = ', inRasters[0])
    inMaskData = maskdata
    disc_exts = ['{}'.format(inRasters[0])]
    inRasters = inRasters[1:]

    print('disc exts beginning = ', disc_exts)
    print('unitnames = ', unitnames)

    for raster, mask, unitname in zip(inRasters, inMaskData, unitnames[1:]):
        print('...masking', raster, 'with', mask, '= {}'.format(unitname))
        name = r'b002005r{}.tif'.format(unitname)
        outExtractByMask = ExtractByMask(raster, mask)
        outExtractByMask.save(name)
        disc_exts.append(name)
        print('disc_exts = ', disc_exts, 'after loop')
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
        print('...reclassifying', ras, '--- should end in --->', unitname)
        outReclass = Reclassify(ras, reclassField, remap)
        name = 'b002004r{}.tif'.format(unitname)
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
        name = 'b002003r{}.tif'.format(unitname)
        outMinus.save(name)
        output_rasters.append(name)
        print('...calculated thickness of', lower_unit, '...should be same as...', unitname)

    thickness_ras = output_rasters
    print('FINISHED calculating full extent unit thicknesses')
    return thickness_ras


def mosaic_min(rasters, unitnames):
    print('BEGIN mosaicking upper/lower surfaces and taking minimum')
    fullext_rasters = [rasters[0]]

    # create alluvium base full extent first:
    name_alv_fe = 'b002002r{}.tif'.format(unitnames[1])
    print('...mosaicking', rasters[0], 'with', rasters[1], 'MINIMUM', 'name', name_alv_fe)

    arcpy.MosaicToNewRaster_management('{};{}'.format(rasters[0], rasters[1]), working_folder,
                                       name_alv_fe, env.outputCoordinateSystem,
                                       '32_BIT_FLOAT', '1000', '1', 'MINIMUM', '')

    fullext_rasters.append(name_alv_fe)

    i = 1
    for lower_ras, unitname in zip(rasters[2:], unitnames[2:]):
        # now mosaic output fullext_raster with underlying unit
        fe_upper_ras = fullext_rasters[i]

        name_fullext = 'b002002r{}.tif'.format(unitname)
        print('...mosaicking', fe_upper_ras, 'with', lower_ras, 'MINIMUM', 'out_name', name_fullext)

        arcpy.MosaicToNewRaster_management('{};{}'.format(fe_upper_ras, lower_ras), working_folder,
                                           name_fullext, env.outputCoordinateSystem,
                                           '32_BIT_FLOAT', '1000', '1', 'MINIMUM', '')
        fullext_rasters.append(name_fullext)
        i = i+1

    mosaic_ras = fullext_rasters
    print('FINISHED mosaicking upper/lower surfaces and taking minimum')
    return mosaic_ras


def resample(surfaces, units, size='1000', kind='NEAREST'):
    # USER INPUT CELL SIZE
    size_label = '{}x{}m'.format(size, size)
    print('BEGIN resampling rasters to {}'.format(size_label))


    # resampled_rasters = ['{}_resample'.format(r) for r in surfaces]
    resampled_rasters = ['b002001r{}.tif'.format(u) for u in units]
    for surface, output in zip(surfaces, resampled_rasters):
        print('...resampling', surface)
        print('out name = ', output)
        arcpy.Resample_management(surface, output, size, kind)

    res_ras = resampled_rasters
    print('FINISHED resampling rasters to {}'.format(size_label))
    return res_ras


def place_final002_surfaces(rasters):
    outfolder002 = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\working_geodb_and_folders_ex\b002'
    outgdb002 = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\working_geodb_and_folders_ex\b002.gdb'

    for raster in rasters:
        print('raster = ', raster)
        name = r'{}\{}'.format(outfolder002, raster)
        print('output TIFF file = ', name)
        arcpy.CopyRaster_management(raster, name, '', '', '-3.402823e38', 'NONE', 'NONE',
                                    '32_BIT_FLOAT', '', '', 'TIFF', '')


        gdbname = r'{}\{}'.format(outgdb002, raster.replace('.tif', ''))
        print('output GRID file = ', gdbname)
        arcpy.CopyRaster_management(raster, gdbname, '', '', '-3.402823e38', 'NONE', 'NONE',
                                    '32_BIT_FLOAT', '', '', 'GRID', '')


def copy_to_network_folder(versionrasters):
    print('COPYING VERSIONS TO NETWORK VERSION FOLDER')

    output_location = r'{}'.format(CONFIG_FIN_V['ROOT'])
    if not os.path.exists(output_location):
        os.makedirs(output_location)

    for raster in versionrasters:
        print('...copying', raster, 'to', output_location, '---- as ----',
              '{}'.format(raster))
        name = r'{}\v{}{}'.format(output_location, v, raster)
        arcpy.CopyRaster_management(raster, name, '', '', '-3.402823e38',
                                    'NONE', 'NONE', '32_BIT_FLOAT', '', '')

    print('finished copying to network folder: {}'.format(output_location))


def make_network_gdb_name(name, create=True):
    basename = '{}.gdb'.format(name)
    name = os.path.join(CONFIG_FIN_V['ROOT'], basename)
    if create:
        # if does not exist create it
        if not arcpy.Exists(name):
            arcpy.CreateFileGDB_management(CONFIG_FIN_V['ROOT'], basename)
    return name


def export_fc_to_csv(fc, elevID, unit):
    print('EXPORTING attribute table to csv for {}'.format(fc))
    fields = ['OBJECTID', 'Field1', 'OriginalID', 'Easting', 'Northing', '{}'.format(elevID),
              'DataSource', 'ei4']
    out_path = r'C:\Users\mfichera\PycharmProjects\3D_mapping\db_methods\qcexports'
    out_csv = '{}_modelbuild_inputdata.csv'.format(unit)
    arcpy.ExportXYv_stats('{}'.format(fc), fields, 'COMMA', os.path.join(out_path, out_csv), 'ADD_FIELD_NAMES')
    print('EXPORTED attribute table to csv for {}'.format(unit))

    qc_csv = os.path.join(out_path, out_csv)

    return qc_csv


def uncert_topo_to_raster(name, n):
    # need to make n number of surfaces, where n = number of random sample text files generated in sample_percent

    for i in range(1, n+1):
        print('Running topo to raster on {}, {}'.format(name, i))
        fc = '{}_fc00{}.shp'.format(name, i)
        inPointElevations = TopoPointElevation([[fc, 'ei4']])
        inCliffs = TopoCliff(['cbp_f.shp', 'gm_f.shp'])
        inFeatures = ([inPointElevations, inCliffs])

        outTTR = TopoToRaster(inFeatures, "1000", Extent(485690, 3530089, 693190, 3627589), "20", "#", "#", "ENFORCE",
                          "SPOT", "20", "#", "1", "0", "0", "200", '#', '#', '#', '#', '#', '#', '#')

        outTTR.save(r'{}_t2r{}.tif'.format(name, i))
        print('t2r', '{}, {}'.format(name, i))
    print('t2r done')


def create_feature_class(name, n):
    for i in range(1, n+1):
        print('Creating feature class out of rand sample files: {}, {}'.format(name, i))
        table = '{}_rand00{}.csv'.format(name, i)
        X = 'Easting'
        Y = 'Northing'
        Z = 'ei4'
        out_layername = '{}_lyr00{}'.format(name, i)
        out_layer = os.path.join(working_folder, out_layername)
        arcpy.MakeXYEventLayer_management(table, X, Y, out_layer, env.outputCoordinateSystem, Z)

        fc_name = '{}_fc00{}'.format(name, i)
        arcpy.FeatureClassToFeatureClass_conversion(out_layer, working_folder, fc_name)
        print('fc', '{} {}'.format(name, i), 'created')
    print('{} all feature classes created'.format(name))


def sample_percent(df, unitname, n):
    # ei4 is the final point dataset used in making the final raster surface, so need to take a random 75% of
    # that dataset (500) times - store in 'output_random_sample_datasets'
    # out_path = r'C:\Users\mfichera\PycharmProjects\3D_mapping\db_methods\randsample_exports'
    out_path = working_folder

    for i in range(1, n+1):
        print('RANDOM SAMPLE {}: taking random sample of {} dataset'.format(i, unitname))
        rand_samp = df.sample(frac=.75)
        p = '{}_rand00{}.csv'.format(unitname, i)
        rand_samp.to_csv(os.path.join(out_path, p))
        print('random sample file taken {}, {}'.format(i, unitname))
    print('random sample files created')

    return out_path


def generate_uncertainty_maps(unitnames, n, masks):
    env.workspace = working_folder
    umaps = []
    for unit, mask in zip(unitnames[1:], masks[1:]):
        print('generating uncertainty map for unit {}'.format(unit))
        rasterList = arcpy.ListRasters('{}_t2r*'.format(unit), 'TIF')
        print('==== raster list =====')
        print(rasterList)
        print('...calculating standard deviation at each cell...')
        outSTD = CellStatistics(rasterList, 'STD', 'DATA')
        print('...calculating mean at each cell...')
        outMEAN = CellStatistics(rasterList, 'MEAN', 'DATA')

        print('...clipping to geologic extent...')
        outSTD_map = ExtractByMask(outSTD, mask)
        outMEAN_map = ExtractByMask(outMEAN, mask)

        print('...saving result...')
        nameSTD = '{}_stdev{}.tif'.format(unit, n)
        outSTD_map.save(nameSTD)
        nameMEAN = '{}_mean{}.tif'.format(unit, n)
        outMEAN_map.save(nameMEAN)

        print('...saving results to separate folder...')
        uncertainty_path = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\working_geodb_and_folders_ex\b004'
        if not os.path.exists(uncertainty_path):
            os.makedirs(uncertainty_path)
        outSTD_map.save('{}\{}'.format(uncertainty_path, nameSTD))
        outMEAN_map.save('{}\{}}'.format(uncertainty_path, nameMEAN))

        umaps.append(nameSTD)
        umaps.append(nameMEAN)

    return umaps

def main():
    # unitnames = ['alvb', 'udb', 'srt', 'ldb', 'dlb', 'uob', 'lob',
    #              'artb']
    # elevIDs = ['alv_b_elev', 'ud_b_elev', 'srtop_elev', 'ld_b_elev', 'rtop_elev', 'saltop_elev', 'lochoan_b_elev',
    #            'art_b_elev']
    unitnames = ['alvb', 'udb']
    elevIDs = ['alv_b_elev', 'ud_b_elev']

    QC_output_rasters = []
    QC_output_fcs = []
    QC_output_csvs = []

    for unit, elev_ID in zip(unitnames, elevIDs):
        b001001fc = copy_master_to_working(unit)

        temp_fcs = [b001001fc, 'b001003{}0'.format(unit), 'b001003{}1'.format(unit),
                    'b001003{}2'.format(unit), 'b001003{}3'.format(unit)]

        for i, fc in enumerate(temp_fcs):
            print(i, fc)
            b001002r = topo_to_raster(fc, i, elev_ID, unit)
            extract_vals_to_pts(fc, b001002r, i, unit)
            if i == 4:
                QC_out_r = copy_final(b001002r, unit)
                QC_output_rasters.append(QC_out_r)
                QC_output_fcs.append(fc)
                qc_csv = export_fc_to_csv(fc, elev_ID, unit)
                QC_output_csvs.append(qc_csv)
                print('{} QC process finished'.format(unit))
            else:
                calc_sigma(fc, i, elev_ID)
                query_by_sigma(fc, i, unit)

    print('DONE WITH QC FOR ALL UNITS')
    print('Raster surfaces going into model build = ', QC_output_rasters)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('~~~~~~~~~~~~~~~ BUILDING ~~~~~~~~~~~~~~~~~~~~')
    print('~~~~~~~~~~~~~~~~ MODEL ~~~~~~~~~~~~~~~~~~~~~~')
    print('~~~~~~~~~~~~~~~ STARTS ~~~~~~~~~~~~~~~~~~~~~~')
    print('~~~~~~~~~~~~~~~~~ NOW ~~~~~~~~~~~~~~~~~~~~~~')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')


    ## Step 02 - build down model
    b002_rasters = QC_output_rasters
    b002_rasters.insert(0, 'DEM.tif')
    unitnames.insert(0, 'DEM')

    env.workspace = working_folder
    print('unitnames ====== ', unitnames)
    res_ras = resample(b002_rasters, unitnames)
    print('==== RESAMPLED RASTERS ====')
    print(res_ras)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    fe_ras = mosaic_min(res_ras, unitnames)
    print('==== FULL EXT. RASTERS ====')
    print(fe_ras)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    thickness_ras = minus(fe_ras, unitnames)
    print('==== MINUS RASTERS ====')
    print(thickness_ras)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    maskdata = reclassify(thickness_ras, unitnames)
    print('==== MASK RASTERS ====')
    print(maskdata)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    disc_exts = extract_by_mask(fe_ras, maskdata, unitnames)
    print('==== DISCRETE EXTENT RASTERS ====')
    print(disc_exts)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    print('>>>>>>>>>>>>>> CLIPPING FULL AND DISCRETE EXTENT RASTERS TO MODEL EXTENT <<<<<<<<<<<<<<<<<<')
    #### clips to model extent #####
    print('>>>>>>>>>>>>>> FULL EXTENT <<<<<<<<<<<<<<<<<<')
    exts_modelext_full = ebm_modelbound(fe_ras[1:], '6', unitnames[1:])
    print('>>>>>>>>>>>>>> DISCRETE EXTENT <<<<<<<<<<<<<<<<<<')
    exts_modelext_disc = ebm_modelbound(disc_exts[1:], '7', unitnames[1:])
    print('>>>>>>>>>>>>>> ISOPACH MAPS <<<<<<<<<<<<<<<<<<')
    isopach_modelext = ebm_modelbound(maskdata, '8', unitnames[1:])
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    print('>>>>> placing final discrete extent, full extent, and isopach rasters in separate local folder and gdb <<<<<<<<<<')
    place_final002_surfaces(exts_modelext_disc)
    place_final002_surfaces(exts_modelext_full)
    place_final002_surfaces(isopach_modelext)

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ generating uncertainty datasets ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    n = 10
    for c, unit in zip(QC_output_csvs, unitnames[1:]):
        qcdata = pd.read_csv(c)
        df = pd.DataFrame(qcdata)

        sample_percent(df, unit, n)
        create_feature_class(unit, n)
        uncert_topo_to_raster(unit, n)

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ generating uncertainty maps ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    umaps = generate_uncertainty_maps(unitnames, n, exts_modelext_disc)


    ########## copies to network ##############
    ########## NMBG specific and user input req'd ###########

    # type 'yes' as copy_command between the quotes if you want to copy to network
    # type 'no' between the quotes if you don't
    copy_command = 'no'
    print('Do you want me to copy the final surfaces to the network? user says: ', copy_command)
    if copy_command == 'yes':
        print('okay - COPYING TO NETWORK FOLDER')
        copy_to_network_folder(exts_modelext_disc)
        copy_to_network_folder(exts_modelext_full)
        copy_to_network_folder(isopach_modelext)
        copy_to_network_folder(umaps)
        print('COPIED TO NETWORK FOLDER')
    elif copy_command == 'no':
        print('okay - DID NOT COPY TO NETWORK')
    else:
        print('error: please specify whether or not to copy to a network folder with yes or no')

if __name__ == '__main__':
    main()
