#!/bin/bash
# Create group specific population in freesurfer - does 2 rounds to refine.
# this is mainly taken from freesurfer wiki https://surfer.nmr.mgh.harvard.edu/fswiki/SurfaceRegAndTemplates#Creatingaregistrationtemplatefromscratch.28GW.29
# with ~60 participants I've found this may take 1-2 days

subj_list=$1					# .txt file with list of subject freesufer folders - each on a new line (don't include rootpath).
subj_dir=$2						# directory where subject freesurfer subfolders are (stated above in subj_list).
template_name=$3     	# output directory created in subj_dir with average subject (don't include rootpath).

# convert subject list into array
mapfile -t subjs < ${subj_list}

# initialise group template - uses fsaverage to start it off
make_average_subject --out ${template_name} --subjects ${subjs[@]} --sdir ${subj_dir}

# create hemi array for looping through
hemis=(lh rh)

# register each participant to the initialised group template
# this will create a new registration file for each participants' surfaces in the group template space (surf/${ihemi}.sphere.reg.${template_name})
for isubj in ${subjs[@]}; do
echo "------- Registering ${isubj} ---------"
cd ${subj_dir}/${isubj}
	for ihemi in ${hemis[@]}; do
		mris_register -curv surf/${ihemi}.sphere ${subj_dir}/${template_name}/${ihemi}.reg.template.tif surf/${ihemi}.sphere.reg.${template_name}
	done
done

# changed current working directory back to subjdir (freesurfer wiki tends to cd-around for registrations so don't want to mess with it)
cd ${subj_dir}

# create a final group template using the initialised template (above) as the starting point
# this should create a more refined template as it is starting in a position closer to the final template (via registration loop above)
make_average_subject --out ${template_name}_final --surf-reg sphere.reg.${template_name} --subjects ${subjs[@]} --sdir ${subj_dir}

# cleanup first template?

# register all subjects to final template
for isubj in ${subjs[@]}; do
echo "------- Registering ${isubj} ---------"
cd ${subj_dir}/${isubj}
        for ihemi in ${hemis[@]}; do
                mris_register -curv surf/${ihemi}.sphere ${subj_dir}/${template_name}_final/${ihemi}.reg.template.tif surf/${ihemi}.sphere.reg.${template_name}_final
        done
done
