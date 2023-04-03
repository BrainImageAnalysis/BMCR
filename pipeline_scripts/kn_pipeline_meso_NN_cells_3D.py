#!/usr/bin/env python

import sys
import os
import math
import re
from os.path import isfile, join, isdir
from os import listdir
import csv

from kn_common import pipetools,pipedef
from kn_pipeline_class import CPipeError,CPipeStep

def get_injection_site_location(folder):
    allfiles_and_folders = listdir(folder)
    allfiles = [
        f for f in allfiles_and_folders if isfile(join(folder, f))]

    csv_files = [join(folder,f) for f in allfiles if (
        (f[len(f) - 3:len(f)] == 'csv'))]

    scount = 0
    
    x = 0
    y = 0
    z = 0
    total_number = 0
    for f in csv_files:
        scount += 1
        with open(join(folder,'shape.csv'), 'r') as csvfile:
            label_data_ = csv.reader(csvfile, delimiter=",")
            for l in label_data_:
                shape=[int(l[1]),int(l[0])]

        with open(f, 'r') as csvfile:
            label_data_ = csv.reader(csvfile, delimiter=",")
            for l in label_data_:
                posx = float(l[1])
                posy = float(l[0])
                z += scount
                x += posx
                y += posy
                
                total_number += 1
                
    x /= total_number
    y /= total_number
    z /= total_number
    
    return x, y, z


class CPipeStepNNCellsStitch3D(CPipeStep):

    def progress_update(self,txt):
      if re.match(r'#PROGRESS#\d*#', txt):
        progress=int(re.search(r'\d+', txt).group())
        self.update_progress("run",progress)
      else:
        print("#I: "+txt)
        sys.stdout.flush()
        
    foldername="inj"    
    signal_name="cell_density_TC_org.nii.gz"
    signal_name2="cell_counts_raw_TC_org.nii.gz"
    
  
    def batch_run(self):
        matlab_tools=pipedef.matlab_tools
        matlab_tools_cells=pipedef.matlab_tools+'/NN_cell/'
        matlab_bin=pipedef.matlab_bin

        

        if True:
            MCOMMAND='cd '+matlab_tools+'/; addpath(pwd);cd '+matlab_tools_cells+'/; addpath(pwd);'
            #MCOMMAND+="ishii_pipeline_NN_tracer_3D(\'"+self.mid+"\',\'trafo\',\'"+trafo+"\');"
            MCOMMAND+="pipeline_cell_3D(\'"+self.mid+"\');"
            MCOMMAND+='exit;'
    
            COMMAND=matlab_bin+" -r \""+MCOMMAND+"\""
    
            success  = pipetools.bash_run_and_print(COMMAND,self.progress_update)
    
            if not success:
                    print(res[0])
                    print(res[1])
                    raise CPipeError("3D stitching of cell density map failed")

        #inj_x,inj_y,inj_z = get_injection_site_location(pipedef.PIPELINE_DATABSE_FOLDER+"/"+self.mid+"/tissuecyte/slice/labels/CELLS/")
        if False:
            print(("inj_x "+format(inj_x)))
            print(("inj_y "+format(inj_y)))
            print(("inj_z "+format(inj_z)))

            MCOMMAND='cd '+matlab_tools+'/; addpath(pwd);'
            #MCOMMAND+="ishii_pipeline_NN_tracer_3D(\'"+self.mid+"\',\'trafo\',\'"+trafo+"\');"
            MCOMMAND+="pipeline_inj_center_3D(\'"+self.mid+"\',\'"+str(inj_x)+"\',\'"+str(inj_y)+"\',\'"+str(inj_z)+"\');"
            MCOMMAND+='exit;'
    
            COMMAND=matlab_bin+" -r \""+MCOMMAND+"\""
    
            success  = pipetools.bash_run_and_print(COMMAND,self.progress_update)
    
            if not success:
                    print(res[0])
                    print(res[1])
                    raise CPipeError("3D stitching of cell density map failed")
        
                
        self.update_progress("run",25)

        #self.local_chgrp(pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"+self.foldername+" "+" -R")
        #self.local_chmod(" +Xr ",pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"+self.foldername+" ")
        #self.local_chmod(" +Xr ",pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"+self.foldername+" -R")

        if True:
            self.create_previews()
    
    def create_previews(self):
        matlab_tools_cells='/disk/k_raid/KAKUSHIN-NOU-DATA/SOFT/pipeline/pipeline_local/matlab/NN_tracer/'
        matlab_bin="/disk/soft/MATLAB/matlab2019/bin/matlab"
        
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
        ifolder=ofolder+"/"+self.signal_name
        ifolder2=ofolder+"/"+self.signal_name2
        if True:
            MCOMMAND='cd '+matlab_tools_cells+'/; addpath(pwd);'
            MCOMMAND+="my_Tracersig_create_preview(\'"+ifolder+"\',\'"+preview_folder+"/"+pipe_step.name()+"\');"
            MCOMMAND+="my_Tracersig_create_preview(\'"+ifolder2+"\',\'"+preview_folder+"/"+pipe_step.name()+"\','_raw_');"
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
        html+="echo '<img src=\""+prev_path+"_t_normal.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
        #html+="echo 'bla';";
        html+="echo '</div><br>';"
        html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';"
        #html+="echo 'bla';";
        html+="echo '<img src=\""+prev_path+"_raw__t_normal.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
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
          ofolder+"/"+self.signal_name2
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
    pipe_step=CPipeStepNNCellsStitch3D({'kn_pipeline_meso_NN_cells.py','kn_pipeline_meso_get_t2n.py'},shortname="meso-trsig3D")
    print("#I: scriptname is \""+pipe_step.name()+"\"")
    pipe_step.print_settings()
    #slurm_params={'queue':"kn_pipe_IO",'time':"10-00:00:00",'cores':8,'mem':10000,'gres':"KN:10",'feature':'2.4GH'};
    slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':8,'mem':32000,'feature':'','gres':"KN:5"}
    pipe_step.run(slurm_params,{'kn_pipeline_meso_apply_trafos_TC.py'})
    
    
except CPipeError as e:
    print("#E: "+e.value)







