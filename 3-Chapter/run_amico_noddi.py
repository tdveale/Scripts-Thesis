#!/usr/bin/env python


from argparse import ArgumentParser, RawDescriptionHelpFormatter
import amico
import spams

# Arguments
__description__ = '''
This script fits the NODDI model using AMICO (Accelerated Microstructural Imaging via Convex Optimisation).
Must be run in an environment with spams (requires new-ish gcc like 7.4) and amico modules.
This is a simple script that essentially wraps around the tutorial/demo from here: 
https://github.com/daducci/AMICO

Author: Tom Veale (tom.veale@ucl.ac.uk)
'''

# collect inputs
parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                        description=__description__)

parser.add_argument('-xd', '--experiment_dir',
                    help='Directory where subject directories are (e.g. /data/experiment_1/).',
                    required=True)
parser.add_argument('-sd', '--subject_dir',
                    help='Directory where the subject diffusion data is (e.g. sub-01-001/dwi_preprocessed/).',
                    required=True)
parser.add_argument('-i', '--dwi',
                    help='Preprocessed diffusion weighted images (e.g. motion, eddy, susceptibility corrected).',
                    required=True)
parser.add_argument('-m', '--mask',
                    help='Binary mask for the diffusion weighted images, must be in diffusion space.',
                    required=True)
parser.add_argument('-ba', '--bval',
                    help='File with bvalues in (.bval). MUST BE FULL PATH',
                    required=True)
parser.add_argument('-be', '--bvec',
                    help='File with bvecs in (.bvec). MUST BE FULL PATH',
                    required=True)
parser.add_argument('-b0', '--b0_threshold',
                    help='Threshold for b0s (e.g. if b0s are set to 5 and not 0 in bvals, set this to 5). Default=0',
                    type=int,
                    default=0,
                    required=False)

args = parser.parse_args()

amico.core.setup()

# give amico directory structure
ae = amico.Evaluation(args.experiment_dir, args.subject_dir)

# generate scheme file if don't already have one
scheme = amico.util.fsl2scheme(args.bval, args.bvec)

# load data
ae.load_data(dwi_filename=args.dwi,
             scheme_filename=scheme,
             mask_filename=args.mask,
             b0_thr=args.b0_threshold)

# set model
ae.set_model('NODDI')

# generate kernels
ae.generate_kernels()

# Note that you need to compute the response functions only once per study;
# in fact, scheme files with same b-values but different number/distribution of samples on each shell
# will result in the same precomputed kernels (which are actually computed at higher angular resolution).
# The function generate_kernels() does not recompute the kernels if they already exist,
# unless the flag regenerate is set, e.g. generate_kernels( regenerate = True ).

# Load the precomputed kernels (at higher resolution) and adapt them to the actual scheme
# (distribution of points on each shell) of the current subject:
ae.load_kernels()

# fit model
ae.fit()

# save results as nifti
ae.save_results()
