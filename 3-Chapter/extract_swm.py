# This pipeline takes the dwi maps (FA/MD etc from DTI or NDI/ODI from NODDI) and FreeSurfer outputs and extracts
# metrics from various distances from the GM/WM boundary
#
# Need env-niftypipe virtual environment

# import nipype modules
import os  # system functions
import glob
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from itertools import chain  # flattens lists
from nibabel import freesurfer as nfs
import numpy as np
from collections import OrderedDict
import pandas as pd
from nipype import Workflow, Node
from nipype.interfaces.io import DataSink
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.niftyreg as reg


# Arguments
__description__ = '''
This script uses freesurfer outputs and diffusion MRI maps and extracts ROI metrics at various distances from the
WM surface. Main output is a csv file with average and standard deviations of specified ROIs at various distances.
'''

# collect inputs
parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                        description=__description__)

parser.add_argument('-f', '--fsdir',
                    help='Path to freesurfer output (e.g. ~/sub-01-001/freesurfer_6_t2)',
                    required=True)
parser.add_argument('-m', '--metric',
                    help='Input metric (e.g. NODDI map) (i.e. ~/sub-01-001/diffusion/NDI.nii.gz)',
                    required=True)
parser.add_argument('-mr', '--metric_reg',
                    help='Image to guide registration from metric -> freesurfer T1 (e.g. b0 or NODDI isotropic map) '
                         '(e.g. ~/sub-01-001/diffusion/ISO.nii.gz)',
                    required=True)
parser.add_argument('-rmask', '--reference_mask',
                    help='Mask for the reference space during registration. Helpful if registering images with noisy'
                         'backgrounds like MPMs (e.g. ~/sub-01-001/gif/TIVgifMask-to-FST1.nii.gz',
                    required=False)
parser.add_argument('-d', '--distances',
                    help='Millimetres away from the WM surface to sample from. Positive = above, negative = below.'
                         'e.g. 1 0 -1 -2',
                    required=True,
                    type=int,
                    nargs='+')
parser.add_argument('-tp', '--template',
                    help='Common template for sampled metrics to be registered to for vertex-wise analysis '
                         '(e.g. fsaverage). Output surface smoothed at 5mm fwhm. This is done in addition to individual'
                         'space sampling.',
                    required=False)
parser.add_argument('-hm', '--hemis',
                    help='Hemispheres to sample from (e.g. lh rh). Default is both hemispheres.',
                    required=False,
                    nargs='+',
                    default=['lh', 'rh'])
parser.add_argument('-r', '--rois',
                    help='FreeSurfer ROI to extract measures for (i.e. precuneus, middletemporal, parahippocampal). '
                         'If none specified, all cortical FreeSurfer ROIs will be extracted.',
                    required=False,
                    nargs='+')
parser.add_argument('-o', '--out_dir',
                    help='Output directory to put csv file with all data.',
                    required=True)
args = parser.parse_args()

# if output directory doesn't exist - create it
if not os.path.exists(args.out_dir):
    os.makedirs(args.out_dir)

# Create DataSink node
swm_sinker = Node(DataSink(), name='swm_sinker')
swm_sinker.inputs.base_directory = os.path.join(os.path.abspath(args.out_dir), 'swm_output')

# set up workflow
wf = Workflow(name='extract_swm', base_dir=args.out_dir)

# convert T1.mgz to T1.nii
subj_t1 = os.path.join(os.path.abspath(args.fsdir), 'mri/T1.mgz')
subj_t1_root = subj_t1.split('.')[0]
t1_convert = Node(fs.MRIConvert(in_file=subj_t1,
                                out_file=subj_t1_root + '.nii',
                                out_type='nii'),
                  name='MRIConvert')

if args.reference_mask:
    # register iso metric into T1 FS space
    metric_reg_root = os.path.basename(args.metric_reg).split('.')[0]
    dwi2fst1_reg = Node(reg.RegAladin(ref_file=subj_t1,
                                      flo_file=os.path.abspath(args.metric_reg),
                                      aff_file=metric_reg_root + '_to_fsT1.txt',
                                      rmask_file=os.path.abspath(args.reference_mask)),
                        name='reg_aladin')
else:
    # register iso metric into T1 FS space
    metric_reg_root = os.path.basename(args.metric_reg).split('.')[0]
    dwi2fst1_reg = Node(reg.RegAladin(ref_file=subj_t1,
                                      flo_file=os.path.abspath(args.metric_reg),
                                      aff_file=metric_reg_root + '_to_fsT1.txt'),
                        name='reg_aladin')

# resample dwi metric into T1 FS space
dwi2fst1_res = Node(reg.RegResample(ref_file=subj_t1,
                                    flo_file=os.path.abspath(args.metric)),
                    name='reg_resample')

# connect convert, registration and resampling nodes together

# output of convert goes to registration
wf.connect([(t1_convert, dwi2fst1_reg,
             [('out_file', 'ref_file')])])
# output of convert goes to resample
wf.connect([(t1_convert, dwi2fst1_res,
             [('out_file', 'ref_file')])])
# transformation from registration goes to resample
wf.connect([(dwi2fst1_reg, dwi2fst1_res,
             [('aff_file', 'trans_file')])])

# option for gyral coordinate system here

# Need to create a dummy.dat file as registration from dwi -> FS T1 already complete above (identity matrix)
fs_dir_end = os.path.abspath(args.fsdir).split('/')[-1]
dummy_reg_file = os.path.join(os.path.abspath(args.out_dir), 'identity_dw2fsT1.dat')
with open(dummy_reg_file, 'w') as dummy_file:
    dummy_file.write(fs_dir_end + '\n')
    dummy_file.write('1.000000' + '\n')
    dummy_file.write('1.000000' + '\n')
    dummy_file.write('0.150000' + '\n')
    dummy_file.write('1.0 0.0 0.0 0.0' + '\n')
    dummy_file.write('0.0 1.0 0.0 0.0' + '\n')
    dummy_file.write('0.0 0.0 1.0 0.0' + '\n')
    dummy_file.write('0 0 0 1' + '\n')
    dummy_file.write('round' + '\n')
    dummy_file.write('\n')

# Build the sampler interface - samples specified mms from the GM/WM boundary
subj_dwi_file = os.path.basename(args.metric).split('.')[0]
sampler = Node(fs.SampleToSurface(subjects_dir=os.path.dirname(os.path.abspath(args.fsdir)),  # this is a horrible hacky way - fix this
                                  reg_file=dummy_reg_file,
                                  sampling_method='point',
                                  sampling_units='mm',
                                  surface='white',
                                  out_file=subj_dwi_file + '_swm_sampled.mgz'),
               name='mri_vol2surf')

sampler.iterables = [('hemi', args.hemis),
                     ('sampling_range', args.distances)]

wf.connect([(dwi2fst1_res, sampler,
             [('out_file', 'source_file')])])
wf.connect([(sampler, swm_sinker,
             [('out_file', 'swm_sampled')])])

wf.run('MultiProc', plugin_args={'n_procs': 4})

# if common space template specified - run the sampler interface again but sample to specified template (i.e. fsaverage)
if args.template:

    # already done registration at this point - pull resample metric image to go directly into sampler
    resampled_metric = glob.glob(os.path.join(os.path.abspath(args.out_dir), 'extract_swm', 'reg_resample',
                                              '*_res.nii.gz'))[0]
    sampler_template = Node(fs.SampleToSurface(subjects_dir=os.path.dirname(os.path.abspath(args.fsdir)),
                                               source_file=resampled_metric,
                                               reg_file=dummy_reg_file,
                                               sampling_method='point',
                                               sampling_units='mm',
                                               surface='white',
                                               target_subject=args.template,
                                               smooth_surf=5.0,
                                               out_file=subj_dwi_file + '_swm_sampled_template.mgz'),
                            name='mri_vol2surf_template')

    sampler_template.iterables = [('hemi', args.hemis),
                                  ('sampling_range', args.distances)]

    # Create new DataSink node
    swm_tp_sinker = Node(DataSink(), name='swm_tp_sinker')
    swm_tp_sinker.inputs.base_directory = os.path.join(os.path.abspath(args.out_dir), 'swm_output_template')

    # set up workflow
    wf_template = Workflow(name='extract_swm_template', base_dir=args.out_dir)

    # connect the resampled metric image to sampler in new workflow
    wf_template.connect([(sampler_template, swm_tp_sinker,
                          [('out_file', 'swm_sampled_template')])])

    # run workflow
    wf_template.run('MultiProc', plugin_args={'n_procs': 4})

### extract ROIs using nibabel for native ROIs

hemi_list = []
swm_dict = {}

for i_hemi in args.hemis:
    # get ROIs from Desikan-Killiany Atlas
    annot_data = nfs.read_annot(os.path.join(os.path.abspath(args.fsdir), 'label/' + i_hemi + '.aparc.annot'))

    # find indices of rois (label values) - use all rois if none specified
    if not args.rois:
        rois = annot_data[2]
    else:
        rois = args.rois
    indx = [np.where(np.array(annot_data[2]) == i)[0][0] for i in rois]

    dist_list = []
    swm_dict[i_hemi] = {}
    for i_distance in args.distances:
        # construct file path from sampler parameters
        i_file = os.path.join(args.out_dir, wf.name,
                              '_hemi_' + i_hemi +
                              '_sampling_range_' + str(i_distance),
                              sampler.name,
                              sampler.inputs.out_file)
        print(i_file)
        # load dwi data sampled at distance in sampler node. Then get data into a reasonable format (vector)
        swm_obj = nfs.mghformat.load(i_file)  # datasink instead
        swm_data = swm_obj.get_data()
        swm_data = swm_data.flatten()

        # add data to dictionary
        swm_dict[i_hemi][i_distance] = swm_data

        # create masks for each ROI
        roi_dict = {}
        for i in range(0, len(rois)):
            roi_dict[rois[i]] = {}
            roi_dict[rois[i]]['roi_index'] = indx[i]
            roi_dict[rois[i]]['mask'] = (annot_data[0] == indx[i])

        # index vertices from dwi swm data for each roi (from gyri/sulci code)
        roi_list = []
        for i_roi, i_gws in roi_dict.iteritems():
            i_data = swm_dict[i_hemi][i_distance]
            i_dict = OrderedDict()
            i_dict['Hemi'] = i_hemi
            i_dict['Distance'] = i_distance
            i_dict['Region'] = i_roi
            # Get mean and standard deviations of current ROI
            i_dict['DWI_Avg'] = np.mean(i_data[roi_dict[i_roi]['mask']])
            i_dict['DWI_Std'] = np.std(i_data[roi_dict[i_roi]['mask']])
            # append this ROI dictionary to list
            roi_list.append(i_dict)

        # append dfs for different distances
        dist_list.append(roi_list)

    # turn distance list to df (chain flattens nested list of dicts in order to create df)
    dist_df = pd.DataFrame(list(chain.from_iterable(dist_list)))
    # append dfs for both hemispheres
    hemi_list.append(dist_df)

# concatenate hemisphere dfs
final_swm_data = pd.concat([hemi_list[0], hemi_list[1]])

# output csv for ROIs
output_csv = subj_dwi_file + '_swm_roi_metrics.csv'
final_swm_data.to_csv(os.path.join(os.path.abspath(swm_sinker.inputs.base_directory), output_csv), index=False)


# write graph out - this no longer works on linux - need graphviz stuff installed - install in niftypipe venv?
# wf.write_graph('graph.dot')
