
"""
Generate fsgd file needed for glm analysis in freesurfer.
This is still a work in progress and hasn't been tested on all types of statistical designs.
It works best with simple designs (e.g. 1-2 groups and 1 variable).

Author: Tom Veale (tom.veale@ucl.ac.uk)

"""

import os
import pandas as pd
from argparse import ArgumentParser, RawDescriptionHelpFormatter

# Arguments
__description__ = '''
Script generates an FSGD file to be used in GLM analysis with FreeSurfer.
See https://surfer.nmr.mgh.harvard.edu/fswiki/FsgdFormat for more details on the FSGD files.
'''

parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                        description=__description__)

parser.add_argument('--input_csv',
                    help='CSV file with group demographics',
                    type=str,
                    required=True)
parser.add_argument('--title',
                    help='Title that is input into FSGD file (for display only) (e.g. THICKvsAge)',
                    type=str,
                    required=True)
parser.add_argument('--subj_col',
                    help='Column in input_csv with participant identifiers (e.g. PARTICIPANT)',
                    type=str,
                    required=True)
parser.add_argument('--groups',
                    help='Column(s) in input_csv with grouping variables and depends on desired design matrix.'
                         'With 1 grouping variable, name this column in the input_csv (e.g. DIAGNOSIS).'
                         'With > 1 grouping variable, name these columns in input_csv (i.e. DIAGNOSIS SEX).',
                    nargs='+',
                    type=str,
                    required=True)
parser.add_argument('--variables',
                    help='Column(s) in input_csv with continuous variables and depends on desired design matrix.'
                         'E.g. with 1 continuous variable, name this column in the input_csv (e.g. AGE).'
                         'E.g. with > 1 continuous variable, name these columns in input_csv (i.e. AGE WEIGHT).',
                    nargs='+',
                    type=str,
                    required=True)
parser.add_argument('--out_fsgd',
                    help='Filename (including path) to resulting FSGD file (e.g. /users/me/data/glm/thick_age.fsgd)',
                    type=str,
                    required=True)

# Parse arguments and set up paths
args = parser.parse_args()

# import csv with demographics to build fsgd file
csv_df = pd.read_csv(args.input_csv)

# determine classes
if len(args.groups) == 0:
    raise Exception('No Groups Specified!')
elif len(args.groups) == 1:
    fsgd_classes = args.groups[0]
elif len(args.groups) > 1:
    csv_df['CLASS_COMBINED'] = csv_df[args.groups[0]].str.cat(csv_df[args.groups[1:]], sep='')
    fsgd_classes = 'CLASS_COMBINED'
    # automated way to combine multiple groups for classes - may want to specify order of these down the line
    fsgd_class_levels = csv_df['CLASS_COMBINED'].sort_values().unique()

# first make variable columns all strings to concat later
csv_df[args.variables] = csv_df[args.variables].astype(str)

# determine variables
if len(args.variables) == 0:
    raise Exception('No Variables Specified!')
elif len(args.variables) == 1:
    fsgd_variables = args.variables[0]
elif len(args.variables) > 1:
    csv_df['VARS_COMBINED'] = csv_df[args.variables[0]].str.cat(csv_df[args.variables[1:]], sep=' ')
    fsgd_variables = 'VARS_COMBINED'

# write to file
with open(args.out_fsgd, 'w') as fsgd:
    # write header info
    fsgd.write('GroupDescriptorFile 1 \n')
    fsgd.write('Title   ' + args.title + '\n')

    # write each class (grouping variable)
    # WORK ON COMBINING CLASSES
    if len(args.groups) == 1:
        for iclass in args.groups:
            fsgd.write('Class   ' + iclass + '\n')
    elif len(args.groups) > 1:
        for iclass in fsgd_class_levels:
            fsgd.write('Class   ' + iclass + '\n')

    # write variables on one line
    fsgd.write('Variables   ' + '   '.join(args.variables) + '\n')

    # now write each participant info
    for isubj in range(0, csv_df.shape[0]):
        fsgd.write('Input   ' + csv_df.iloc[isubj][args.subj_col] + '    ' +
                   csv_df.iloc[isubj][fsgd_classes] + '    ' +
                   csv_df.iloc[isubj][fsgd_variables] + '    ' + '\n')
