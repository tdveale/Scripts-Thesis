# this takes a file with many roi labels (i.e. GIF) and extracts underlying ROI measures from nifti image
# useful if you want to collect ROI measures from all ROIs without splitting the file into separate ROI files
# two files MUST BE IN SAME SPACE BEFOREHAND

# load packages
import numpy as np
import nibabel as nb
import pandas as pd
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from collections import OrderedDict
import os
import warnings

__description__ = '''
This script extracts either descriptive statistics (mean,sd, sum, min, max) or volume from all regions of interest (ROI)
of specified file and outputs a csv.

Author: Tom Veale
Email: tom.veale@ucl.ac.uk
'''

# collect inputs
parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                        description=__description__)

parser.add_argument('-i', '--input_image',
                    help='Input nifti file to take ROI measures from (e.g. FA/MD/MT/T1 image).',
                    required=True)
parser.add_argument('-r', '--input_rois',
                    help='Input nifti file with all ROIs labelled as unique integers (e.g. GIF labels image).',
                    required=True)
parser.add_argument('-m', '--output_metric',
                    help='Output metric to be calculated. Specify \'descriptive\' or \'volume\' outputs.'
                         'Default is descriptive.',
                    required=False,
                    default="descriptive",
                    type=str)
parser.add_argument('-p', '--probability',
                    help='The input image is a tissue probability map where each voxel ranges from 0.0-1.0 '
                         'representing the probability of that voxel belonging to that class. If this is chosen volume '
                         'probabilities will also be calculated. NOT YET IMPLEMENTED.',
                    required=False,
                    action='store_true')
parser.add_argument('-o', '--out_file',
                    help='Output csv file (including path) containing ROI metrics. '
                         'Default path is in input_rois directory with the metric filename as a basename',
                    required=False)
args = parser.parse_args()

# check output is mean or volume
if args.output_metric not in ["descriptive", "volume"]:
    raise ValueError("Output metric must be \'descriptive\' or \'volume\'")

# if no output file specified, append rois to input metric file for filename
if not args.out_file:
    args.out_file = os.path.join(os.path.dirname(args.input_rois),
                                 os.path.basename(args.input_image.split('.')[0])) + '_rois.csv'

# load in metric file (e.g. diffusion metric, MPM, T1 whatever)
metric_img = nb.load(args.input_image)
metric_data = metric_img.get_fdata()

# load in label file (e.g. file with labels for each ROI such as GIF labels/freesurfer rois)
roi_img = nb.load(args.input_rois)
roi_data = roi_img.get_fdata()

# loop through each label value and extract mean and SD of underlying metrics
# get unique label values in roi_data
roi_vals = np.unique(roi_data).astype(int)

# initiate roi list
roi_list = []

# if using descriptive
if args.output_metric == "descriptive":
    # for each label in roi_data - extract mean and sd
    for i_roi in roi_vals:
        # create dict
        i_dict = OrderedDict()
        i_dict['Filename'] = args.input_image
        i_dict['ROI_Value'] = i_roi
        # extract mean
        i_dict['Mean'] = np.mean(metric_data[roi_data == i_roi])
        # extract std
        i_dict['SD'] = np.std(metric_data[roi_data == i_roi])
        # extract sum of metric in ROI
        i_dict['Sum'] = np.sum(metric_data[roi_data == i_roi])
        # extract min of metric in ROI
        i_dict['Min'] = np.min(metric_data[roi_data == i_roi])
        # extract max of metric in ROI
        i_dict['Max'] = np.max(metric_data[roi_data == i_roi])
        # extract median of metric in ROI
        i_dict['Median'] = np.median(metric_data[roi_data == i_roi])
        # extract lower and upper quartile for inter-quartile range
        i_dict['q25'], i_dict['q75'] = np.percentile(metric_data[roi_data == i_roi], [25, 75])
        # append dict to list
        roi_list.append(i_dict)

# if using volume
elif args.output_metric == "volume":
    # get image dimensions
    # inspired by nibabel package
    # https://github.com/nipy/nibabel/blob/master/nibabel/imagestats.py
    voxel_volume_mm3 = np.prod(metric_img.header.get_zooms()[:3])

    if voxel_volume_mm3 != 1:
        warnings.warn('Voxel dimensions are ' + str(voxel_volume_mm3) + "mm", UserWarning)

    # for each label in roi_data - extract volume
    for i_roi in roi_vals:
        # create dict
        i_dict = OrderedDict()
        i_dict['Filename'] = args.input_image
        i_dict['ROI_Value'] = i_roi
        # extract volume
        # this is sum of voxels within the mask multiplied by the voxel dimensions
        i_dict['Volume_Cat'] = np.sum(roi_data == i_roi) * voxel_volume_mm3
        # for weighted average - not yet implemented
        # if args.probability:
            # weighted average - where tissue probability are the weights. element-wise: weights * vol / sum(weights)
            # need to check this is right
            #i_dict['Volume_Prob'] = (np.multiply(metric_data[roi_data == i_roi], roi_data == i_roi) / np.sum(metric_data[roi_data == i_roi])
        # append dict to list
        roi_list.append(i_dict)



# convert list of dicts to data frame
roi_df = pd.DataFrame(roi_list)
# output to csv
roi_df.to_csv(args.out_file, index=False)
print('Saved metric csv file to: ', args.out_file)
