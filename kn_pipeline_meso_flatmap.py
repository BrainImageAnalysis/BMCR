#!/usr/bin/env python

import sys
import os
import math
import subprocess
#import pandas as pd
from os.path import isfile, join, isdir

from kn_common import pipetools,pipedef
from kn_pipeline_class import CPipeError,CPipeStep

import hashlib



class CPipeStepFmap(CPipeStep):

    reg_name = "img3D_bg_TC_org.nii.gz"
    
    jobs = [ 
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_masked_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap/tracer_masked_TC_org_2_TC_std',
        ],        
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_masked_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap/tracer_weighted_masked_TC_org_2_TC_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_2020_masked_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap/tracer_2020_masked_TC_org_2_TC_std',
        ],        
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_2020_masked_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap/tracer_weighted_2020_masked_TC_org_2_TC_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/cell_density_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap/cell_density_TC_org_2_TC_std',
        ],                
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/inj-mask_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap/inj-mask_TC_org_2_TC_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C03_vis_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap/tc-C03_vis_TC_org_2_TC_std',
        ],   
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/retrograde_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap/tc-retrograde_TC_std',
        ],   
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/retrograde_max_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap/tc-retrograde_max_TC_std',
        ],   
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg_converted/track_density_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap/track_density_TC_std',
        ]                     
      ]  
            
          
    def batch_run(self):
        #ants="/disk/k_raid/SOFTWARE/ANTS/bin/antsApplyTransforms "
        #ants = "/disk/k_raid/SOFTWARE//ANTS//bin/antsApplyTransforms"
        
        print("#I: creating dest folder")
    
        folder_name=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/flatmap/";
        mkdir="mkdir -p "+folder_name;
        print("#I: "+mkdir)
        res , folder_success  = pipetools.bash_run(mkdir)
        if not (folder_success):
                raise CPipeError("creating folder failed")
                
                
        print("#I: creating preview image folder")
        preview_folder=pipedef.PIPELINE_DATABSE_FOLDER+"/preview/"+format(self.mid)+"/";
        mkdir="mkdir -p "+preview_folder;
        print("#I: "+mkdir)
        res , folder_success  =  pipetools.bash_run(mkdir)
        if not (folder_success):
            raise CPipeError("#E: creating folders failed")                
                             
                             
        prev_path="\{PREVIEWFOLDER\}"+"/"+self.mid+"/"+pipe_step.name();
        
        if True:      
            
            img_list = ""
            fmap_list = ""
            preview_list = []
            progress = 0  
            #html="";
            for job in self.jobs:
              #print("#I 0 ")
              
              f_in = job[0].replace("#MID#",self.mid)
              f_out = job[1].replace("#MID#",self.mid)            
              #print(f_in)                
              #print(f_out)                
              #print("####################")                
              if os.path.isfile(f_in):
                      fn = f_out.split("/")
                      fn = fn[len(fn)-1]
                      #pimg = prev_path+fn+"large.jpg"
                      preview_list.append([f_out,fn])
                      #html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';";
                      #html+="echo '<td><img src=\""+pimg+"\" style=\"image-rendering: pixelated;\" width=100%></td>';";
                      #html+="echo '</div><br>';";                              
              
              if os.path.isfile(f_in) and not os.path.isfile(f_out+"-right.shape.gii"):
                  img_list += " "+f_in+" "
                  fmap_list += " "+f_out+" "
  
              else:
                  print(("skipping  "+f_out))
                  if not os.path.isfile(f_in):
                                    print(("missing input file "+(f_in)))
                  else:                 
                                    print("already exists")                                                       
                         
            
                
              
              
            print("##############################")              
              

            COMMAND =  [   
                        #"source /disk/soft/MODULES/init.sh",
                        #"source /etc/profile.d/modules.sh",
                        #"echo ${WORKON_HOME}",
                        #"workon pipeline3",
                        #"which python",               
                        #"echo ${WORKON_HOME}",      
                        "cd /disk/k_raid/KAKUSHIN-NOU-DATA/SOFT/pipeline/pipeline_local/flatmap",
                        "python pipeline_map2fmap.py --images "+img_list+" --flatmaps "+fmap_list,
                        "echo ###################"
                        ]            
         
         
            COMMAND = " && ".join(COMMAND)
            #COMMAND = "bash -c '" +COMMAND+"'"
            if len(img_list) >0:            
                print("#I: "+COMMAND)
                success  = pipetools.bash_run_and_print(COMMAND,executable='/bin/bash')
                #success  = pipetools.bash_run_and_print(COMMAND)
                if not (success):
                    raise CPipeError("error mapping to fmap")
                
            html=""
            if True:
                for pfile in preview_list:
                    print(("in : "+pfile[0]))
                    print(("out : "+pfile[1]))
                    
                    if True:
                        if len(html) == 0 :
                            pimg_disk = preview_folder+pipe_step.name()+"_small.jpg"
                            cmd = "convert -scale 20% " + pfile[0]+"-left_hot.png" + " " + pimg_disk
                            pimg_disk = preview_folder+pipe_step.name()+"_tiny.jpg"
                            cmd += " && convert -scale 10% " + pfile[0]+"-left_hot.png" + " " + pimg_disk
                            print("#I: "+cmd)
                            success  = pipetools.bash_run_and_print(cmd,executable='/bin/bash')
                            #success  = pipetools.bash_run_and_print(COMMAND)
                            if not (success):
                                raise CPipeError("error creating preview files")
                    
                    
                    pimg_l = prev_path+pfile[1]+"large-l.jpg"
                    pimg_disk = preview_folder+pipe_step.name()+pfile[1]+"large-l.jpg"
                    cmd = "convert " + pfile[0]+"-left_hot.png" + " " + pimg_disk
                    print("#I: "+cmd)
                    success  = pipetools.bash_run_and_print(cmd,executable='/bin/bash')
                    #success  = pipetools.bash_run_and_print(COMMAND)
                    if not (success):
                        raise CPipeError("error creating preview files")
                        
                    pimg_r = prev_path+pfile[1]+"large-r.jpg"
                    pimg_disk = preview_folder+pipe_step.name()+pfile[1]+"large-r.jpg"
                    cmd = "convert -flop " + pfile[0]+"-right_hot.png" + " " + pimg_disk
                    print("#I: "+cmd)
                    success  = pipetools.bash_run_and_print(cmd,executable='/bin/bash')
                    #success  = pipetools.bash_run_and_print(COMMAND)
                    if not (success):
                        raise CPipeError("error creating preview files")
                        
                    html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';";
                    html+="echo '<table width=\"100%\">';";
                    html+="echo '<td style=\"align: center;\">"+pfile[1]+"</td>';";
                    html+="echo '<tr>';";
                    html+="echo '<td><img src=\""+pimg_r+"\" style=\"image-rendering: pixelated;\" width=100%></td>';";
                    html+="echo '<td><img src=\""+pimg_l+"\" style=\"image-rendering: pixelated;\" width=100%></td>';";
                    html+="echo '</tr>';";
                    html+="echo '</table>';";
                    html+="echo '</div><br>';";      
                    
            print("#I: adding detailed preview data to table") 
            self.sql_add_custome_data("details",html.replace("'","\\\'"),"VARCHAR(20000)");
            print("#I: done") 
                
                    
          
    def batch_clean(self):
        pass
        
        
        
try:
    #pipe_step=CPipeStepTrafos({'kn_pipeline_meso_reg2TCstd.py','kn_pipeline_meso_inj_seg.py','kn_pipeline_meso_axonfilt_3D.py'},shortname="meso-atrafo");
    pipe_step=CPipeStepFmap({'kn_pipeline_meso_apply_trafos_TC.py','kn_pipeline_meso_NN_cells_3D.py','kn_pipeline_meso_NN_tracerseg_3D.py'},shortname="meso-fmap")
    print("#I: scriptname is \""+pipe_step.name()+"\"")
    pipe_step.print_settings()
    #print("222")
    #print("bla {}".format(pipe_step.jobs))
    #print("2222")
    slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':4,'mem':64000,'gres':"KN:5",'feature':''}
    pipe_step.run(slurm_params,{'kn_pipeline_meso_flatmap_stack.py'})
       
    
    
except CPipeError as e:
    print("#E: "+e.value)



