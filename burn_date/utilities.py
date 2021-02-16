
import os
from subprocess import Popen, PIPE, STDOUT, check_call
import numpy as np
from osgeo import gdal
from gdalconst import GA_ReadOnly
import sys
sys.path.append('../')
import constants_and_names as cn
import universal_util as uu


def hdf_to_array(hdf):
    hdf_open = gdal.Open(hdf).GetSubDatasets()
    ds = gdal.Open(hdf_open[0][0])
    array = ds.ReadAsArray()

    return array


def makedir(folder):
    if not os.path.exists(folder):
        os.mkdir(folder)


def raster_to_array(raster):
    ds = gdal.Open(raster)
    array = np.array(ds.GetRasterBand(1).ReadAsArray())
    # array = np.array(ds.GetRasterBand(1).ReadAsArray(win_xsize = 5000, win_ysize = 5000)) # For local testing. Reading in the full array is too large.
    
    return array


def array_to_raster_simple(array, outname, template):
    
    ds = gdal.Open(template)
    x_pixels = ds.RasterXSize
    y_pixels = ds.RasterYSize
    
    geoTransform = ds.GetGeoTransform()
    height = geoTransform[1]
    
    pixel_size = height
    
    minx = geoTransform[0]
    maxy = geoTransform[3]
    
    wkt_projection = ds.GetProjection()
    
    driver = gdal.GetDriverByName('GTiff')

    dataset = driver.Create(
        outname,
        x_pixels,
        y_pixels,
        1,
        gdal.GDT_Int16,
        options=["COMPRESS=LZW"])

    dataset.SetGeoTransform((
        minx,    # 0
        pixel_size,  # 1
        0,                      # 2
        maxy,    # 3
        0,                      # 4
        -pixel_size))  

    dataset.SetProjection(wkt_projection)
    dataset.GetRasterBand(1).WriteArray(array)
    dataset.FlushCache()  # Write to disk.
    
    return outname


def array_to_raster(global_grid_hv, year, array, template_hdf, outfolder):

    filename = '{0}_{1}.tif'.format(year, global_grid_hv)
    dst_filename = os.path.join(outfolder, filename)
    # x_pixels, y_pixels = get_extent.get_size(raster)
    hdf_open = gdal.Open(template_hdf).GetSubDatasets()
    ds = gdal.Open(hdf_open[0][0])
    x_pixels = ds.RasterXSize
    y_pixels = ds.RasterYSize

    geoTransform = ds.GetGeoTransform()

    pixel_size = geoTransform[1]

    minx = geoTransform[0]
    maxy = geoTransform[3]

    wkt_projection = ds.GetProjection()

    driver = gdal.GetDriverByName('GTiff')

    dataset = driver.Create(
        dst_filename,
        x_pixels,
        y_pixels,
        1,
        gdal.GDT_Int16, )

    dataset.SetGeoTransform((
        minx,    # 0
        pixel_size,  # 1
        0,                      # 2
        maxy,    # 3
        0,                      # 4
        -pixel_size))  

    dataset.SetProjection(wkt_projection)
    dataset.GetRasterBand(1).WriteArray(array)
    dataset.FlushCache()  # Write to disk.
    
    return dst_filename


def stack_arrays(list_of_year_arrays):

    stack = np.stack(list_of_year_arrays)
    
    return stack


def makedir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

    return dir


def download_df(year, hv_tile, output_dir):
        include = 'MCD64A1.A{0}*{1}*'.format(year, hv_tile)
        cmd = ['aws', 's3', 'cp', cn.burn_year_hdf_raw_dir, output_dir, '--recursive', '--exclude',
               "*", '--include', include]

        # Solution for adding subprocess output to log is from https://stackoverflow.com/questions/21953835/run-subprocess-and-print-output-to-logging
        process = Popen(cmd, stdout=PIPE, stderr=STDOUT)
        with process.stdout:
            uu.log_subprocess_output(process.stdout)


