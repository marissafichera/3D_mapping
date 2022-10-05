## written by marissa m. fichera

# Import system modules
import arcpy
from arcpy import env
from arcpy.sa import *

# Set environment settings - USER SPECIFIC
# env.workspace = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\dbasin_geodata_originals.gdb'
env.workspace = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\dbasin_geodata_originals5_deccheck.gdb'
arcpy.env.snapRaster = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\BASEMAP.gdb\z_snapraster'
arcpy.env.overwriteOutput = True

# GEOLOGIC MODEL SPECIFIC
unitnames = ['alv_base', 'udockum_base', 'sr_top', 'ldockum_base', 'deweylake_base', 'uochoan_base', 'lochoan_base',
             'artesia_base']


def topo_to_raster(shapefile, i, elev_ID, unit):
    print(shapefile, i, elev_ID, unit)
    ps_units = ['udockum_base_pecos', 'ldockum_base_pecos', 'uochoan_base_pecos', 'lochoan_base_pecos']
    db_units = ['udockum_base', 'ldockum_base', 'uochoan_base', 'lochoan_base']

    # Set local variables
    inPointElevations = TopoPointElevation([[shapefile, '{}'.format(elev_ID)]])
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

    outTTR.save(r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\dbasin_t2r2_dec2021\t2r{}{}.tif'.format(unit, i))
    print(i, 't2r done')
    # sys.exit('CHECK IF T2R WAS DONE CORRECTLY WITH CLIFF')
    # sys.exit('CHECK DIAGNOSTIC FILE')


def extract_vals_to_pts(shapefile, raster, i):
    # Name: ExtractMultiValuesToPoints_Ex_02.py
    # Description: Extracts the cells of multiple rasters as attributes in
    #    an output point feature class.  This example takes a multiband IMG
    #    and two GRID files as input.
    # Requirements: Spatial Analyst Extension

    # Set local variables
    inPointFeatures = shapefile
    inRasterList = [[raster, 'ei{}'.format(i)]]

    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")

    # Execute ExtractValuesToPoints
    ExtractMultiValuesToPoints(inPointFeatures, inRasterList)

    print(i, 'extract multi values to pts done')


def calc_sigma(shapefile, i, elev_ID):
    arcpy.AddField_management(shapefile, "sigmae_{}".format(i), "DOUBLE")
    arcpy.CalculateField_management(shapefile, "sigmae_{}".format(i),
                                    'abs(!{}! - !ei{}!)'.format(elev_ID, i), "PYTHON")
    print(i, 'calculate sigma done')


def query_by_sigma(shapefile, i, unit):
    table = shapefile
    out_table = "{}_qc{}_result_table".format(unit, i)
    in_key_field_option = 'USE_KEY_FIELDS'
    in_key_field = ''
    in_field = ''
    where_clause = 'sigmae_{} < 100'.format(i)

    in_features = arcpy.MakeQueryTable_management(table, out_table, in_key_field_option, in_key_field, in_field,
                                                  where_clause)
    out_feature_class = "{}_qc{}_result".format(unit, i)
    arcpy.CopyFeatures_management(in_features, out_feature_class)

    print(i, 'query done and shapefile output')


def copy_master_to_working(unit):
    arcpy.FeatureClassToFeatureClass_conversion('{}_data_all_orig'.format(unit), env.workspace,
                                                '{}_data_all_working'.format(unit))

    working_fc = '{}_data_all_working'.format(unit)
    return working_fc


def copy_final(raster, unit):
    out_geodatabase = 'E:\DelawareBasin\DelawareBasin_geodata\workingdata\QCoutputs_v12.gdb'
    name = '{}\{}'.format(out_geodatabase, unit)
    arcpy.CopyRaster_management(raster, name, '', '', '-3.402823e38',
                                'NONE', 'NONE', '32_BIT_FLOAT', '', '')


def main():
    unitnames = ['alvbase', 'udockum_base', 'sr_top', 'ldockum_base', 'deweylake_base', 'uochoan_base', 'lochoan_base',
                 'artesia_base']
    elevIDs = ['alv_b_elev', 'ud_b_elev', 'srtop_elev', 'ld_b_elev', 'rtop_elev', 'saltop_elev', 'lochoan_b_elev',
               'art_b_elev']

    for unit, elev_ID in zip(unitnames, elevIDs):
        working_fc = copy_master_to_working(unit)

        temp_fcs = [working_fc, '{}_qc0_result'.format(unit), '{}_qc1_result'.format(unit),
                    '{}_qc2_result'.format(unit), '{}_qc3_result'.format(unit)]

        for i, fc in enumerate(temp_fcs):
            print(i, fc)
            topo_to_raster(fc, i, elev_ID, unit)
            out_ras = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\dbasin_t2r2_dec2021\t2r{}{}.tif'.format(unit,
                                                                                                                   i)
            extract_vals_to_pts(fc, out_ras, i)
            calc_sigma(fc, i, elev_ID)
            query_by_sigma(fc, i, unit)
            if i == 4:
                copy_final(out_ras, unit)
            print('{} QC process finished'.format(unit))


if __name__ == '__main__':
    main()
