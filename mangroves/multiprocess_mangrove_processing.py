### Creates Hansen-style tiles for aboveground mangrove biomass (Mg/ha) from Lola Fatoyinbo's country
### mangrove data.
### Output tiles conform to the dimensions, resolution, and other properties of Hansen loss tiles.

import multiprocessing
import mangrove_processing
import sys
sys.path.append('../')
import constants_and_names as cn
import universal_util as uu

# # Downloads zipped raw mangrove files
# # NOTE: for some reason, during the unzip process, it asks if a few files need to be replaced, so you have to monitor
# # the unzipping and intervene or it'll never finish.
# uu.s3_file_download(os.path.join(cn.mangrove_biomass_raw_dir, cn.mangrove_biomass_raw_file), '.')
#
# # Unzips mangrove images into a flat structure (all tifs into main folder using -j argument)
# # NOTE: Unzipping the Australia tif takes a very long time, so don't worry if the script appears to freeze on that.
# cmd = ['unzip', '-j', cn.mangrove_biomass_raw_file]
# subprocess.check_call(cmd)
#
# # Creates vrt of all raw mangrove tifs
# utilities.build_vrt(utilities.mangrove_vrt)

# Iterates through all possible tiles (not just WHRC biomass tiles) to create mangrove biomass tiles that don't have analogous WHRC tiles
total_tile_list = uu.tile_list(cn.pixel_area_dir)
# biomass_tile_list = ['00N_000E', '20S_120W', '00N_120E'] # test tile
print total_tile_list

# For multiprocessor use
# This script didn't work with count/4; perhaps that was using too many processors.
# It did work with count/5, though.
count = multiprocessing.cpu_count()
pool = multiprocessing.Pool(processes=count/5)
pool.map(mangrove_processing.create_mangrove_tiles, total_tile_list)

# # For single processor use, for testing purposes
# for tile in total_tile_list:
#
#     mangrove_processing.create_mangrove_tiles(tile)