#!/bin/bash -l

#******************************************************#
#                                                      #
#             Script for running FHI-Aims              #
#     Intended to work with the SLURM queue system     #
#           within the Easley HPC system               #
#                                                      #
#        Benjamin Jackson, Auburn University           #
#                 baj0040@auburn.edu                   #
#                                                      #
#                Updated: 04/29/2022                   #
#                                                      #
#******************************************************#

Main(){
	FNAME=$(echo ${!#} | awk -F. '{print $1}')
  ##Defaults:
	NODES=1
	QTYPE=g
	TIME=200:00	
	SCR_CLEAN=1 #Setting to autoclean FHI job folders in scratch, 1 = true
  ##Default paths:
	#SUBDIR=$(pwd)
	SUBDIR=/home/$(whoami)/.subfiles
	WRKDIR=$(pwd)
	SCRDIR=/scratch/$(whoami)/fhia/${FNAME}
	BACKUPDIR=/home/$(whoami)/trash/overwrite
	SCRIPT_PATH=$( dirname "$(readlink -f "$0")" )
	##Modules
	FHIAims_MODULE=fhi-aims/2021 
	#Begin Program
	if [[ ! -d ${SCRDIR} ]]; then mkdir -p ${SCRDIR}; fi
	if [[ ! -d ${BACKUPDIR} ]]; then mkdir -p ${BACKUPDIR}; fi 
	if [[ "$#" -lt 1 ]]; then Helpfn; exit; fi #Calls help function if no passed variables
	Option_Handler "$@";
	if [[ ! -e ${FNAME}.ctrl ]]; then echo "Input file was not found"; exit 30; fi
	Proc_Handler;
  QUEUE=$(Queue_Set)
	Maint_Check; #Checks if there as a max walltime and adjust time if so
	Batch_Builder; #Construct the batch submission script
	if [[ ${STOP} = 1 ]]; then mv ${SUBDIR}/${FNAME}.batch ${WRKDIR}/; exit; fi
	sbatch ${SUBDIR}/${FNAME}.batch
	#rm -f ${SUBDIR}/${FNAME}.batch
}
Proc_Handler(){
  QTYPE=$( echo $QTYPE | awk '{print tolower($0)}' )
  case ${QTYPE} in
    [bB]2) SCALE=48; NPROC_PER=48;;
    [rR][bB]2) SCALE=48; NPROC_PER=48;;
    [bB]4) SCALE=48; NPROC_PER=48;;
    [a]) SCALE=128; NPROC_PER=128;;
    [Gg][Pp][Uu]) SCALE=48; NPROC_PER=48;;
    [rR]) SCALE=48; NPROC_PER=48;;
    *) SCALE=48; NPROC_PER=48;;
  esac
	#echo $(( ${NODES} * ${SCALE} )) 
	NPROC=$(( ${NODES} * ${SCALE} )) 
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
Batch_Builder(){
	Opening_Gen;
	FHIAims_Gen;
	Closer_Gen;	
}
#Function for specifying general job settings
Opening_Gen(){
	cat > ${SUBDIR}/${FNAME}.batch <<- EOF
		#!/bin/bash -l
		#SBATCH --job-name=${FNAME}.fhi
		#SBATCH --error=${SUBDIR}/${FNAME}.e%j
		#SBATCH --nodes=${NODES}
		##SBATCH --ntasks=${NPROC}
		#SBATCH --ntasks-per-node=${NPROC_PER}
		#SBATCH --time=${TIME}:00
		#SBATCH --output=/dev/null
		#SBATCH --partition=${QUEUE}
		#SBATCH --mail-user=$(whoami)@auburn.edu
		#SBATCH --mail-type=NONE
		#SBATCH --no-requeue
		#SBATCH --exclusive
		WRKDIR=${WRKDIR}
		FNAME=${FNAME}
		SCRDIR=${SCRDIR}
		SUBDIR=${SUBDIR}
		export OMP_NUM_THREADS=${THREADS}
		ulimit -s unlimited
		ulimit -f unlimited
	EOF
#${MEM_STR}
#${NODE_STR}
#${NPROC_STR}
#SBATCH --cpus-per-task=1
}
#Function for generating FHI-Aims specific commands
FHIAims_Gen(){
	if [[ ${SCR_CLEAN} = 1 ]]; then rm -f ${SCRDIR}/*in; rm -f ${SCRDIR}/*out; rm -f ${SCRDIR}/band*out; rm -f ${SCRDIR}/*cube; fi
	cat >> ${SUBDIR}/${FNAME}.batch <<- EOF
		NPROC=${NPROC}
		module load ${FHIAims_MODULE}
		cp \${WRKDIR}/\${FNAME}.geom \${SCRDIR}/geometry.in
		cp \${WRKDIR}/\${FNAME}.ctrl \${SCRDIR}/control.in
		cd \${SCRDIR}
		mpirun -n \${NPROC} aims.210226.scalapack.mpi.x > \${WRKDIR}/\${FNAME}.out
		bandorg.py --IsJob --HomeDir \${WRKDIR} \${FNAME}
		cd \${WRKDIR}
		#cube ${FNAME}.out
		${SCRIPT_PATH}/fhicube ${FNAME}.out
	EOF
}
#Cleans up error and batch files on completion
Closer_Gen(){
	cat >> ${SUBDIR}/${FNAME}.batch <<- EOF
		if [[ ! -s \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID} ]]; then
    rm -f \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID}; else
    mv \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID} \${WRKDIR}/. ; fi
		exit 0
	EOF
}
#Function for checking if their is a maintenance max walltime and adjusts time requests accordingly
Maint_Check(){
	Queue_Limit=$(/tools/scripts/max_walltime.sh | grep 'Wall-time (hours)' | awk -F: '{print $2}' | sed 's/ //') 
	Time_Req=$( Round_Up $( echo ${TIME} | awk -F: '{print $1  * 60 +  $2 }') )
	if [[ -s Queue_Limit ]] && [[ $(( ${Queue_Limit} * 60 )) -lt ${Time_Req} ]]; then TIME="${Queue_Limit}:00"; fi 
}
#Function for determing job queue
Queue_Set(){
	QTYPE=$( echo $QTYPE | awk '{print tolower($0)}' )
	case ${QTYPE} in
		[bB]2) echo "bigmem2";;
		[rR][bB]2) echo "ezm0048_bg2";;
		[bB]4) echo "bigmem4";;
		[a]) echo "amd";;
		[Gg][Pp][Uu]2) echo "gpu2";;
		[Gg][Pp][Uu]4) echo "gpu4";;
		[r]) echo "ezm0048_std";;
		*) echo "general";;
	esac
}
#Determines the maximum allowed resources for each queue; not currently used
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
Req_Check(){
#Not used currently
	QTYPE=$( echo $QTYPE | awk '{print tolower($0)}' )
	case $QTYPE in
		rb2 | b2 ) NMAX=48; MEMMAX=384;;
		b4) NMAX=48; MEMMAX=768;;
		a | amd) NMAX=128; MEMMAX=256;;
		gpu2 | gpu4) echo "This script is not set up for GPU calculations- please resubmit with another queue"; exit 30 ;;
		s | * ) NMAX=48; MEMMAX=192;;
	esac
	if [[ ${NPROC} -gt ${NMAX} ]]; then NODES_NPROC=$( Div_Rounder "${NPROC}" "${NMAX}" ); fi
	if [[ ${MEM} -gt ${MEMMAX} ]]; then NODES_MEM=$( Div_Rounder "${MEM}" "${MEMMAX}" ); fi
	if [[ ${NODES_NPROC} -gt ${NODES_MEM} ]]; then NODES=${NODES_NPROC};
		elif [[ ${NODES_MEM} -gt ${NODES_NPROC} ]]; then NODES=${NODES_MEM};
		else NODES=1; fi
	if [[ ${NODES} -eq 1 ]]; then MEM_STR="#SBATCH --mem=${MEM}GB";
		else MEM_STR="#SBATCH --mem-per-cpu=$( Div_Rounder "${MEM}" "${NPROC}" )GB
#SBATCH --ntasks-per-node="; 
	fi	
	#Set up a handler for controlling tasks per node here
	NPROC_STR="#SBATCH --ntasks=${NPROC}"	
	NODE_STR="#SBATCH --nodes=${NODES}"
	if [[ ${NODE_LIMIT} -eq 1 ]]; then
		if [[ ${MEM} -gt ${MEMMAX} ]]; then
			echo "You have requested more memory than is available for this queue; if needed, request additional nodes"
			exit 10
		fi
		if [[ $NPROC -gt $NMAX ]]; then
			echo "You have requested more processors than is available on a node; if needed, request additional nodes"
			exit 15
		fi
	fi
}
Helpfn(){
echo "
You have run the rfhi job submission script for FHI-Aims 2022. This script will automatically create a batch job for you. 

The output files will automatically be placed in the current directory.
Input files must be of the form:  [file].ctrl and [file].geom
Output files will be of the form: [file].out

      Options:
       -h    |   Help, displays this current usage guide
       -n    |   Number of Processors Requested
       -m    |   Memory Requested in GB; Specifying the GB units is optional- this is not currently used 
       -t    |   Time Limit for Jobs in HR:MIN format
       -N    |   Number of nodes to run on; this is unnecessary as the nodes will be determined by your resources request
       -q    |   Which queue this job will be submitted to; Options: b2- bigmem2, rb2- Investor bigmem2, b4-bigmem4, a-amd,
             |      gpu-GPU2, r-Investor general, g- general nodes       

You may specify these in any order, but the file name must be the last value specified. 

If -n, -m, -t, and -q are not specified default values will be used.

Your current defaults are:
       Proc    =   ${NPROC}
       Time    =   ${TIME}
       Queue   =   ${QTYPE}/$(Queue_Set)
You can change this in $(echo $0)

EXAMPLE:
$(echo $0) -n 12 -t 10:00 -q b2 file.ctrl 
"
}
Round_Up(){
echo $( python -c "print( int( -(-${1} // 1) ) )"   )
}
Div_Rounder(){
	A=$1
	B=$2
	if [[ $( python -c "print(${A}%${B})" ) -ne 0 ]]; then
		echo $( python -c "print( int( ((${A}-(${A}%${B}))/${B}+1) ) )" )
		else echo $( python -c "print( int(${A}/${B}) )" )
	fi
}
Main "$@"; exit
