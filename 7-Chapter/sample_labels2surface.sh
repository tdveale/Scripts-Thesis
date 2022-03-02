#!/bin/bash
# samples labels from atlas onto participant surfaces
# this is essentially the same as sample_hmri_profile.sh but put into a different script for clarity - only samples on the GM/WM boundary (projdist=0)
# requires a freesurfer-like directory tree (i.e. $sessDir/surf/lh.synth_white)
# identity.dat is an identity matrix file as labels and surface should be in the same space already

# root directory
dataDir=/path/to/all/data/

# inputs
label=$1	# atlas labels in participant native space to sample to surface
sessDir=$2      # this should be where the anatomical data is - e.g. /path/to/all/data/s001/anat/s001_7T_MR1

# split session dir to get source subject (e.g. s001_7T_MR1) and subject dir (e.g. /path/to/all/data/s001/anat)
srcSubj=`basename ${sessDir}`
subjDir=`dirname ${sessDir}`

# set vars to loop through
hemis=(lh rh)

# sample label values at each distance from synthseg WM surface
for ihemi in ${hemis[@]}; do
  mri_vol2surf --src ${label} --srcreg ${dataDir}/identity.dat --srcsubject ${srcSubj} --hemi ${ihemi} --surf synth_white --sd ${subjDir} --projdist 0 --o ${sessDir}/surf/${ihemi}.HOCP_labels_annot.mgz
done
