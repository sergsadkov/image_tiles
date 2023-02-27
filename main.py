# This is a sample Python script.

from source_s2 import *
from tiles import *

def print_hi():
    # Use a breakpoint in the code line below to debug your script.
    print(f'Script to make tiled deep learning training sets')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi()

    # source_path = input('Print path to the input data source: ')
    # band_str = input('Print band list, comma separated: ')
    # band_list = [band.upper().strip() for band in band_str.split(',')]
    # resolution = int(input('Print resolution: '))
    # output_dir = input('Print path to the output directory: ')
    # mask_dir = input('Print path to the output mask directory: ')
    # input_vector = input('Print path to the input vector file: ')
    # column = input('Print vector mask column name: ')

    source_path = r'C:\Users\Пользватель\Downloads\S2A_MSIL2A_20220319T064631_N0400_R020_T40TGP_20220319T102951.zip'
    band_list = ['R', 'G', 'B', 'N']
    resolution = 10
    output_dir = r'c:\test\zip\new'
    mask_dir = r'c:\test\zip\mask'
    input_vector = r'c:\test\vector_test.shp'
    column = 'code'

    band_keys = s2_bands(band_list, resolution)
    band_files = s2_files(source_path, band_keys)
    raster_band_source = RasterBandSource(*tuple(band_files))
    raster_band_source.save_tiles(output_dir, name='image', tile_size=256,
                                  mask_dir=mask_dir, input_vector=input_vector,
                                  column='code')


print('Script finished successfully')
