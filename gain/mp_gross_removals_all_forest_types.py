'''
This script calculates the cumulative above and belowground carbon dioxide gain (removals) for all forest types
for the duration of the model.
It multiplies the annual aboveground and belowground carbon removal factors by the number of years of gain and the C to CO2 conversion.
It then sums the aboveground and belowground gross removals to get gross removals for all forest types in both emitted_pools.
That is the final gross removals for the entire model.
Note that gross removals from this script are reported as positive values.
'''

import multiprocessing
import argparse
import os
import datetime
from functools import partial
import sys
sys.path.append('../')
import constants_and_names as cn
import universal_util as uu
sys.path.append(os.path.join(cn.docker_app,'gain'))
import gross_removals_all_forest_types

def mp_gross_removals_all_forest_types(sensit_type, tile_id_list, run_date = None, no_upload = True):

    os.chdir(cn.docker_base_dir)

    # If a full model run is specified, the correct set of tiles for the particular script is listed
    if tile_id_list == 'all':
        # List of tiles to run in the model
        # tile_id_list = uu.tile_list_s3(cn.model_extent_dir, sensit_type)
        gain_year_count_tile_id_list = uu.tile_list_s3(cn.gain_year_count_dir, sensit_type=sensit_type)
        annual_removals_tile_id_list = uu.tile_list_s3(cn.annual_gain_AGC_all_types_dir, sensit_type=sensit_type)
        tile_id_list = list(set(gain_year_count_tile_id_list).intersection(annual_removals_tile_id_list))
        uu.print_log("Gross removals tile_id_list is combination of gain_year_count and annual_removals tiles:")

    uu.print_log(tile_id_list)
    uu.print_log("There are {} tiles to process".format(str(len(tile_id_list))) + "\n")


    # Files to download for this script.
    download_dict = {
        cn.annual_gain_AGC_all_types_dir: [cn.pattern_annual_gain_AGC_all_types],
        cn.annual_gain_BGC_all_types_dir: [cn.pattern_annual_gain_BGC_all_types],
        cn.gain_year_count_dir: [cn.pattern_gain_year_count]
    }


    # List of output directories and output file name patterns
    output_dir_list = [cn.cumul_gain_AGCO2_all_types_dir, cn.cumul_gain_BGCO2_all_types_dir, cn.cumul_gain_AGCO2_BGCO2_all_types_dir]
    output_pattern_list = [cn.pattern_cumul_gain_AGCO2_all_types, cn.pattern_cumul_gain_BGCO2_all_types, cn.pattern_cumul_gain_AGCO2_BGCO2_all_types]


    # Downloads input files or entire directories, depending on how many tiles are in the tile_id_list, if AWS credentials are found
    if uu.check_aws_creds():

        for key, values in download_dict.items():
            dir = key
            pattern = values[0]
            uu.s3_flexible_download(dir, pattern, cn.docker_base_dir, sensit_type, tile_id_list)


    # If the model run isn't the standard one, the output directory and file names are changed
    if sensit_type != 'std':
        uu.print_log("Changing output directory and file name pattern based on sensitivity analysis")
        output_dir_list = uu.alter_dirs(sensit_type, output_dir_list)
        output_pattern_list = uu.alter_patterns(sensit_type, output_pattern_list)

    # A date can optionally be provided by the full model script or a run of this script.
    # This replaces the date in constants_and_names.
    if run_date is not None:
        output_dir_list = uu.replace_output_dir_date(output_dir_list, run_date)


    # Calculates gross removals
    if cn.count == 96:
        if sensit_type == 'biomass_swap':
            processes = 18
        else:
            processes = 22   # 50 processors > 740 GB peak; 25 = >740 GB peak; 15 = 490 GB peak; 20 = 590 GB peak; 22 = 710 GB peak
    else:
        processes = 2
    uu.print_log('Gross removals max processors=', processes)
    pool = multiprocessing.Pool(processes)
    pool.map(partial(gross_removals_all_forest_types.gross_removals_all_forest_types, output_pattern_list=output_pattern_list,
                     sensit_type=sensit_type, no_upload=no_upload), tile_id_list)
    pool.close()
    pool.join()

    # # For single processor use
    # for tile_id in tile_id_list:
    #     gross_removals_all_forest_types.gross_removals_all_forest_types(tile_id, output_pattern_list, sensit_type, no_upload)

    # Checks the gross removals outputs for tiles with no data
    for output_pattern in output_pattern_list:
        if cn.count <= 2:  # For local tests
            processes = 1
            uu.print_log("Checking for empty tiles of {0} pattern with {1} processors using light function...".format(
                output_pattern, processes))
            pool = multiprocessing.Pool(processes)
            pool.map(partial(uu.check_and_delete_if_empty_light, output_pattern=output_pattern), tile_id_list)
            pool.close()
            pool.join()
        else:
            processes = 55  # 55 processors = 670 GB peak
            uu.print_log(
                "Checking for empty tiles of {0} pattern with {1} processors...".format(output_pattern, processes))
            pool = multiprocessing.Pool(processes)
            pool.map(partial(uu.check_and_delete_if_empty, output_pattern=output_pattern), tile_id_list)
            pool.close()
            pool.join()

    # If no_upload flag is not activated, output is uploaded
    if not no_upload:

        for i in range(0, len(output_dir_list)):
            uu.upload_final_set(output_dir_list[i], output_pattern_list[i])


if __name__ == '__main__':

    # The arguments for what kind of model run is being run (standard conditions or a sensitivity analysis) and
    # the tiles to include
    parser = argparse.ArgumentParser(
        description='Create tiles of the annual AGB and BGB gain rates for mangrove forests')
    parser.add_argument('--model-type', '-t', required=True,
                        help='{}'.format(cn.model_type_arg_help))
    parser.add_argument('--tile_id_list', '-l', required=True,
                        help='List of tile ids to use in the model. Should be of form 00N_110E or 00N_110E,00N_120E or all.')
    parser.add_argument('--run-date', '-d', required=False,
                        help='Date of run. Must be format YYYYMMDD.')
    parser.add_argument('--no-upload', '-nu', action='store_true',
                       help='Disables uploading of outputs to s3')
    args = parser.parse_args()
    sensit_type = args.model_type
    tile_id_list = args.tile_id_list
    run_date = args.run_date
    no_upload = args.no_upload

    # Disables upload to s3 if no AWS credentials are found in environment
    if not uu.check_aws_creds():
        no_upload = True
        uu.print_log("s3 credentials not found. Uploading to s3 disabled.")

    # Create the output log
    uu.initiate_log(tile_id_list=tile_id_list, sensit_type=sensit_type, run_date=run_date, no_upload=no_upload)

    # Checks whether the sensitivity analysis and tile_id_list arguments are valid
    uu.check_sensit_type(sensit_type)
    tile_id_list = uu.tile_id_list_check(tile_id_list)

    mp_gross_removals_all_forest_types(sensit_type=sensit_type, tile_id_list=tile_id_list, run_date=run_date, no_upload=no_upload)