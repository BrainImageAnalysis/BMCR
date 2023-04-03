#!/usr/bin/env python

import sys
import os
import math
import re
from os.path import isfile, join, isdir


from kn_common import pipetools,pipedef
from kn_pipeline_class import CPipeError,CPipeStep


class CPipeStepNNTracerStitch3D(CPipeStep):

    def progress_update(self,txt):
      if re.match(r'#PROGRESS#\d*#', txt):
        progress=int(re.search(r'\d+', txt).group())
        self.update_progress("run",progress)
      else:
        print("#I: "+txt)
        sys.stdout.flush()
        
    foldername="NN_tracer"    
    signal_name="NN_tracer.nii.gz"
    weighted_signal_name="NN_tracer_weighted.nii.gz"
    signal_name_2020="NN_tracer_2020.nii.gz"
    weighted_signal_name_2020="NN_tracer_weighted_2020.nii.gz"
    weighted_signal_name_single_channel="NN_tracer_weighted_C2.nii.gz"
    weighted_signal_name_single_channel_2020="NN_tracer_weighted_C2_2020.nii.gz"
    def batch_run(self):
        matlab_tools1=pipedef.matlab_tools
        matlab_tools2=pipedef.matlab_tools+'/NN_tracer'
        matlab_bin=pipedef.matlab_bin



        print("#I: creating dest folders")
        mkdir="mkdir -p "+pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"+self.foldername
        print("#I: "+mkdir)
        res , folder_success  = pipetools.bash_run(mkdir)

        if not (folder_success):
                raise CPipeError("creating folders failed")

        success=True
        #reference=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/img3Dcubic_org.nii.gz"
        reference=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/img3D_bg_TC_org.nii.gz"
        #trafo_file=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/meta/tif2nii_trafo.mat"    


        MCOMMAND='cd '+matlab_tools1+'/; addpath(pwd);cd '+matlab_tools2+'/; addpath(pwd);'
        MCOMMAND+="ishii_pipeline_NN_tracer_3D_2019(\'"+self.mid+"\',\'ref\',\'"+reference+"\',\'signal_name\',\'"+self.signal_name+"\',\'weighted_signal_name\',\'"+self.weighted_signal_name+"\',\'weighted_signal_name_single_channel\',\'"+self.weighted_signal_name_single_channel+"\');"
        MCOMMAND+="ishii_pipeline_NN_tracer_3D(\'"+self.mid+"\',\'ref\',\'"+reference+"\',\'signal_name\',\'"+self.signal_name_2020+"\',\'weighted_signal_name\',\'"+self.weighted_signal_name_2020+"\',\'weighted_signal_name_single_channel\',\'"+self.weighted_signal_name_single_channel_2020+"\');"
        MCOMMAND+="ishii_pipeline_NN_tracer_3D_smooth_z(\'"+self.mid+"\',\'ref\',\'"+reference+"\',\'signal_name\',\'"+self.signal_name_2020+"\',\'weighted_signal_name\',\'"+self.weighted_signal_name_2020+"\',\'weighted_signal_name_single_channel\',\'"+self.weighted_signal_name_single_channel_2020+"\');"
        
        MCOMMAND+='exit;'


        
        COMMAND=matlab_bin+" -r \""+MCOMMAND+"\""
        print(COMMAND)

        if True:
          success  = pipetools.bash_run_and_print(COMMAND,self.progress_update)

          if not success:
                  print(res[0])
                  print(res[1])
                  raise CPipeError("3D stitching of channel tracer signal failed")
                


        #self.local_chgrp(pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"+self.foldername+" "+" -R")
        #self.local_chmod(" +Xr ",pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"+self.foldername+" ")
        #self.local_chmod(" +Xr ",pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"+self.foldername+" -R")

        self.create_previews()
    
    def create_previews(self):
        matlab_tools1=pipedef.matlab_tools
        matlab_tools2=pipedef.matlab_tools+'/NN_tracer'
        matlab_bin=pipedef.matlab_bin
        
        print("#I: creating preview images")
        preview_folder=pipedef.PIPELINE_DATABSE_FOLDER+"/preview/"+format(self.mid)+"/"
        mkdir="mkdir -p "+preview_folder
        print("#I: "+mkdir)
        res , folder_success  =  pipetools.bash_run(mkdir)
        if not (folder_success):
            raise CPipeError("#E: creating folders failed")

        success=True;    
        print("#I: creating preview image ")
        
        ofolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"+self.foldername+"/"
        
        ifolder=ofolder+"/"+self.signal_name_2020
        ifolder2=ofolder+"/"+self.weighted_signal_name_2020
        ifolder_m=ofolder+"/"+self.signal_name_2020.replace(".nii.gz","_masked.nii.gz")
        ifolder2_m=ofolder+"/"+self.weighted_signal_name_2020.replace(".nii.gz","_masked.nii.gz")

        MCOMMAND='cd '+matlab_tools1+'/; addpath(pwd);cd '+matlab_tools2+'/; addpath(pwd);'
        MCOMMAND+="my_Tracersig_create_preview(\'"+ifolder+"\',\'"+preview_folder+"/"+pipe_step.name()+"_2020\');"
        MCOMMAND+="my_Tracersig_create_preview(\'"+ifolder2+"\',\'"+preview_folder+"/"+pipe_step.name()+"weighted_2020\');"
        MCOMMAND+="my_Tracersig_create_preview(\'"+ifolder_m+"\',\'"+preview_folder+"/"+pipe_step.name()+"_m_2020\');"
        MCOMMAND+="my_Tracersig_create_preview(\'"+ifolder2_m+"\',\'"+preview_folder+"/"+pipe_step.name()+"weighted_m_2020\');"
        #MCOMMAND+='exit;'
        
        ifolder=ofolder+"/"+self.signal_name
        ifolder2=ofolder+"/"+self.weighted_signal_name
        ifolder_m=ofolder+"/"+self.signal_name.replace(".nii.gz","_masked.nii.gz")
        ifolder2_m=ofolder+"/"+self.weighted_signal_name.replace(".nii.gz","_masked.nii.gz")

        #MCOMMAND='cd '+matlab_tools1+'/; addpath(pwd);cd '+matlab_tools2+'/; addpath(pwd);'
        MCOMMAND+="my_Tracersig_create_preview(\'"+ifolder+"\',\'"+preview_folder+"/"+pipe_step.name()+"\');"
        MCOMMAND+="my_Tracersig_create_preview(\'"+ifolder2+"\',\'"+preview_folder+"/"+pipe_step.name()+"weighted\');"
        MCOMMAND+="my_Tracersig_create_preview(\'"+ifolder_m+"\',\'"+preview_folder+"/"+pipe_step.name()+"_m\');"
        MCOMMAND+="my_Tracersig_create_preview(\'"+ifolder2_m+"\',\'"+preview_folder+"/"+pipe_step.name()+"weighted_m\');"
        MCOMMAND+='exit;'
        
        print("#I: "+MCOMMAND)

        command=matlab_bin+" -r \""+MCOMMAND+"\""

        res , success  = pipetools.bash_run(command)
        
        if not (success):
            print(format(res[0]))
            print(format(res[1]))
            raise CPipeError("creating preview image")

        #self.local_chgrp(preview_folder+" -R")
        
        print("#I: adding preview data to table")
        if True:
          self.sql_add_custome_data("icon",pipe_step.name()+"tiny.jpg")
          self.sql_add_custome_data("preview",pipe_step.name()+"small.jpg")
          

        
        prev_path="\{PREVIEWFOLDER\}"+"/"+self.mid+"/"+pipe_step.name()

        
        print("#I: creating html code") 
        
        html=""
        
        html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';"
        #html+="echo 'bla';";
        html+="echo '<img src=\""+prev_path+"_2020_t_normal.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
        #html+="echo 'bla';";
        html+="echo '</div><br>';"
        
        html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';"
        #html+="echo 'bla';";
        html+="echo '<img src=\""+prev_path+"weighted_2020_t_normal.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
        #html+="echo 'bla';";
        html+="echo '</div><br>';"

        html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';"
        #html+="echo 'bla';";
        html+="echo '<img src=\""+prev_path+"_m_2020_t_normal.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
        #html+="echo 'bla';";
        html+="echo '</div><br>';"

        html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';"
        #html+="echo 'bla';";
        html+="echo '<img src=\""+prev_path+"weighted_m_2020_t_normal.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
        #html+="echo 'bla';";
        html+="echo '</div><br>';"



        html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';"
        #html+="echo 'bla';";
        html+="echo '<img src=\""+prev_path+"_t_normal.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
        #html+="echo 'bla';";
        html+="echo '</div><br>';"
        
        html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';"
        #html+="echo 'bla';";
        html+="echo '<img src=\""+prev_path+"weighted_t_normal.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
        #html+="echo 'bla';";
        html+="echo '</div><br>';"

        html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';"
        #html+="echo 'bla';";
        html+="echo '<img src=\""+prev_path+"_m_t_normal.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
        #html+="echo 'bla';";
        html+="echo '</div><br>';"

        html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';"
        #html+="echo 'bla';";
        html+="echo '<img src=\""+prev_path+"weighted_m_t_normal.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
        #html+="echo 'bla';";
        html+="echo '</div><br>';"
        
          
        print("#I: adding detailed preview data to table") 
        self.sql_add_custome_data("details",html.replace("'","\\\'"),"VARCHAR(20000)")
        print("#I: done") 
    
    def batch_clean(self):
        ofolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"+self.foldername+"/"
        #ofolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/"+self.foldername+"/"
        clearme={
          ofolder+"/"+self.signal_name,
          ofolder+"/"+self.weighted_signal_name
        }
        
        deldir_basedir=pipedef.PIPELINE_KN_RAID_DEL+"/"
        deldir=self.mid+pipetools.get_folder_timestamp()
        self.local_mkdir(deldir_basedir+deldir)
        
        for delme in clearme:
          if not os.path.isfile(delme):
            print("#W: skipping "+delme+", does not exist")
          else:  
            self.local_mv(delme,deldir_basedir+deldir)
              
        SLURM_command={"cd "+deldir_basedir+" && rm "+deldir+" -r"}
        
        res, success=pipetools.slurm_submit(SLURM_command,self.ofile,name=self.mid+"-CLEAN-"+self.shortname,queue="kn_pipe_cleanup")
        if not success:
            raise CPipeError("submitting cleaning script failed "+format(res[0]))
          
try:
    pipe_step=CPipeStepNNTracerStitch3D({'kn_pipeline_meso_NN_tracerseg.py','kn_pipeline_meso_get_t2n.py','kn_pipeline_meso_NN_cells_3D.py'},shortname="meso-trsig3D")
    print("#I: scriptname is \""+pipe_step.name()+"\"")
    pipe_step.print_settings()
    #slurm_params={'queue':"kn_pipe_IO",'time':"10-00:00:00",'cores':8,'mem':10000,'gres':"KN:10",'feature':'2.4GH'};
    slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':8,'gres':"KN:5",'mem':32000,'feature':''}
    #pipe_step.run(slurm_params,{'kn_pipeline_meso_apply_trafos_TC.py'})
    #pipe_step.run(slurm_params,{''})
    pipe_step.run(slurm_params,{'kn_pipeline_meso_norm_tracer.py'})
    
    
    
except CPipeError as e:
    print("#E: "+e.value)







