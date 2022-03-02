#!/bin/bash
# Create GM/WM surface from synthseg output https://github.com/BBillot/SynthSeg
# Could be improved with other FreeSurfer commands (e.g. topology correction)

# Input and output parameters
SynthSeg=$1	# Synthseg output
OutDir=$2	# output directory for surfaces - should already exist

# create binary mask of left and right hemis
fslmaths ${SynthSeg} -thr 1 -uthr 2 -bin ${SynthSeg%.nii.gz}_lh_wm_mask.nii.gz
fslmaths ${SynthSeg} -thr 40 -uthr 41 -bin ${SynthSeg%.nii.gz}_rh_wm_mask.nii.gz

# tesselate each WM mask
mri_tessellate ${SynthSeg%.nii.gz}_lh_wm_mask.nii.gz 1 ${OutDir}/lh.tess
mri_tessellate ${SynthSeg%.nii.gz}_rh_wm_mask.nii.gz 1 ${OutDir}/rh.tess

# smooth each surfacce
mris_smooth ${OutDir}/lh.tess ${OutDir}/lh.synth_white
mris_smooth ${OutDir}/rh.tess ${OutDir}/rh.synth_white
