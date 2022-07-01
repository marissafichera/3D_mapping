import arcpy

import arcpy
import os
from arcpy import env
from arcpy.sa import *
import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")
env.workspace = r'E:\DelawareBasin\report_figures\report_figures.gdb'
env.outputCoordinateSystem = arcpy.SpatialReference("NAD 1983 UTM Zone 13N")

arcpy.env.snapRaster = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\BASEMAP.gdb\z_snapraster'
arcpy.env.overwriteOutput = True

def feature_vertices_to_pts(line, unit):
    print('feature vertices to points for ', unit, 'along', line)
    point_file = 'profile_pts_{}'.format(line)
    print('output file name = ', point_file)
    arcpy.FeatureVerticesToPoints_management(line, point_file, 'ALL')

    print('adding X Y Z fields')
    arcpy.AddFields_management(point_file, [['Xcoord', 'LONG'], ['Ycoord', 'LONG'], ['Zcoord', 'DOUBLE']])
    print('calculating X Y Z coordinates')
    arcpy.CalculateGeometryAttributes_management(point_file, [['Xcoord', 'POINT_X'], ['Ycoord', 'POINT_Y'], ['Zcoord', 'POINT_Z']])

    print('creating final cross section data table')
    out_table = 'XS_datatable_{}{}.csv'.format(line, unit)
    print('output table name = ', out_table)
    arcpy.TableToTable_conversion(point_file, r'E:\DelawareBasin\report_figures', out_table)

    return out_table

def ishape(xsline, unit):


    print('interpolate shape unit = ', unit, 'along', xsline)
    raster = '{}_elev_ft'.format(unit)
    print(unit, 'raster = ', raster)
    out_line = 'is_wexs_{}_{}'.format(unit, xsline)
    arcpy.InterpolateShape_3d(raster, xsline, out_line)
    print('interpolate shape done -- input raster = {} ---- xsline = {} ----, output line with Z vals = {}'.format(raster, xsline, out_line))
    xsdatatable = feature_vertices_to_pts(out_line, unit)

    return xsdatatable



def stack_profile(xsline):
    units = ['alvb', 'udb', 'srt', 'ldb', 'dlb', 'uob', 'lob', 'artb', 'capitant', 'capitanb']
    in_line_feature = xsline

    profile_targets = ['R00_land_resample']

    for unit in units:
        raster = '{}_elev_ft'.format(unit)
        profile_targets.append(raster)
        print('Raster Appended = {}'.format(raster))

    print('profile targets = ', profile_targets)
    out_table = 'profile_wexs_all'
    out_graph = 'profile_graph_wexs_all'
    arcpy.StackProfile_3d(in_line_feature, profile_targets, out_table, out_graph)

    arcpy.AddField_management(out_table, 'Xcoord', 'LONG')
    arcpy.CalculateGeometryAttributes_management(out_table, 'Xcoord', 'POINT_X')


def plot_xsection(xsline, xsdatatables, units):
    table_location = r'E:\DelawareBasin\report_figures'
    ax = plt.axes()

    for unit, xsdt in zip(units, xsdatatables):
        table = pd.read_csv(os.path.join(table_location, xsdt))
        print('table = ', xsdt)
        print('unit = ', unit)
        df = pd.DataFrame(table)

        X = df['Xcoord']
        df['X_ft'] = X*3.281
        df['X_miles'] = X*3.281/5280
        X_ft = df['X_ft']
        X_mi = df['X_miles']
        Z = df['Zcoord']
        label = '{}'.format(unit)

        ax.plot(X, Z, label='{}'.format(unit))
        plt.xlabel('Easting (m)')
        plt.ylabel('Elevation (ft. amsl)')
        plt.legend()


    x_left, x_right = plt.xlim()
    print('xleft = {}, xright = {}'.format(x_left, x_right))
    y_low, y_high = plt.ylim()
    print('ylow = {}, yhigh = {}'.format(y_low, y_high))
    # a = abs((x_right - x_left) / (y_high - y_low)) * ratio
    ax.set_aspect(20/3.281)
    plt.show()


def main():
    units = ['landsurf', 'alvb', 'udb', 'srt', 'ldb', 'dlb', 'uob', 'lob', 'artb', 'capitant', 'capitanb']
    xsline = 'wexsline_southjal'

    PLOT_ONLY_FLAG = 'no'
    if PLOT_ONLY_FLAG == 'yes':
        print('skipping GIS part')
    else:
        xsdatatables = []
        for unit in units:
            print('begin cross-section data generation for {} along {}'.format(unit, xsline))
            xsdatatable = ishape(xsline, unit)
            xsdatatables.append(xsdatatable)
            print('xs data tables === ', xsdatatables)

        print('plotting cross section')
        plot_xsection(xsline, xsdatatables, units)


    # existing_tables = ['XS_datatable_is_wexs_landsurf_wexsline_throughCarlsbadlandsurf.csv', 'XS_datatable_is_wexs_alvb_wexsline_throughCarlsbadalvb.csv', 'XS_datatable_is_wexs_udb_wexsline_throughCarlsbadudb.csv', 'XS_datatable_is_wexs_srt_wexsline_throughCarlsbadsrt.csv', 'XS_datatable_is_wexs_ldb_wexsline_throughCarlsbadldb.csv', 'XS_datatable_is_wexs_dlb_wexsline_throughCarlsbaddlb.csv', 'XS_datatable_is_wexs_uob_wexsline_throughCarlsbaduob.csv', 'XS_datatable_is_wexs_lob_wexsline_throughCarlsbadlob.csv', 'XS_datatable_is_wexs_artb_wexsline_throughCarlsbadartb.csv', 'XS_datatable_is_wexs_capitant_wexsline_throughCarlsbadcapitant.csv', 'XS_datatable_is_wexs_capitanb_wexsline_throughCarlsbadcapitanb.csv']
    # plot_xsection(xsline, existing_tables, units)


if __name__ == '__main__':
    main()
