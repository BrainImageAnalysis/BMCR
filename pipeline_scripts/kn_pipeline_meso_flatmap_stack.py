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
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_2020_masked_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/tracer_2020_masked_TC_org_2_TC_std',
        ],        
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_2020_masked_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/tracer_weighted_2020_masked_TC_org_2_TC_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_masked_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/tracer_masked_TC_org_2_TC_std',
        ],        
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_masked_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/tracer_weighted_masked_TC_org_2_TC_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/cell_density_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/cell_density_TC_org_2_TC_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C03_vis_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/tc-C03_vis_TC_org_2_TC_std',
        ],   
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/retrograde_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/tc-retrograde_TC_std',
        ], 
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/retrograde_max_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/tc-retrograde_max_TC_std',
        ], 
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg_converted/track_density_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/track_density_TC_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg_converted/tracer_normalized_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/tracer_normalized_TC_org_2_TC_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg_converted/anterograde2_smoothed_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/anterograde2_smoothed_TC_org_2_TC_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg_converted/anterograde2_max_TC_org_2_TC_std.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/anterograde2_max_TC_org_2_TC_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg_converted/dist_map_m.nii.gz.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/streamline_dist_map_m_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg_converted/dist_map_i.nii.gz.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/streamline_dist_map_i_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg_converted/dist_map_i_sharp.nii.gz.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/streamline_dist_map_i_sharp_std',
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg_converted/paths.nii.gz.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/streamline_paths_std',
        ]

      ]  
    jobs = [ 
    [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/streamlines/dist_map_m.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/streamline_dist_map_m_std',
        "NearestNeighbor"
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/streamlines/dist_map_i.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/streamline_dist_map_i_std',
        "NearestNeighbor"
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/streamlines/dist_map_i_sharp.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/streamline_dist_map_i_sharp_std',
        "NearestNeighbor"
        ],
        [
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/streamlines/paths.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/flatmap_stack/streamline_paths_std',
        "NearestNeighbor"
        ]
    ]      
          
    def batch_run(self):
        #ants="/disk/k_raid/SOFTWARE/ANTS/bin/antsApplyTransforms "
        #ants = "/disk/k_raid/SOFTWARE//ANTS//bin/antsApplyTransforms"
        
        print("#I: creating dest folder")
    
        folder_name=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/flatmap_stack/";
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
              interp = job[2] if len(job) == 3 else "Linear"
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
                        
              if os.path.isfile(f_in):# and not os.path.isfile(f_out+"_stack_r.nii.gz"):
              #if os.path.isfile(f_in) and not os.path.isfile(f_out+"_stack_r.nii.gz"):
                  img_list += " "+f_in+" "
                  fmap_list += " "+f_out+" "
  
              else:
                  print(("skipping  "+f_out))
                  if not os.path.isfile(f_in):
                                    print(("missing input file "+(f_in)))
                  else:                 
                                    print("already exists")                                                       
                         
            
            COMMAND_BM =  [   
                        "cd /disk/k_raid/KAKUSHIN-NOU-DATA/SOFT/pipeline/pipeline_local/flatmap",
                        "python fmap_stack_ants.py --images "+img_list+" --flatmaps "+fmap_list+" --mid "+"_".join(self.mid.split("_")[:2])+" --image_space BMAv2 --interpolation "+interp
                        ]        

            #COMMAND = " && ".join(COMMAND)

            COMMAND_MBM =  [   
                        "cd /disk/k_raid/KAKUSHIN-NOU-DATA/SOFT/pipeline/pipeline_local/flatmap",
                        "python fmap_stack_ants.py --images "+img_list+" --flatmaps "+fmap_list+" --postfix 2021MBM" +" --mid "+"_".join(self.mid.split("_")[:2])+" --image_space MBMv3 --interpolation "+interp
                        #"python fmap_stack_2021.py --images "+img_list+" --flatmaps "+fmap_list+" --mapfolder fmap_stack_2021_MBM/ --postfix 2021MBM" 
                        ]        


            
            COMMAND = " && ".join(COMMAND_BM)  
           # print("###")
           # print(COMMAND)
            COMMAND = COMMAND +" && "+ (" && ".join(COMMAND_MBM))
                

            #COMMAND = "bash -c '" +COMMAND+"'"
            if len(img_list) >0:            
                print("#I: "+COMMAND)
                success  = pipetools.bash_run_and_print(COMMAND,executable='/bin/bash')
                #success  = pipetools.bash_run_and_print(COMMAND)
                if not (success):
                    raise CPipeError("error mapping to fmap")
                
            
                
                    
          
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
    #pipe_step.run(slurm_params,{'kn_pipeline_riken_sync.py','kn_pipeline_riken_backup.py'})
    pipe_step.run(slurm_params,{})
       
    
    
except CPipeError as e:
    print("#E: "+e.value)



