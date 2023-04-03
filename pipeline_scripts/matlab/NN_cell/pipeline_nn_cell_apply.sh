#!/bin/bash

SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"


source ${SCRIPTPATH}/pipeline_paths.sh

echo $PATH
echo $LD_LIBRARY_PATH



__conda_setup="$(${HOME}'/miniconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "${HOME}/miniconda3/etc/profile.d/conda.sh" ]; then
        . "${HOME}/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="${HOME}/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup

conda activate pipeline3



which python
echo "calling ${SCRIPTPATH}/detect_cells.py with "
echo $1
echo $2



python ${SCRIPTPATH}/detect_cells.py --fg $1  --out $2 --model ${SCRIPTPATH}/model_pipe_net_wider_gaussian_revised02_manual_neg/tracer_net --chkpt 146000 
