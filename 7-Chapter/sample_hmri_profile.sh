#!/bin/bash
# sample metrics from synth surface across cortical profile
# requires a freesurfer-like directory tree (i.e. $sessDir/surf/lh.synth_white)
# the identity.dat file is a identity matrix as metric image and surface should already be in the same space

# root directory
dataDir=/path/to/all/data/

# inputs
metric=$1	# metric/map filename to sample (e.g. R1/MT/NDI)
sessDir=$2      # this should be the directory where the anatomical data is - e.g. /path/to/all/data/s001/anat/s001_7T_MR1
metricName=$3   # used to name output for brevity

# split session dir to get source subject (e.g. s001_7T_MR1) and subject dir (e.g. /path/to/all/data/s001/anat)
srcSubj=`basename ${sessDir}`
subjDir=`dirname ${sessDir}`

# set vars to loop through
hemis=(lh rh)
distances=(1 0.5 0 -0.5 -1 -1.5 -2)

# sample metric values at each distance from synthseg WM surface
for ihemi in ${hemis[@]}; do
  for idist in ${distances[@]}; do
    mri_vol2surf --src ${metric} --srcreg ${dataDir}/identity.dat --srcsubject ${srcSubj} --hemi ${ihemi} --surf synth_white --sd ${subjDir} --projdist ${idist} --o ${sessDir}/surf/${ihemi}.${metricName}_profile${idist}mm.mgz
  done
done
