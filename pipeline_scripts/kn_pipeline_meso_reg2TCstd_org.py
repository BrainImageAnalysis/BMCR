#!/usr/bin/env python

import sys
import os
import re
import math
#import commands
#import pandas as pd
from os.path import isfile, join, isdir

from kn_common import pipetools,pipedef
from kn_pipeline_class import CPipeError,CPipeStep


class CPipeStepR2TC(CPipeStep):
  
    def batch_run(self):
            if True:
                matlab_tools=pipedef.matlab_tools
                matlab_bin=pipedef.matlab_bin
                ants_reg = ants_reg.ants_reg
                ants_apply = ants_apply.ants_apply
                
                
                
                compute_trafo = True
                apply_trafo = True
                create_preview = True
                create_mask = True

                compute_trafo = False
                apply_trafo = False
                create_preview = False  
                create_mask = False

                create_mask = False
                compute_trafo = True
                apply_trafo = True
                create_preview = True  

                
                
                 
                FIX = pipedef.PIPELINE_DATABSE_FOLDER+"/model/avg_TC_std.nii.gz"          
                MOVE = pipedef.PIPELINE_DATABSE_FOLDER+format(self.mid)+"/tissuecyte/3d/reg/img3D_bg_TC_org.nii.gz"
                MASK = pipedef.PIPELINE_DATABSE_FOLDER+format(self.mid)+"/tissuecyte/3d/reg/img3D_bg_TC_org_mask.nii.gz"
                MASK_INV = pipedef.PIPELINE_DATABSE_FOLDER+format(self.mid)+"/tissuecyte/3d/reg/img3D_bg_TC_org_mask_inverse.nii.gz"
                
                meta = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/meta/trafos/reg2TC/"
                
                reg_out = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/"
                
                
                reg_out_file = (reg_out + "img3D_bg_TC_org.nii.gz").replace("TC_org.nii.gz",'TC_std.nii.gz')
                
                print(FIX)
                print(MOVE)
                
                POSTTRAFO = meta+"trafo-final"
  
                
                PRETRAFO = " --initial-moving-transform ["+FIX+","+MOVE+",1] "
                
                print("#I: starting the registration 2 ")
            
                COMMAND = "ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=80 "+ants_reg+" -d 3 -v 1  \
                                                    --float 1 \
                                                    --winsorize-image-intensities [0.005,0.995] \
                                                    --write-composite-transform 1 \
                                                    "+PRETRAFO+" \
                                                    -o ["+POSTTRAFO+"]  \
                                                    --transform affine[ 0.1 ] \
                                                    --masks [NONE,NONE] \
                                                    -m Mattes["+FIX+","+MOVE+",1,32,Random,0.25] \
                                                    -c [1000x250x200x100, 1.e-8, 20]  \
                                                    -s 3x2x1x0vox  \
                                                    -f 8x4x2x1  \
                                                    --transform SyN[ 0.05,3,0 ] \
                                                    --masks [NONE,NONE] \
                                                    -m Mattes["+FIX+","+MOVE+",1,32,Random,0.5] \
                                                    -c [1000, 1.e-10, 20]  \
                                                    -s 3vox  \
                                                    -f 8 \
                                                    --transform SyN[ 0.15,3,0 ] \
                                                    --masks [NONE,"+MASK_INV+"] \
                                                    -m CC["+FIX+","+MOVE+",1,4,Random,0.5] \
                                                    -c [1000, 1.e-10, 20]  \
                                                    -s 3vox  \
                                                    -f 8 \
                                                    \
                                                    --transform SyN[ 0.05,3,0 ] \
                                                    --masks [NONE,NONE] \
                                                    -m Mattes["+FIX+","+MOVE+",1,32,Random,0.25] \
                                                    -c [500, 1.e-10, 20]  \
                                                    -s 2vox  \
                                                    -f 4 \
                                                    --transform SyN[ 0.15,3,0 ] \
                                                    --masks [NONE,"+MASK_INV+"] \
                                                    -m CC["+FIX+","+MOVE+",1,4,Random,0.25] \
                                                    -c [500, 1.e-10, 20]  \
                                                    -s 2vox  \
                                                    -f 4 \
                                                    \
                                                    --transform SyN[ 0.15,3,0 ] \
                                                    --masks [NONE,"+MASK_INV+"] \
                                                    -m CC["+FIX+","+MOVE+",1,4,Random,0.25] \
                                                    -c [100, 1.e-10, 20]  \
                                                    -s 1vox  \
                                                    -f 2 \
                                                    --transform SyN[ 0.15,3,0 ] \
                                                    --masks [NONE,"+MASK_INV+"] \
                                                    -m CC["+FIX+","+MOVE+",1,4,Random,0.25] \
                                                    -c [50, 1.e-10, 20]  \
                                                    -s 0vox  \
                                                    -f 1  "



                print("#I: creating directories")
                cmd = 'mkdir -p '+meta
                res , folder_success  = pipetools.bash_run(cmd)
                if not (folder_success):
                			raise CPipeError(" mkdir failed")
                
                cmd = 'mkdir -p '+reg_out
                res , folder_success  = pipetools.bash_run(cmd)
                if not (folder_success):
                			raise CPipeError(" mkdir reg out failed")
                
                self.update_progress("run",5)       
                print("#I: starting the registration")
                


                MCOMMAND='cd '+matlab_tools+'/; addpath(pwd);'
                MCOMMAND+="pipeline_reg_mask(\'"+self.mid+"\');"
                MCOMMAND+='exit;'
		
                print("#I: "+MCOMMAND)

                if create_mask:
                    command=matlab_bin+" -r \""+MCOMMAND+"\""
                    success  = pipetools.bash_run_and_print(command)
    		
                    if not (success):
                        raise CPipeError("creating mask image")


                print("#I: "+COMMAND)


                if compute_trafo:
                    success  = pipetools.bash_run_and_print(COMMAND)
                    		
                    if not (success):
                    			raise CPipeError("error in antsRegistration")
                    
                self.update_progress("run",90)       
                 
                PRETRAFO_COMPOSED_NAME = POSTTRAFO+"Composite.h5 "  
                    
                COMMAND_APPLY = "ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=80 "+ants_apply+" -i "+MOVE+" -o "+reg_out_file+"\
                            -r  "+FIX + " \
                            -n Linear  \
                            --float 1 -v 1 \
                            -t  "+PRETRAFO_COMPOSED_NAME
                            
                if apply_trafo:
                    success  = pipetools.bash_run_and_print(COMMAND_APPLY)
                    		
                    if not (success):
                    			raise CPipeError("error applying final TRAFO ")
                            
                self.update_progress("run",95)            
                
                print("#I: creating preview images")
                preview_folder=pipedef.PIPELINE_DATABSE_FOLDER+"/preview/"+format(self.mid)+"/"
                mkdir="mkdir -p "+preview_folder
                print("#I: "+mkdir)
                res , folder_success  =  pipetools.bash_run(mkdir)
                if not (folder_success):
                    raise CPipeError("#E: creating folders failed")

                success=True;	
                print("#I: creating preview image ")
                fix_img = pipedef.PIPELINE_DATABSE_FOLDER+'/model/avg_TC_std.nii.gz'
                #moving_img = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/img3Dcubic_std_TC.nii.gz"
                moving_img = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/img3D_bg_TC_std.nii.gz"
                
                MCOMMAND='cd '+matlab_tools+'/; addpath(pwd);'
                MCOMMAND+="tiling_preview(\'"+preview_folder+"/"+pipe_step.name()+"_reg2TC_"+"\',\'"+fix_img+"\',\'"+moving_img+"\',70);"
                MCOMMAND+='exit;'
		
                print("#I: "+MCOMMAND)

                if create_preview:
                    command=matlab_bin+" -r \""+MCOMMAND+"\""
                    success  = pipetools.bash_run_and_print(command)
    		
                    if not (success):
                        raise CPipeError("creating preview image")

                #print("#I: updating folder premissions")
                #self.local_chgrp(preview_folder+" -R")


                prev_path="\{PREVIEWFOLDER\}"+"/"+self.mid+"/"+pipe_step.name()
              
                print(prev_path)
                desc=[  ['INFO(Tiling)', prev_path+"_reg2TC_normal.png"],
                        ['INFO(Color)', prev_path+"_reg2TC_color.jpg"]]


                html=""
                for value in desc:
                        html+="echo '<div class=\"group2\"  style=\"font-size:12px\">';"
                        html+="echo '<div  style=\"font-size:24px\">"+value[0]+"</div><br>';"
                        html+="echo '<img src="+value[1]+" width=100%>';"
                        html+="echo '</div><br>';"

                print("#I: adding detailed preview data to table")
                self.sql_add_custome_data("details",html.replace("'","\\\'"),"VARCHAR(20000)");                                   

    def batch_clean(self):
    	  clearme={
      pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/3d/reg/img3Dcubic_std_TC.nii.gz",
      pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/3d/reg/img3D_bg_TC_std.nii.gz"
      }
    	  
    	  deldir_basedir=pipedef.PIPELINE_KN_RAID_DEL+"/"
    	  deldir=self.mid+pipetools.get_folder_timestamp()
    	  self.local_mkdir(deldir_basedir+deldir)
    	  
    	  for delme in clearme:
    	    if not os.path.isfile(delme):
    	      print("#W: skipping "+delme+", does not exist")
    	    else:  
    	      self.local_mv(delme,deldir_basedir+deldir)
    	  	
    	  SLURM_command={"cd "+deldir_basedir+" && rm "+deldir+" -r"};
    	  
    	  res, success=pipetools.slurm_submit(SLURM_command,self.ofile,name=self.mid+"-CLEAN-"+self.shortname,queue="kn_pipe_cleanup")
    	  if not success:
    	      raise CPipeError("submitting cleaning script failed "+format(res[0]));	
	      
try:
	pipe_step=CPipeStepR2TC({'kn_pipeline_meso_get_t2n.py'},shortname="meso-R2TC");
	print("#I: scriptname is \""+pipe_step.name()+"\"")
	pipe_step.print_settings()
	slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':160,'mem':128000,'gres':"KN:5",'feature':''}
	pipe_step.run(slurm_params,{'kn_pipeline_meso_apply_trafos_TC.py'})
       
	
	
except CPipeError as e:
	print("#E: "+e.value)



