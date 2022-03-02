# general file to concatenate many csv files into one spreadsheet
# this is a generalised version of code in extract_swm_stats_nipype.py

# load packages
import os
import pandas as pd
from argparse import ArgumentParser, RawDescriptionHelpFormatter

# get arguments
__description__ = '''
This script collates all csv's matching pattern and concatenates them into one long csv file.
Each csv file is indexed by their filename. Each filename's full path must be unique!
Tip: make each csv filename subject + measure specific and then clean the filename column afterwards to get those variables.
'''

# collect inputs
parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                        description=__description__)

parser.add_argument('-pd', '--parent_dir',
                    help='Path to the parent data directory csvs are located (BIDS preferred)')
parser.add_argument('-sd', '--sub_dir',
                    help='Only grab csv files that are in the specified subdirectory (i.e. \'dwi\').',
                    required=False)
parser.add_argument('-ew', '--ends_with',
                    help='Common string that all the csvs end with (e.g. \'roi_metrics.csv\'). Default is \'.csv\'',
                    required=False,
                    default='.csv')
parser.add_argument('-o', '--output',
                    help='Output csv file name with all data. Saved in parentdir.',
                    required=False,
                    default='all_csv_data.csv')
args = parser.parse_args()

# get list of csvs
dir_list = []
indir = os.path.abspath(args.parent_dir)

if args.sub_dir:
    print('Subdirectory defined - only extracting csv files under this subdirectory:' + str(args.sub_dir))
    for root, dirs, files in os.walk(indir):
        if args.sub_dir in root:
            for ifile in files:
                if ifile.endswith(str(args.ends_with)):
                    print(os.path.join(root, ifile))
                    dir_list.append(os.path.join(root, ifile))
else:
    print('Extracting all csv files under parent directory' + str(args.parent_dir))
    for root, dirs, files in os.walk(indir):
        for ifile in files:
            if ifile.endswith(str(args.ends_with)):
                print(os.path.join(root, ifile))
                dir_list.append(os.path.join(root, ifile))


# loop through and create nested dictionaries of dfs
csv_dict = {}
for icsv in dir_list:
    # read each file into a dataframe
    csv_dict[icsv] = pd.read_csv(icsv)
    # put the file name as a column in the data frame
    csv_dict[icsv]['Filename'] = icsv

# concatenate all files into one dataframe
csv_all = pd.concat(csv_dict.values(), ignore_index=True)

# save to output csv
csv_all.to_csv(os.path.join(args.parent_dir, args.output), index=False)
