#!/bin/bash

global_POTCAR_Dir="/opt/software/VASP/6.2.1-intel-2020b/pot/PBE"

local_POTCAR_Dir="$SALSA_DIR/ReferenceFiles/POTCARs"

elements=( H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og )

if [[ ! -d $local_POTCAR_Dir ]]; then
    mkdir -p $local_POTCAR_Dir
    echo Made directory $local_POTCAR_Dir
fi

for element in "${elements[@]}"; do
    potential_POTCAR="${global_POTCAR_Dir}/${element}/POTCAR"
    potential_new_POTCAR="${local_POTCAR_Dir}/POTCAR_${element}"
    if [[ -f $potential_new_POTCAR ]]; then
        echo POTCAR_${element} already exists locally. Skipping.
    elif [[ -f $potential_POTCAR ]]; then
        cp $potential_POTCAR $potential_new_POTCAR
        echo Copied POTCAR_${element} to local directory
    else
        echo Did not find ${potential_POTCAR}. Skipping.
    fi
done

