#!/usr/bin/env python

import sys
import os
import math
import re
from os.path import isfile, join, isdir


from kn_common import pipetools,pipedef
from kn_pipeline_class import CPipeError,CPipeStep


class CPipeNNCell(CPipeStep):

	def progress_update(self,txt):
	  if re.match(r'#PROGRESS#\d*#', txt):
	    progress=int(re.search(r'\d+', txt).group())
	    self.update_progress("run",progress)
	  else:
	    print("#I: "+txt)
	    sys.stdout.flush()
  
	def batch_run(self):
            matlab_tools=pipedef.matlab_tools+"/NN_cell/"
            matlab_bin=pipedef.matlab_bin


            ofolder = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/labels/CELLS/"
            print("#I: creating dest folder")

            mkdir="mkdir -p "+ofolder
            print("#I: "+mkdir)
            res , folder_success  = pipetools.bash_run(mkdir)

            if not (folder_success):
                    raise CPipeError("creating folders failed")


            success=True

            MCOMMAND='cd '+matlab_tools+'/; addpath(pwd);'
            MCOMMAND+="pipeline_nn_cell(\'"+self.mid+"\',\'"+ofolder+"\');"
            MCOMMAND+='exit;'
            if True:
                COMMAND=matlab_bin+" -r \""+MCOMMAND+"\""

                success  = pipetools.bash_run_and_print(COMMAND,self.progress_update)

            if not success:
                raise CPipeError("cell detection failed")

            #self.local_chgrp(ofolder+" -R")
            #self.local_chmod(" +Xr ",ofolder+" -R")
	      
	def batch_clean(self):
            ofolder = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/labels/CELLS/"
            clearme={
                ofolder
            }

            deldir_basedir=pipedef.PIPELINE_KN_RAID_DEL+"/";
            deldir=self.mid+pipetools.get_folder_timestamp();
            self.local_mkdir(deldir_basedir+deldir)

            for delme in clearme:
                if not os.path.isdir(delme):
                    print("#W: skipping "+delme+", does not exist")
                else:  
                    self.local_mv(delme,deldir_basedir+deldir)
                    
            SLURM_command={"cd "+deldir_basedir+" && rm "+deldir+" -r"};

            res, success=pipetools.slurm_submit(SLURM_command,self.ofile,name=self.mid+"-CLEAN-"+self.shortname,queue="kn_pipe_cleanup")
            if not success:
                raise CPipeError("submitting cleaning script failed "+format(res[0]));

		  
try:
	pipe_step=CPipeNNCell({'kn_pipeline_meso_get_t2n.py','kn_pipeline_meso_inj_seg.py'},shortname="meso-NN-cell");
	print("#I: scriptname is \""+pipe_step.name()+"\"")
	pipe_step.print_settings()
	slurm_params={'queue':"kn_pipe_slave_GPU",'time':"10-00:00:00",'cores':8,'mem':20000,'gres':"gpu:1,KN:1",'feature':''}
	#slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':8,'mem':20000,'feature':''}
	pipe_step.run(slurm_params,{'kn_pipeline_meso_NN_cells_3D.py'})
	
	
except CPipeError as e:
	print("#E: "+e.value)







