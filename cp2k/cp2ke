#!/bin/bash
#******************************************************#
#                                                      #
#               Script for running CP2K                #
#     Intended to work with the SLURM queue system     #
#      within the Constance/Deception HPC systems      #
#                                                      #
#        Benjamin Jackson, Auburn University           #
#                 baj0040@auburn.edu                   #
#                                                      #
#                Updated: 08/18/2022                   #
#                                                      #
#******************************************************#
Main(){
	FNAME=$(echo ${!#} | awk -F. '{print $1}')
	##Defaults:
	TIME=8-00:00:00
	QTYPE=g
	NODES=1
	THREADS=1
	EDIT_TIME=true #true will edit inp file to ensure WALLTIME in input agrees with the job submission, false null 
	EDIT_INPUT_PROJECT=true #true will edit the project name to always match the input name
#	                        #to work you must format your project name using "@set FNAME Project_Name"
	ALT_ERROR_LOCATION=false
	##Default paths:
	NOVA_MODULES="module -q load nova/modules cp2k/9.1"
	GENBIG_MODULES="module -q load intel/2021.1 cp2k/9.1"
	WRKDIR=$(pwd)
	SCRDIR=/scratch/$(whoami)/${FNAME}
	#if [[ ! -d ${SCRDIR} ]]; then mkdir -p ${SCRDIR}; fi

	#Begin Program
	SCRIPT_PATH=$( dirname "$(readlink -f "$0")" )
	if [[ "$#" -lt 1 ]]; then Helpfn; exit; fi
	Option_Handler "$@";
	if [[ ! -e ${FNAME}.inp ]]; then echo "Input file was not found"; exit 30; fi
	if [[ -z ${JOBNAME} ]]; then JOBNAME=${FNAME}; fi;
	if [[ ${EDIT_INPUT_PROJECT} = true ]]; then Edit_Input_Project; fi
	if [[ ${ALT_ERROR_LOCATION} = true ]]; then
		SUBDIR=/people/$(whoami)/.subfiles;	mkdir -p ${SUBDIR}; else SUBDIR=${WRKDIR};	fi
	Time_Converter;
  Queue_Set;
	Resources_Check;
	#Maint_Check;
	Batch_Builder;
	if [[ ${STOP_MARKER} = 1 ]]; then 
		if [[  ${SUBDIR} = ${WRKDIR} ]]; then exit;
		else mv ${SUBDIR}/${FNAME}.batch ${WRKDIR}/; exit; fi
	fi
	sbatch ${SUBDIR}/${FNAME}.batch
	rm -f ${SUBDIR}/${FNAME}.batch
}
Option_Handler(){
	while getopts ":ghen:c:m:t:q:p:rh:" option; do
		case $option in
			h) Helpfn; exit;;          #Call help function and exit
			n) NODES_SET=$OPTARG;;     #Number of Nodes
			c) NPROC_SET=$OPTARG;;     #Number of processors, not yet implemented fully
			r) RESTART_OPT="true";;
			m) MEM=$( echo $OPTARG | sed 's/GB//' );; #Memory Request
			t) TIME=$OPTARG;;          #HOUR:MINUTES
			q) QTYPE=$OPTARG;;         #Define the partition 
			h) THREADS=$OPTARG;;       #Define the number of threads
			g) STOP_MARKER=1;;		     #Create batch file then exit; do not start job
			e) EMAIL_MARKER=1;;        #Used to trigger email notifications
		esac
	done
}
Edit_Input_Project(){
	PROJECT_VAR_STR=$(grep -oE '@set FNAME .+' ${FNAME}.inp)
	PROJECT_STR=$(grep -oE "PROJECT .+" ${FNAME}.inp)
	if [[ -n ${PROJECT_VAR_STR} ]]; then
		sed -i "s/${PROJECT_VAR_STR}/@set FNAME ${FNAME}/" ${FNAME}.inp
	elif [[ -n ${PROJECT_STR} ]]; then
		sed -i "s/${PROJECT_STR}/PROJECT ${FNAME}/" ${FNAME}.inp
	fi
}
Queue_Set(){
	QTYPE=$( echo $QTYPE | awk '{print tolower($0)}' )
	case ${QTYPE} in
		[bB]2) NMAX=48; MEMMAX=384; QUEUE="bigmem2";;
		[rR][bB]2) NMAX=48; MEMMAX=384; QUEUE="ezm0048_bg2";;
		[bB]4) NMAX=48; MEMMAX=768; QUEUE="bigmem4";;
		[Aa]) NMAX=128; MEMMAX=256; QUEUE="amd";;
		[Gg][Pp][Uu]2) NMAX=48; MEMMAX=384; QUEUE="gpu2";;
		[Gg][Pp][Uu]4) NMAX=48; MEMMAX=768; QUEUE="gpu4";;
		[Rr]) NMAX=48; MEMMAX=192; QUEUE="ezm0048_std";;
		[nN]) NMAX=28; MEMMAX=125; QUEUE="nova";;
		*) NMAX=48; MEMMAX=192; QUEUE="general";;
	esac
}
Resources_Check(){
	if [[ -n ${NODES_SET} ]] && [[ -z ${NPROC_SET} ]]; then
		NODES=${NODES_SET}; TASK_PER_NODE=${NMAX}; NPROC=$(( ${NMAX} * ${NODES} ))  #Edit here for adding threading settings
	elif [[ -n ${NPROC_SET} ]]; then
		if [[ -z ${NODES_SET} ]] || [[ ${NODES_SET} = 1 ]]; then
			NPROC=${NPROC_SET}; TASK_PER_NODE=${NPROC_SET}; NODES=1 #Edit here for adding threading settings
			if [[ ${NPROC} -gt ${NMAX} ]]; then echo "You have requested more processors than is available on one node (${NMAX})"; exit; fi
		elif [[ ${NODES_SET} -ne 1 ]]; then #Add functionality for specifying NPROC per nodes in this way
			NODES=${NODES_SET}; TASK_PER_NODE=${NPROC_SET}; NPROC=$(( ${NPROC_SET} * ${NODES} ))
		fi
	else
		NODES=1; NPROC=${NMAX}; TASK_PER_NODE=${NMAX}
	fi
}
Batch_Builder(){
	if [[ ${QUEUE} == "nova" ]]; then 
		MODULES_STR="${NOVA_MODULES}"; else MODULES_STR="${GENBIG_MODULES}"
	fi
	TAB="$(printf '\t')"
	if [[ ${EMAIL_MARKER} == 1 ]]; then EMAIL_OPTION="#SBATCH --mail-type=END,FAIL,REQUEUE,TIME_LIMIT_90";
		else	EMAIL_OPTION="#SBATCH --mail-type=NONE"; fi
	if [[ ${RESTART_OPT} -ne "true" ]]; then RESTART_OPTION="#SBATCH --no-requeue"; fi
	Opening_Gen;
	Edit_Inp_Time;
	Submit_Gen;
	Closer_Gen;
}
Proc_Handler(){
#This is not currently used; add functionality for multi-threading
	if [[ ${THREADS} = 1 ]]; then
		:
	fi
}
Time_Converter(){
 #Function for converting the time request to correct format/calculating total seconds, and job cut-off
 #days-hours:minutes:seconds
	if [[ ${TIME} =~ ^[[:digit:]]+$ ]]; then
		DAY=${TIME}
		elif [[ ${TIME} =~ ^([0-9]+)-([0-9]+):([0-9]+)(:)?([0-9]*)$ ]]; then
			DAY=${BASH_REMATCH[1]}; HOUR=${BASH_REMATCH[2]}; MINUTE=${BASH_REMATCH[3]}; SECOND=${BASH_REMATCH[5]}
		elif [[ ${TIME} =~ ^([0-9]+):([0-9]+)(:)?([0-9]*)$ ]]; then
			HOUR=${BASH_REMATCH[1]}; MINUTE=${BASH_REMATCH[2]}; SECOND=${BASH_REMATCH[4]}
		else echo "There is an error with your time specification: ${TIME}"; exit
	fi
	if [[ -z ${DAY} ]]; then DAY=0; fi
	if [[ -z ${HOUR} ]]; then HOUR=0; fi
	if [[ -z ${MINUTE} ]]; then MINUTE=0; fi
	if [[ -z ${SECOND} ]]; then SECOND=0; fi
	TIME_FORMAT=$( echo ${DAY}-${HOUR}:${MINUTE}:${SECOND})
	TIME_SEC=$(( ${DAY}*24*3600 + ${HOUR}*3600 + ${MINUTE}*60 + ${SECOND} ))
	TIME_SEC_SHIFT=$(( ${DAY}*24*3600 + ${HOUR}*3600 + ${MINUTE}*60 + ${SECOND} - 300 ))
}
Edit_Inp_Time(){
 #Adds a function to batch files to automatically edit the walltime in input file to allow a calculation to end before time-out
	if [[ ${STOP_MARKER} == 1 ]]; then
		#If request for generating batch file for later submissions, edits batch file for dynamic functionality
		cat >> ${SUBDIR}/${FNAME}.batch <<- EOF
			# Start Wall-Time Editor
			# This function will automatically correct the input file to agree with the time set in this batch file
			TOT_TIME=\$(grep -i '#SBATCH --time=' \${SUBDIR}/\${FNAME}.batch | awk -F= '{print \$2}')
			DAYS_SEC=\$( echo \${TOT_TIME} | awk -F- '{ print \$1 * 24 * 3600 }' ) 
			HOUR_MIN_SEC=\$( echo \${TOT_TIME} | awk -F- '{print \$2}' | awk -F: '{print (\$1 * 3600) + (\$2 * 60) + \$3}')
			TOT_SEC=\$(( \${DAYS_SEC} + \${HOUR_MIN_SEC} - 600 ))
			sed -i "s/WALLTIME [-]*[[:digit:]]*/WALLTIME \${TOT_SEC}/" \${FNAME}.inp
			# End Wall-Time Editor
		EOF
	else
		cat >> ${SUBDIR}/${FNAME}.batch <<- EOF
			sed -i "s/WALLTIME [[:digit:]]*/WALLTIME ${TIME_SEC_SHIFT}/" \${FNAME}.inp
		EOF
	fi
}
Opening_Gen(){
#	Creates the opening section with Slurm settings
	cat > ${SUBDIR}/${FNAME}.batch <<- EOF
		#!/bin/bash  
		#SBATCH --partition=${QUEUE}
		#SBATCH --time=${TIME_FORMAT}
		#SBATCH --nodes=${NODES}
		#SBATCH --ntasks-per-node=${TASK_PER_NODE}
		#SBATCH --cpus-per-task=${THREADS}
		#SBATCH --job-name=${JOBNAME}.cp2k
		#SBATCH --error=${SUBDIR}/${FNAME}.err%j
		#SBATCH --output=${SUBDIR}/${FNAME}.err%j
		#SBATCH --mail-user=$(whoami)@auburn.edu
		${EMAIL_OPTION}
		${RESTART_OPTION}
		SUBDIR=${SUBDIR}
		WRKDIR=${WRKDIR}
		FNAME=${FNAME}
	EOF
}
Submit_Gen(){
	cat >> ${SUBDIR}/${FNAME}.batch <<- EOF
		#Submission of CP2K job
		${MODULES_STR}
		export OMP_NUM_THREADS=${THREADS}
		ulimit -s unlimited
		ulimit -f unlimited
		mpirun -np ${NPROC} cp2k.popt -i \${WRKDIR}/${FNAME}.inp -o \${WRKDIR}/${FNAME}.out
	EOF
}
Closer_Gen(){
	cat >> ${SUBDIR}/${FNAME}.batch <<- EOF
		# Clean up Script, deletes empty error files or moves to WRKDIR if not empty and the exit code
		if [[ ! -s \${SUBDIR}/\${FNAME}.err\${SLURM_JOB_ID} ]]; then
		${TAB} rm -f \${SUBDIR}/\${FNAME}.err\${SLURM_JOB_ID}
		elif [[ -s \${SUBDIR}/\${FNAME}.err\${SLURM_JOB_ID} ]] && [[ \${WRKDIR} != \${SUBDIR} ]]; then
		${TAB} mv \${SUBDIR}/\${FNAME}.err\${SLURM_JOB_ID} \${WRKDIR}/\${FNAME}.e\${SLURM_JOB_ID}
		fi
		exit 0
	EOF
}
Main "$@"; exit

#export OMP_NUM_THREADS=4
#export OMP_PROC_BIND=close
#export OMP_PLACES=cores

