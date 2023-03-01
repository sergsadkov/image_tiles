# Code to create tiles from a set of one-band raster files

# All files need to have the same projection, data type, and geotransform
# The original data values are preserved, no reprojection performed

import os, sys
import numpy as np
from math import sin, cos, floor
from paths import DeleteFile, TempName
from auxiliary import functionWorkTime

try:
    from osgeo import gdal
except:
    import gdal


# Creates composite from a set of raster bands
class RasterBandSource(list):

    def __init__(self, *input_tuple):
        self.clear()
        self.size = None
        self.RasterYSize = None
        for input in input_tuple:
            ds_in = gdal.Open(input)
            if ds_in is None:
                raise Exception(f'Cannot open raster from "{input}"')
            else:
                if self.size is None:
                    self.size = (ds_in.RasterXSize, ds_in.RasterYSize)
                elif (self.size[0] != ds_in.RasterXSize) or \
                        (self.size[1] != ds_in.RasterYSize):
                    Exception(f'Source data raster size mismatch: {self.size} \
                        vs ({ds_in.RasterXSize}, {ds_in.RasterYSize})')
                self.append(input)

    # Makes a set of tiles with several bands each
    @functionWorkTime
    def save_tiles(self, output_dir, name='image', tile_size=256,
                   input_vector=None, mask_dir=None, column=None):

        if not os.path.exists(output_dir):
            raise Exception(f'Output folder does not exist: {output_dir}')
        if (mask_dir is not None) and (input_vector is not None):
            if not os.path.exists(mask_dir):
                raise Exception(f'Mask folder does not exist: {output_dir}')
            elif os.path.exists(self[0]):
                full_mask_path = TempName(ext='tif')
                rasterize_mask(self[0], input_vector, full_mask_path, column)

        for y_tile in range(floor(self.size[1] / tile_size)):
            for x_tile in range(floor(self.size[0] / tile_size)):
                x = x_tile * tile_size
                y = y_tile * tile_size
                tile_name = f'{name}_X{x_tile+1}_Y{y_tile+1}.tif'
                tile_path = os.path.join(output_dir, tile_name)

                if os.path.exists(tile_path):
                    continue

                elif save_tile(self, x, y, tile_size, tile_path):
                    continue

                elif (mask_dir is not None) and (input_vector is not None):

                    mask_path = os.path.join(mask_dir, tile_name)

                    if os.path.exists(mask_path):
                        continue

                    # The following code is slow due to multiple times
                    # vector data processing:
                    # rasterize_mask(tile_path, input_vector, mask_path, column)

                    # Creating mask from full_mask_path in temp dir
                    save_tile([full_mask_path], x, y, tile_size, mask_path)

        if (mask_dir is not None) and (input_vector is not None):
            DeleteFile(full_mask_path)



# Creates geotransform for a tile
def TileGeoTransform(gt, x_min, y_min):
    new_gt = list(gt)
    dx = (new_gt[1] * cos(gt[2]) * x_min) + (new_gt[5] * sin(gt[4]) * y_min)
    dy = (new_gt[1] * sin(gt[2]) * x_min) + (new_gt[5] * cos(gt[4]) * y_min)
    new_gt[0] += dx
    new_gt[3] += dy
    return tuple(new_gt)


# @functionWorkTime
def save_tile(input_list, x, y, tile_size, output_path, **options):

    raster_list = [gdal.Open(input) for input in input_list]
    ds_1 = raster_list[0]
    x_block_size = min(tile_size, ds_1.RasterXSize - x)
    y_block_size = min(tile_size, ds_1.RasterXSize - y)

    band_array_list = [ds.GetRasterBand(1).
                           ReadAsArray(x, y, x_block_size, y_block_size)
                       for ds in raster_list]

    y_res, x_res = band_array_list[0].shape
    data_type = ds_1.GetRasterBand(1).DataType
    geotransform = TileGeoTransform(ds_1.GetGeoTransform(), x, y)

    if any([band_array is None for band_array in band_array_list]):
        raise Exception('Band is None')
    elif all([(band_array==0).all() for band_array in band_array_list]):
        # print('Data is empty, cannot create tile')
        return 1
    else:
        drv = gdal.GetDriverByName('GTiff')
        out_ds = drv.Create(output_path, x_res, y_res, len(band_array_list), data_type)
        out_ds.SetProjection(ds_1.GetProjection())
        out_ds.SetGeoTransform(geotransform)

        for i, band_array in enumerate(band_array_list):
            band = out_ds.GetRasterBand(i+1)
            band.WriteArray(band_array)
            band.SetNoDataValue(0)

        out_ds = None

        return 0


# Make raster mask from a vector file writing values from a specified column
# !!! There should be no NULL data in the specified column !!!
@functionWorkTime
def rasterize_mask(in_raster, in_vector, out_raster, column):
    in_ds = gdal.Open(in_raster)
    if in_ds is None:
        raise Exception(f'Cannot open raster: "{in_raster}"')
    drv = gdal.GetDriverByName('GTiff')
    out_ds = drv.Create(out_raster, in_ds.RasterXSize, in_ds.RasterYSize, 1, 2)
    out_ds.SetProjection(in_ds.GetProjection())
    out_ds.SetGeoTransform(in_ds.GetGeoTransform())
    out_ds.GetRasterBand(1).SetNoDataValue(0)
    options = gdal.RasterizeOptions(gdal.ParseCommandLine(f'-a {column}'))
    gdal.Rasterize(out_ds, in_vector, options=options)
    out_ds = None


# Make a set of tiles from data source
def make_tiles(input_tuple, output, **options):
    # Not ready yet
    pass
