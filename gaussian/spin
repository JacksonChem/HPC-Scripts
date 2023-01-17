#!/bin/bash

flag=$1

for file in $( ls *log)
  do 
    if [ "$flag" != "p" ]; then
      echo "**************************"
    fi
      echo $file | awk -F. '{print $1}'
      grep 'S\*\*2' $file 
    if [ "$flag" != "p" ]; then
      echo "----------------------------------------------"  
    fi
  done
