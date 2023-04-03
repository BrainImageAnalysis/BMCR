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

class CPipeStepNormTracer(CPipeStep):

    def batch_run(self):
        #ants="/disk/k_raid/SOFTWARE/ANTS/bin/antsApplyTransforms "
        #ants = "/disk/k_raid/SOFTWARE//ANTS//bin/antsApplyTransforms"
        
        print("#I: creating dest folder")
        
        #folder_name=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/"

        injection_site = nib.load(pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/inj/cell_density_TC_org.nii.gz")
        
        tracer_data = nib.load(pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/NN_tracer/NN_tracer_weighted_2020_masked.nii.gz")
        #tracer_data = nib.load(pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/NN_tracer/NN_tracer_weighted_2020_masked_smoothz.nii.gz")

        tracer_inj_site = injection_site.get_fdata() 
        tracer = tracer_data.get_fdata().astype(np.float32) 

        threshold_percent = 0.01
        
        inj_mask = tracer_inj_site > 0
        all_tracer_mask = tracer > 0
        
        tracer_mask = np.logical_and(all_tracer_mask,np.logical_not(inj_mask))
        tracer_intensities = np.sort(tracer[tracer_mask[:]])
        
        threshold =  tracer_intensities[round(tracer_intensities.shape[0]*(1-threshold_percent))]
        tracer_normalized = np.minimum(tracer/threshold,1.0)
        

#        tr_img = (2**16-1)*tracer_normalized
        tr_img = tracer_normalized

       # print("#I: max signal {}, dtype {}".format(max_signal,tracer_site_data.dtype))
        new_image = nib.Nifti1Image(tr_img, affine=tracer_data.affine,header=tracer_data.header)
        new_image.header["scl_inter"] = 0
        new_image.header["scl_slope"] = 100.0#/(2**16-1)
        new_image.header["glmax"] = 100.0
        new_image.header["glmin"] = 0
        
#        new_image.header['bitpix'] = 16
 #       new_image.header['datatype'] = 512
        
        
        #new_image = nib.Nifti1Image(data_t2.numpy().astype(np.uint16), affine=img_ref.affine)
        tracer_norm = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/NN_tracer/tracer_normalized.nii.gz"
        nib.save(new_image,tracer_norm)
        #tracer_norm = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg_converted/tracer_normalized_TC_std.nii.gz"
        #nib.save(new_image,tracer_norm)
        
        if False:
            print("#I: creating dest folder")
        
            folder_name=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/"
    
            injection_site = nib.load(pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/cell_density_TC_org_2_TC_std.nii.gz")
            tracer = nib.load(pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/tracer_weighted_2020_masked_TC_org_2_TC_std.nii.gz")
    
            injection_site_data = injection_site.get_fdata() 
            tracer_site_data = tracer.get_fdata().astype(np.float32) 
    
            valid = tracer_site_data[injection_site_data<0.000001]
    
            max_signal = valid.max()
            tr_img = (2**16-1)*np.minimum(tracer_site_data/max_signal,1.0)
    
            print("#I: max signal {}, dtype {}".format(max_signal,tracer_site_data.dtype))
            new_image = nib.Nifti1Image(tr_img.astype(np.uint16), affine=tracer.affine,header=tracer.header)
            new_image.header["scl_inter"] = 0
            new_image.header["scl_slope"] = 1.0/(2**16-1)
            new_image.header["glmax"] = 1.0
            new_image.header["glmin"] = 0
            #new_image = nib.Nifti1Image(data_t2.numpy().astype(np.uint16), affine=img_ref.affine)
            tracer_norm = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/tracer_normalized_TC_std.nii.gz"
            nib.save(new_image,tracer_norm)
            tracer_norm = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg_converted/tracer_normalized_TC_std.nii.gz"
            nib.save(new_image,tracer_norm)
                    
          
    def batch_clean(self):
        pass
        
        
        
try:
    #pipe_step=CPipeStepTrafos({'kn_pipeline_meso_reg2TCstd.py','kn_pipeline_meso_inj_seg.py','kn_pipeline_meso_axonfilt_3D.py'},shortname="meso-atrafo");
    pipe_step=CPipeStepNormTracer({'kn_pipeline_meso_NN_cells_3D.py','kn_pipeline_meso_NN_tracerseg_3D.py'},shortname="meso-fmap")
    print("#I: scriptname is \""+pipe_step.name()+"\"")
    pipe_step.print_settings()
    #print("222")
    #print("bla {}".format(pipe_step.jobs))
    #print("2222")
    slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':4,'mem':64000,'gres':"KN:5",'feature':''}
    pipe_step.run(slurm_params,{"kn_pipeline_meso_apply_trafos_TC.py"})
       
    
    
except CPipeError as e:
    print("#E: "+e.value)



