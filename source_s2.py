import os
from zipfile import ZipFile

from paths import Files, TempFolder

# Contains {<channel index>: (<band id for the sattelite>, \
#           (<image resolution 1>, <image resolution 2>, ...)), ...}
BANDS = {'C': ('B01', [20, 60]), # Coastal aerosol
            'B': ('B02', [10, 20, 60]), # Blue
            'G': ('B03', [10, 20, 60]), # Green
            'R': ('B04', [10, 20, 60]), # Red
            'RE1': ('B05', [20, 60]), # Vegetation Red Edge 1
            'RE2': ('B06', [20, 60]), # Vegetation Red Edge 2
            'RE3': ('B07', [20, 60]), # Vegetation Red Edge 3
            'N': ('B08', [10]), # Near Infrared (NIR)
            'NN': ('B8A', [20, 60]), # Narrow NIR
            'WV': ('B09', [60]), # Water Vapour
            # 'SWIRC': ('B10', (20, 60)), # SWIR Cirrus
            'SWIR1': ('B11', [20, 60]),
            'SWIR2': ('B12', [20, 60]),
            'Q': ('TCI', [10, 20, 60]), # Quicklook
        }


# Collect band keys for the specified bands and resolution
def s2_bands(band_list, resolution):

    band_keys = []

    for band in band_list:
        if band in BANDS:
            key, resolutions = BANDS[band]
            if resolution in resolutions:
                band_keys.append(f'{key}_{resolution}m.jp2')
            else:
                raise Exception(f'Sentinel-2 has no band "{band}" \
                                with resolution {resolution} meter')
                # Need to add another function later to reproject data in this case
        else:
            raise Exception(f'Sentinel-2 has no band "{band}"')

    return band_keys


# Collect source data files from the source folder or archive
def s2_files(source, band_keys):

    band_files = []

    if os.path.isfile(source) and source.lower().endswith('.zip'):

        zip_data = ZipFile(source, 'r')
        zip_paths = [f.filename for f in zip_data.filelist]
        temp_folder = TempFolder()

        for band_key in band_keys:
            for zip_path in zip_paths:
                if zip_path.endswith(band_key):
                    zip_data.extract(zip_path, path=temp_folder)
                    band_files.append(os.path.join(temp_folder, zip_path))
                    break

    else:
        files = Files(source, extensions='jp2')
        for band_key in band_keys:
            for file in files:
                if file.endswith(band_key):
                    band_files.append(file)
                    break

    return band_files
