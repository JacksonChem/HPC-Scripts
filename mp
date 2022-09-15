#!/bin/bash

flag=$1

for file in $( ls *log); do 
	if [[ -n $(grep '#mp2/' ${file}) ]]; then
		if [ "$flag" != "p" ]; then
			echo "**************************"
		fi
		if [ "$flag" != "p" ] && [ `grep -c 'Error termination' $file` -ne 0 ]; then
      			echo $file | awk -F. '{print $1}'
      			echo "Failed"
		elif [ `grep -c 'Normal term' $file` -eq 1 ] || [ `grep -c 'Normal term' $file` -eq 2 ]; then
			ehf=$(grep 'E([UR]HF)' $file | tail -1 | awk '{print $5}')
			mp2_val=$(grep 'EUMP2 =' $file | awk '{print $6}' | tail -1 | awk -FD '{print $1}')
			mp2_exp=$(grep 'EUMP2 =' $file | awk '{print $6}' | tail -1 | awk -FD '{print $2}')
			if [[ -n ${mp2_exp} ]]; then	
				mp2_power=$((10**$mp2_exp))
				emp2=$(echo "$mp2_val * $mp2_power" | bc )
			else
				emp2="null"
      			fi
			echo $file | awk -F. '{print $1}'
			echo "Ehf  = $ehf"
			echo "Emp2 = $emp2"
			if [ "$flag" = "e" ]; then
				echo "mp2_val   = $mp2_val"
				echo "mp2_exp   = $mp2_exp"
				echo "mp2_power = $((10**$mp2_exp))"
			fi 
		fi
		if [ "$flag" != "p" ]; then
			echo "----------------------------------------------"  
		fi
	fi
done

