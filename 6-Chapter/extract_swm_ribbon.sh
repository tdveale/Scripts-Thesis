#!/bin/bash
# Run SWM ribbon extraction
# Use FreeSurfer commands to extract SWM region between WM surface and 2mm below the WM surface

# set data directory
dataDir=/path/to/all/data

# set hemispheres to loop over
hemis=(lh rh)

# loop through each FAD participant and session - create swm ribbon
# this is currently hard coded for a certain directory structure (BIDS-like) 
for isess in ${dataDir}/FAD-00*/sess-v*; do

 # if DWI and FreeSurfer data exists
 if [ -e "${isess}/dwi/noddi/AMICO/" ] && [ -e ${isess}/anat/freesurfer_6_* ]; then

  # extract freesurfer names
  freesurferDir=`ls -d ${isess}/anat/freesurfer_6_*`
  fsSubjID=`basename ${freesurferDir}`

  # for each hemisphere, expand 2mm below GM/WM
  for ihemi in ${hemis[@]}; do
    mris_expand ${freesurferDir}/surf/${ihemi}.white -2 ${freesurferDir}/surf/${ihemi}.swm-2mm-surf
  done

  # fill in the GM/WM -> 2mm SWM surfaces to get SWM ribbon
  # the pial surface is now the white surface, the white surface is now the -2mm SWM boundary
  mris_volmask --surf_pial white --surf_white swm-2mm-surf --out_root swm-ribbon --save_ribbon --save_distance --sd ${isess}/anat/ ${fsSubjID}

 fi
done
