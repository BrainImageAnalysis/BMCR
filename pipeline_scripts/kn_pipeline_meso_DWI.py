#!/usr/bin/env python

import sys
import os
import math
import subprocess
#import pandas as pd
from os.path import isfile, join, isdir

from kn_common import pipetools,pipedef
from kn_pipeline_class import CPipeError,CPipeStep
import torch
import torch.nn as nn
import torch.nn.functional as F
import hashlib
import nibabel as nib
import numpy as np

class CPipeStepDWI(CPipeStep):

    def batch_run(self):
        
        print("#I: creating dest folder")
    
        folder_name=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/"

        track_in = pipedef.PIPELINE_DATABSE_FOLDER+"/model/SYN_HARDI/merged_sym.tck"
        track_out = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/meta/track.tck"
        injection_site = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/cell_density_TC_org_2_TC_std.nii.gz"
        template = pipedef.PIPELINE_DATABSE_FOLDER+"/model/avg_TC_std.nii.gz"
        dens_img_org = folder_name+"/track_density_200mu_TC_std.nii.gz"

        if True:
            cmd = "tckedit "+track_in+"  "+track_out+" -include "+injection_site+" --force "
            success  = pipetools.bash_run_and_print(cmd,executable='/bin/bash')
            #success  = pipetools.bash_run_and_print(COMMAND)
            if not (success):
                raise CPipeError("error creating track")

            
            
            cmd = "tckmap -template "+template+"  "+track_out+" "+dens_img_org+" -precise -force -vox 0.2"        
            success  = pipetools.bash_run_and_print(cmd,executable='/bin/bash')
            #success  = pipetools.bash_run_and_print(COMMAND)
            if not (success):
                raise CPipeError("error creating track density image")      


        img_ref = nib.load(pipedef.PIPELINE_DATABSE_FOLDER+"/model//avg_TC_std.nii.gz")
        
        folder_name2 = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg_converted/"
        os.makedirs(folder_name2,exist_ok=True)
        dens_img_std = folder_name2+"/track_density_TC_std.nii.gz"
        
        #%%
        img_2 = nib.load(dens_img_org)
        data = img_2.get_fdata() 
        #%%
        target_shape = img_ref.shape
        data_t = torch.Tensor(data)
        #data_t2 = F.interpolate(data_t[None,None,:,:,:], size=target_shape,mode='trilinear',align_corners=True)
        data_t2 = F.interpolate(data_t[None,None,:,:,:], size=target_shape,mode='trilinear',align_corners=False)
        #%%
        dmax = data_t2.max().item()
        if dmax>0.0000001:
            scaling = ((2**16-1)/dmax)
        else:
            scaling = 1
        new_image = nib.Nifti1Image((data_t2[0,0,...].numpy()*scaling).astype(np.uint16), affine=img_ref.affine)
        new_image.header["scl_inter"] = 0
        new_image.header["scl_slope"] = 1.0/scaling
        new_image.header["glmax"] = dmax
        new_image.header["glmin"] = 0
        #new_image = nib.Nifti1Image(data_t2.numpy().astype(np.uint16), affine=img_ref.affine)
        nib.save(new_image,dens_img_std)
  
                    
          
    def batch_clean(self):
        pass
        
        
        
try:
    #pipe_step=CPipeStepTrafos({'kn_pipeline_meso_reg2TCstd.py','kn_pipeline_meso_inj_seg.py','kn_pipeline_meso_axonfilt_3D.py'},shortname="meso-atrafo");
    pipe_step=CPipeStepDWI({'kn_pipeline_meso_apply_trafos_TC.py','kn_pipeline_meso_NN_cells_3D.py'},shortname="meso-fmap")
    print("#I: scriptname is \""+pipe_step.name()+"\"")
    pipe_step.print_settings()
    #print("222")
    #print("bla {}".format(pipe_step.jobs))
    #print("2222")
    slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':4,'mem':64000,'gres':"KN:5",'feature':''}
    #pipe_step.run(slurm_params,{"kn_pipeline_meso_norm_tracer.py"})
    pipe_step.run(slurm_params,{"kn_pipeline_meso_nifti_convert.py"})
       
    
    
except CPipeError as e:
    print("#E: "+e.value)



