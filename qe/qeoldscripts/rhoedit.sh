#!/bin/bash -l

for i in $(ls *scf.in); do
        findwfc=$(grep 'ecutwfc' "$i")
        findrho=$(grep 'ecutrho' "$i")
        sed -i "s/$findwfc/ ecutwfc=102",/ $i
        sed -i "s/$findrho/ ecutrho=1020",/ $i
done
