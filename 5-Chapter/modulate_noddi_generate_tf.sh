#!/bin/bash
# Calculates NDI and ODI images that are modulated by 1-iso (i.e. tissue-fraction).
# These can then be taken into ROI analysis to create tissue weighted averages
# see https://github.com/tdveale/TissueWeightedMean for more details

iso=$1
ndi=$2
odi=$3
mask=$4

# if iso file exists
if [ -e "${iso}" ]; then
  # calculate 1-Viso (tissue fraction)
  fslmaths ${iso} -mul -1 -add 1 -mas ${mask} ${iso%.nii.gz}_TF.nii.gz
  # multiply by ndi
  fslmaths ${iso%.nii.gz}_TF.nii.gz -mul ${ndi} ${ndi%.nii.gz}_modulated.nii.gz
  ls ${ndi%.nii.gz}_modulated.nii.gz
  # multiply by odi
  fslmaths ${iso%.nii.gz}_TF.nii.gz -mul ${odi} ${odi%.nii.gz}_modulated.nii.gz
  ls ${odi%.nii.gz}_modulated.nii.gz
else
  echo "ISO IMAGE NOT FOUND"
fi
