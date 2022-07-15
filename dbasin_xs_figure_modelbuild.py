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
# env.workspace = r'E:\DelawareBasin\report_figures\report_figures.gdb'
env.workspace = r'E:\Estancia Basin\EstanciaGeology.gdb'
env.outputCoordinateSystem = arcpy.SpatialReference("NAD 1983 UTM Zone 13N")

# arcpy.env.snapRaster = r'E:\DelawareBasin\DelawareBasin_geodata\workingdata\BASEMAP.gdb\z_snapraster'
arcpy.env.overwriteOutput = True


def locate_features_along_routes(in_features, in_route):
    print('locating features along routes')
    print('input features = {} ALONG ROUTE = {}'.format(in_features, in_route))
    route_id = 'id'
    radius = '100 Meters'
    out_xs_table = 'xsdatatable_{}'.format(in_features)
    out_event_props = 'rid point MEASURE'

    arcpy.LocateFeaturesAlongRoutes_lr(in_features, in_route, route_id, radius, out_xs_table, out_event_props)
    tablecopy = '{}.csv'.format(out_xs_table)
    arcpy.TableToTable_conversion(out_xs_table, r'E:\Estancia Basin', tablecopy)

    return tablecopy


def feature_vertices_to_pts(line, unit):
    print('feature vertices to points for ', unit, 'along', line)
    out_point_file_name = 'profile_pts_{}'.format(line)
    print('output file name = ', out_point_file_name)
    arcpy.FeatureVerticesToPoints_management(line, out_point_file_name, 'ALL')

    print('adding X Y Z fields')
    arcpy.AddFields_management(out_point_file_name, [['Xcoord', 'LONG'], ['Ycoord', 'LONG'], ['Zcoord', 'DOUBLE']])
    print('calculating X Y Z coordinates')
    arcpy.CalculateGeometryAttributes_management(out_point_file_name, [['Xcoord', 'POINT_X'], ['Ycoord', 'POINT_Y'], ['Zcoord', 'POINT_Z']])

    # print('creating final cross section data table')
    # out_table_name = 'XS_datatable_{}{}.csv'.format(line, unit)
    # print('output table name = ', out_table_name)
    # arcpy.TableToTable_conversion(out_point_file_name, r'E:\Estancia Basin', out_table_name)

    # locate_features_along_routes(point_file)
    return out_point_file_name
    # return out_table

def ishape(xsline, unit):


    print('interpolate shape unit = ', unit, 'along', xsline)
    raster = '{}'.format(unit)
    print(unit, 'raster = ', raster)
    out_line = 'is_{}_{}'.format(unit, xsline)
    arcpy.InterpolateShape_3d(raster, xsline, out_line)
    print('interpolate shape done -- input raster = {} ---- xsline = {} ----, output line with Z vals = {}'.format(raster, xsline, out_line))
    # xsdatatable = feature_vertices_to_pts(out_line, unit)

    # return xsdatatable
    return out_line



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
    # table_location = r'E:\DelawareBasin\report_figures'
    table_location = r'E:\Estancia Basin'
    ax = plt.axes()

    for unit, xsdt in zip(units, xsdatatables):
        table = pd.read_csv(os.path.join(table_location, xsdt))
        print('table = ', xsdt)
        print('unit = ', unit)
        df = pd.DataFrame(table)

        # X = df['Xcoord']
        # df['X_ft'] = X*3.281
        # df['X_miles'] = X*3.281/5280
        # X_ft = df['X_ft']
        # X_mi = df['X_miles']
        # Z = df['Zcoord']

        X = df['MEASURE']
        Z = df['Zcoord']
        label = '{}'.format(unit)

        ax.plot(X, Z, label='{}'.format(unit))
        plt.xlabel('Distance (m)')
        plt.ylabel('Elevation (ft. amsl)')
        plt.legend()


    x_left, x_right = plt.xlim()
    print('xleft = {}, xright = {}'.format(x_left, x_right))
    y_low, y_high = plt.ylim()
    print('ylow = {}, yhigh = {}'.format(y_low, y_high))
    # a = abs((x_right - x_left) / (y_high - y_low)) * ratio
    ax.set_aspect(10/3.281)
    plt.show()


def create_routes(xsline, ):
    route_id = 'id'
    out_fc = '{}_route'.format(xsline)

    arcpy.CreateRoutes_lr(xsline, route_id, out_fc)

    return out_fc


def main():
    # units = ['landsurf', 'alvb', 'udb', 'srt', 'ldb', 'dlb', 'uob', 'lob', 'artb', 'capitant', 'capitanb']
    units = ['landsurf_ft', 'eb_basinfill_top_raster', 'eb_basinfill_bottom_raster', 'eb_madera_top_raster',
             'eb_madera_bottom_raster',
             'eb_mesozoic_top_raster', 'eb_mesozoic_bottom_raster', 'eb_sanandresglorieta_top_raster',
             'eb_sanandresglorieta_bottom_raster',
             'eb_yesoabo_top_raster', 'eb_yesoabo_bottom_raster', 'eb_basement_top']

    xsline = 'xs_ew_redraw'

    PLOT_ONLY_FLAG = 'no'
    if PLOT_ONLY_FLAG == 'yes':
        print('skipping GIS part')
    else:
        route = create_routes(xsline)
        xsdatatables = []
        for unit in units:
            print('begin cross-section data generation for {} along {}'.format(unit, xsline))
            # xsdatatable = ishape(xsline, unit)
            # points_file = ishape(xsline, unit)
            is_line = ishape(xsline, unit)
            points_fc = feature_vertices_to_pts(is_line, unit)
            xsdatatable = locate_features_along_routes(points_fc, route)
            xsdatatables.append(xsdatatable)
            print('xs data tables === ', xsdatatables)

        print('plotting cross section')
        plot_xsection(xsline, xsdatatables, units)


    # existing_tables = ['XS_datatable_is_wexs_landsurf_wexsline_throughCarlsbadlandsurf.csv', 'XS_datatable_is_wexs_alvb_wexsline_throughCarlsbadalvb.csv', 'XS_datatable_is_wexs_udb_wexsline_throughCarlsbadudb.csv', 'XS_datatable_is_wexs_srt_wexsline_throughCarlsbadsrt.csv', 'XS_datatable_is_wexs_ldb_wexsline_throughCarlsbadldb.csv', 'XS_datatable_is_wexs_dlb_wexsline_throughCarlsbaddlb.csv', 'XS_datatable_is_wexs_uob_wexsline_throughCarlsbaduob.csv', 'XS_datatable_is_wexs_lob_wexsline_throughCarlsbadlob.csv', 'XS_datatable_is_wexs_artb_wexsline_throughCarlsbadartb.csv', 'XS_datatable_is_wexs_capitant_wexsline_throughCarlsbadcapitant.csv', 'XS_datatable_is_wexs_capitanb_wexsline_throughCarlsbadcapitanb.csv']
    # plot_xsection(xsline, existing_tables, units)

    # existing_tables = []
    # for unit in units:
    #     etable = 'xsdatatable_profile_pts_is_wexs_{}_{}.csv'.format(unit, xsline)
    #     existing_tables.append(etable)
    #
    # plot_xsection(xsline, existing_tables, units)


if __name__ == '__main__':
    main()
