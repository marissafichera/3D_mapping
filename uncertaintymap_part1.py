import os
import re
import numpy as np
from numpy import array, dstack
import pandas as pd
import arcpy
from arcpy import env
from arcpy.sa import *

env.workspace = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo'
env.outputCoordinateSystem = arcpy.SpatialReference("NAD 1983 UTM Zone 13N")
arcpy.env.snapRaster = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\BASEMAP.gdb\z_snapraster'
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

n = 5

def copy_faults():
    print('copying faults to fc_exports folder for use in topo to raster')
    # this is where your faults live
    env.workspace = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\ModelInputData_postQC.gdb'
    # this is where you want your faults to live - should be same folder as 'out_loc' in create_feature_class()
    qc_workspace = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\fc_exports'

    arcpy.FeatureClassToFeatureClass_conversion('guadmtnfault', qc_workspace, 'guadmtnfault')
    arcpy.FeatureClassToFeatureClass_conversion('centralbasinplatform', qc_workspace, 'centralbasinplatform')
    print('faults now in fc_exports folder for use in topo to raster')


def topo_to_raster(name):
    #first put centralbasinplatform and guadmtnfault in folder (did this by hand for v12)
    # copy_faults()

    # need to make n number of surfaces, where n = number of random sample text files generated in sample_percent
    env.workspace = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\fc_exports'

    for i in range(1, n+1):
        print('Running topo to raster on {}, {}'.format(name, i))
        fc = '{}_fc{}.shp'.format(name, i)
        inPointElevations = TopoPointElevation([[fc, 'ei4']])
        inCliffs = TopoCliff(['cbp_f.shp', 'gm_f.shp'])
        inFeatures = ([inPointElevations, inCliffs])

        outTTR = TopoToRaster(inFeatures, "1000", Extent(485690, 3530089, 693190, 3627589), "20", "#", "#", "ENFORCE",
                          "SPOT", "20", "#", "1", "0", "0", "200", '#', '#', '#', '#', '#', '#', '#')

        outTTR.save(r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\t2r_exports\{}_t2r{}.tif'.format(name, i))
        print('t2r', '{}, {}'.format(name, i))
    print('t2r done')


def create_feature_class(name):
    env.workspace = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\rand_sample_exports'
    out_loc = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\fc_exports'

    for i in range(1, n+1):
        print('Creating feature class out of rand sample files: {}, {}'.format(name, i))
        table = '{}_rand{}.csv'.format(name, i)
        X = 'Easting'
        Y = 'Northing'
        Z = 'ei4'
        out_layername = '{}_lyr{}'.format(name, i)
        out_layer = os.path.join(out_loc, out_layername)
        arcpy.MakeXYEventLayer_management(table, X, Y, out_layer, env.outputCoordinateSystem, Z)

        fc_path = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\fc_exports'
        fc_name = '{}_fc{}'.format(name, i)
        arcpy.FeatureClassToFeatureClass_conversion(out_layer, fc_path, fc_name)
        print('fc', '{} {}'.format(name, i), 'created')
    print('{} all feature classes created'.format(name))


def sample_percent(df, name):
    # ei4 is the final point dataset used in making the final raster surface, so need to take a random 75% of
    # that dataset (500) times - store in 'output_random_sample_datasets'
    root = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\rand_sample_exports'

    for i in range(1, n+1):
        print('RANDOM SAMPLE {}: taking random sample of {} dataset'.format(i, name))
        rand_samp = df.sample(frac=.75)
        p = '{}_rand{}.csv'.format(name, i)
        rand_samp.to_csv(os.path.join(root, p))
        print('random sample file taken {}, {}'.format(i, name))
    print('random sample files created')


def export_fc_to_csv():
    # I just did this by hand last time (v12)
    env.workspace = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\ModelInputData_postQC.gdb'
    ext = '_qc3_result'
    units = ['alvbase', 'udockum_base', 'sr_top', 'ldockum_base', 'deweylake_base', 'uochoan_base', 'lochoan_base', 'artesia_base']
    elevIDs = ['alv_b_elev', 'ud_b_elev', 'srtop_elev', 'ld_b_elev', 'rtop_elev', 'saltop_elev', 'lochoan_b_elev', 'art_b_elev']

    for unit, elevID in zip(units, elevIDs):
        print('EXPORTING attribute table to csv for {}'.format(unit))
        fields = ['OBJECTID', 'Field1', 'OriginalID', 'Easting', 'Northing', '{}'.format(elevID),
                  'DataSource', 'ei4']
        out_path = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\qcexports'
        out_csv = '{}_qc3export.csv'.format(unit)
        arcpy.ExportXYv_stats('{}{}'.format(unit, ext), fields, 'COMMA', os.path.join(out_path, out_csv), 'ADD_FIELD_NAMES')
        print('EXPORTED attribute table to csv for {}'.format(unit))

def main():
    ROOT = r'C:\Users\mfichera\PycharmProjects\3D_mapping\dbasin_montecarlo\qcexports'

    # export_fc_to_csv()
    ## it's qc3 export because from the QC process, the third output contains the data used for the final surface
    alv = 'alvb_qc3_export.csv'
    art = 'artb_qc3_export.csv'
    dl = 'dlb_qc3_export.csv'
    ld = 'ldb_qc3_export.csv'
    lo = 'lob_qc3_export.csv'
    sr = 'srt_qc3_export.csv'
    ud = 'udb_qc3_export.csv'
    uo = 'uob_qc3_export.csv'
    #
    ps = [alv, ud, sr, ld, dl, uo, lo, art]

    names = ['alvb', 'udb', 'srt', 'ldb', 'dlb', 'uob', 'lob', 'artb']


    for name, p in zip(names, ps):
        qcdata = pd.read_csv(os.path.join(ROOT, p))
        df = pd.DataFrame(qcdata)

        sample_percent(df, name)
        create_feature_class(name)
        topo_to_raster(name)



if __name__ == '__main__':
    main()