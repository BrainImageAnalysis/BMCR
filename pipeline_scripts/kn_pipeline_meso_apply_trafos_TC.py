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

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()





def file_timestamp(fname):
    return os.stat(fname).st_mtime    

class CPipeStepTrafos(CPipeStep):

    reg_name = "img3D_bg_TC_org.nii.gz"
    
    jobs = [ 
        ['alex_std_2_TC_org','MultiLabel',#MultiLabel
        pipedef.PIPELINE_DATABSE_FOLDER+'/model/mod-dir-average_brain/mod-dir-Atlas_LabelMap_v2.nii',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/labelmap_MRI_std_2_TC_org.nii.gz'],        
        #['TC_org_2_alex_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/axonfilter/tracer_masked_org250.nii.gz',
 #       pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_MRI_std.nii.gz'],
          ['TC_org_2_alex_std','NearestNeighbor',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/inj/inj_mask_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/inj-mask_TC_org_2_MRI_std.nii.gz'],    
         ['TC_org_2_TC_std','NearestNeighbor',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/inj/inj_mask_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/inj-mask_TC_org_2_TC_std.nii.gz'],    
          ['TC_org_2_alex_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3D_vis_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C01_vis_TC_org_2_MRI_std.nii.gz'],        
        ['TC_org_2_alex_std','Linear',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c2/img3D_vis_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C02_vis_TC_org_2_MRI_std.nii.gz'],        
        ['alex_std_2_TC_org','Linear',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c3/img3D_vis_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C03_vis_TC_org_2_MRI_std.nii.gz'],    
         ['TC_org_2_alex_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C01_TC_org_2_MRI_std.nii.gz'],        
        ['TC_org_2_alex_std','Linear',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c2/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C02_TC_org_2_MRI_std.nii.gz'],        
        ['alex_std_2_TC_org','Linear',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c3/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C03_TC_org_2_MRI_std.nii.gz'],    
          ['alex_std_2_TC_org','Linear',
        pipedef.PIPELINE_DATABSE_FOLDER+'/model/avg_MRI_std.nii',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/avg_MRI_std_2_TC_org.nii.gz'],   
                ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_2020_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_2020_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_weighted_2020_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_2020_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_2020_masked_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_2020_masked_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_weighted_2020_masked_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_2020_masked_TC_org_2_TC_std.nii.gz'],   
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_weighted.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_masked.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_masked_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_weighted_masked.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_masked_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/inj/cell_density_TC_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/cell_density_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_TC_std','NearestNeighbor',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/inj/inj_center_TC_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/inj_center_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_alex_std','NearestNeighbor',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/inj/inj_center_TC_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/inj_center_TC_org_2_MRI_std.nii.gz'],
               ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_2020_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_2020_TC_org_2_MRI_std.nii.gz'],
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_weighted_2020_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_2020_TC_org_2_MRI_std.nii.gz'],#pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_MRI_org_2_TC_std.nii.gz'],
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_2020_masked_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_2020_masked_TC_org_2_MRI_std.nii.gz'],
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_weighted_2020_masked_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_2020_masked_TC_org_2_MRI_std.nii.gz'],
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_TC_org_2_MRI_std.nii.gz'],
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_weighted.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_TC_org_2_MRI_std.nii.gz'],#pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_MRI_org_2_TC_std.nii.gz'],
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_masked.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_masked_TC_org_2_MRI_std.nii.gz'],
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_weighted_masked.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_masked_TC_org_2_MRI_std.nii.gz'],#pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_masked_MRI_org_2_TC_std.nii.gz'],
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/inj/cell_density_TC_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/cell_density_TC_org_2_MRI_std.nii.gz'],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/Nissl/Nissl_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/Nissl_TC_org_2_TC_std.nii.gz',True],
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/Nissl/Nissl_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/Nissl_TC_org_2_MRI_std.nii.gz',True],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/Nissl/Nissl_NN_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/Nissl_NN_TC_org_2_TC_std.nii.gz',True],
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/Nissl/Nissl_NN_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/Nissl_NN_TC_org_2_MRI_std.nii.gz',True],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/Nissl/Backlit_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/Backlit_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/Nissl/Backlit_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/Backlit_TC_org_2_MRI_std.nii.gz'],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/Nissl/Backlit_NN_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/Backlit_NN_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/Nissl/Backlit_NN_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/Backlit_NN_TC_org_2_MRI_std.nii.gz'],
        ['TC_std_2_TC_org','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/model/avg_TC_std.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/avg_TC_std_TC_std_2_TC_org.nii.gz'],
         ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3D_vis_TC_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C01_vis_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c2/img3D_vis_TC_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C02_vis_TC_org_2_TC_std.nii.gz'],
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c3/img3D_vis_TC_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C03_vis_TC_org_2_TC_std.nii.gz'],
        ['TC_std_2_TC_org','NearestNeighbor',
             pipedef.PIPELINE_DATABSE_FOLDER+'/model/lr_TC_std.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/lr_TC_std_2_TC_org.nii.gz'],
        ['TC_org_2_TC_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C01_TC_org_2_TC_std.nii.gz'],           
        ['TC_org_2_TC_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c2/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C02_TC_org_2_TC_std.nii.gz'],           
        ['TC_org_2_TC_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c3/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C03_TC_org_2_TC_std.nii.gz'],    
        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/tracer_normalized.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_normalized_TC_org_2_TC_std.nii.gz'],  
        ['TC_org_2_alex_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/tracer_normalized.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_normalized_TC_org_2_MRI_std.nii.gz'],  
        ###################
        ###################
        ###################
        #  MBMv3
        ###################
        ###################
        ###################        
        ['TC_org_2_MBM3_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C01_TC_org_2_MBMv3_std.nii.gz'],           
        ['TC_org_2_MBM3_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c2/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C02_TC_org_2_MBMv3_std.nii.gz'],           
        ['TC_org_2_MBM3_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c3/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C03_TC_org_2_MBMv3_std.nii.gz'],     
        ['TC_org_2_MBM3_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/inj/cell_density_TC_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/cell_density_TC_org_2_MBMv3_std.nii.gz'],   
        ['TC_org_2_MBM3_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_2020_masked_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_2020_masked_TC_org_2_MBMv3_std.nii.gz'],
        ['TC_org_2_MBM3_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_weighted_2020_masked_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_2020_masked_TC_org_2_MBMv3_std.nii.gz'],   
        ['TC_org_2_MBM3_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/tracer_normalized.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_normalized_TC_org_2_MBMv3_std.nii.gz'],   
       #  MBMv2
        ###################
        ###################
        ###################        
        ['TC_org_2_MBM2_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C01_TC_org_2_MBMv2_std.nii.gz'],           
        ['TC_org_2_MBM2_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c2/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C02_TC_org_2_MBMv2_std.nii.gz'],           
        ['TC_org_2_MBM2_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c3/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C03_TC_org_2_MBMv2_std.nii.gz'],     
        ['TC_org_2_MBM2_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/inj/cell_density_TC_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/cell_density_TC_org_2_MBMv2_std.nii.gz'],   
        ['TC_org_2_MBM2_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_2020_masked_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_2020_masked_TC_org_2_MBMv2_std.nii.gz'],
        ['TC_org_2_MBM2_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_weighted_2020_masked_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_2020_masked_TC_org_2_MBMv2_std.nii.gz'],   
        ['TC_org_2_MBM2_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/tracer_normalized.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_normalized_TC_org_2_MBMv2_std.nii.gz'],   
          ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/Anterograde01/anterograde_max.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/anterograde2_max_TC_org_2_TC_std.nii.gz'],
          ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/Anterograde01/anterograde2_smoothed.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/anterograde2_smoothed_TC_org_2_TC_std.nii.gz'],
             
        ]
          
    jobs_ = [ 
               ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/Anterograde01/anterograde_max.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/anterograde2_max_TC_org_2_TC_std.nii.gz'],
                        ['TC_org_2_TC_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/Anterograde01/anterograde2_smoothed.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/anterograde2_smoothed_TC_org_2_TC_std.nii.gz'],
             ] 
             
    jobs_ = [
        ['TC_org_2_MBM_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C01_TC_org_2_MBM_std.nii.gz'],           
        ['TC_org_2_MBM_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c2/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C02_TC_org_2_MBM_std.nii.gz'],           
        ['TC_org_2_MBM_std','Linear',
        #pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c1/img3Dcubic_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/c3/img3D_raw_TC_org.nii.gz',
        pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tc-C03_TC_org_2_MBM_std.nii.gz'],     
        ['TC_org_2_MBM_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/inj/cell_density_TC_org.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/cell_density_TC_org_2_MBM_std.nii.gz'],   
        ['TC_org_2_MBM_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_2020_masked_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_2020_masked_TC_org_2_MBM_std.nii.gz'],
        ['TC_org_2_MBM_std','Linear',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/NN_tracer/NN_tracer_weighted_2020_masked_smoothz.nii.gz',
             pipedef.PIPELINE_DATABSE_FOLDER+'/#MID#/tissuecyte/3d/reg/tracer_weighted_2020_masked_TC_org_2_MBM_std.nii.gz'],       
        
             ]
    def batch_run(self):
        #ants="/disk/k_raid/SOFTWARE/ANTS/bin/antsApplyTransforms "
        ants = pipedef.ants
        antsRGB =  pipedef.matlab_bin+" "
        
        TC_org_2_TC_std = pipedef.PIPELINE_DATABSE_FOLDER+'/'+self.mid+'/meta/trafos/reg2TC/trafo-finalComposite.h5'
        TC_org_2TC_std_inv = pipedef.PIPELINE_DATABSE_FOLDER+'/'+self.mid+'/meta/trafos/reg2TC/trafo-finalInverseComposite.h5'
        
        alex_std_2_alex_highers = pipedef.PIPELINE_DATABSE_FOLDER+'/model/skibbe-h/tools/trafos/mod-dir-AverageBrain2_Isotropic_TO_ALEXMRI_std_affine01Composite.h5'
        alex_std_2_alex_highers_inv= pipedef.PIPELINE_DATABSE_FOLDER+'/model/skibbe-h/tools/trafos/mod-dir-AverageBrain2_Isotropic_TO_ALEXMRI_std_affine01InverseComposite.h5'
        
        alex_highers_2_TC_std = pipedef.PIPELINE_DATABSE_FOLDER+'/model/skibbe-h/tools/trafos/ALEXMRI_std_TO_avg_std_finalComposite.h5'
        alex_highers_2_TC_std_inv= pipedef.PIPELINE_DATABSE_FOLDER+'/model/skibbe-h/tools/trafos/ALEXMRI_std_TO_avg_std_finalInverseComposite.h5'


        MBM3_2_STD = pipedef.PIPELINE_DATABSE_FOLDER+'/model/EXTERN/MBM_v3/MBM_2_STPT.h5'
        STD_2_MBM3 = pipedef.PIPELINE_DATABSE_FOLDER+'/model/EXTERN/MBM_v3/STPT_2_MBM.h5'

        MBM2_2_STD = pipedef.PIPELINE_DATABSE_FOLDER+'/model/EXTERN/MBM_v2/MBM_2_STPT.h5'
        STD_2_MBM2 = pipedef.PIPELINE_DATABSE_FOLDER+'/model/EXTERN/MBM_v2/STPT_2_MBM.h5'

        file_checksum_states  = pipedef.PIPELINE_DATABSE_FOLDER+'/'+self.mid+'/meta/transformed.json'
        file_checksums = {}

        if os.path.isfile(file_checksum_states):
            file_checksums, success = pipetools.json_read(file_checksum_states)
            if not (success):
                    raise CPipeError("error reading timestamp file")
            print("#I updating ")
        else:
            print("#I starting from zero ")
            

        trafos={
             'TC_org_2_TC_std':' '+TC_org_2_TC_std,
             'TC_std_2_TC_org':' '+TC_org_2TC_std_inv,
             'TC_org_2_alex_std':' '+alex_std_2_alex_highers_inv+' '+alex_highers_2_TC_std_inv+' '+TC_org_2_TC_std+' ',
             'alex_std_2_TC_org':' '+TC_org_2TC_std_inv+' '+alex_highers_2_TC_std+' '+alex_std_2_alex_highers+' ',
             'TC_org_2_MBM3_std':' '+STD_2_MBM3+' '+' '+TC_org_2_TC_std+' ',
             'TC_org_2_MBM2_std':' '+STD_2_MBM2+' '+' '+TC_org_2_TC_std+' ',
            }    
        references={
            'TC_org_2_alex_std':pipedef.PIPELINE_DATABSE_FOLDER+'/model/avg_MRI_std.nii',
             'TC_org_2_TC_std':pipedef.PIPELINE_DATABSE_FOLDER+'/model/avg_TC_std.nii.gz',
            'alex_std_2_TC_org':pipedef.PIPELINE_DATABSE_FOLDER+self.mid+'/tissuecyte/3d/reg/'+self.reg_name,
            'TC_std_2_TC_org':pipedef.PIPELINE_DATABSE_FOLDER+self.mid+'/tissuecyte/3d/reg/'+self.reg_name,
            'TC_org_2_MBM3_std':pipedef.PIPELINE_DATABSE_FOLDER+'/model/EXTERN/reference_imgs/MBM_v3/template_T2w_brain.nii.gz',
            'TC_org_2_MBM2_std':pipedef.PIPELINE_DATABSE_FOLDER+'/model/EXTERN/reference_imgs/MBM_v2/Template_sym_T2_80um.nii.gz',
            }
        
        if True:      
            progress = 0  
            for job in self.jobs:
              #print("#I 0 ")
              trafo_type=job[0]
              interp_type=job[1]
              img_in=job[2].replace("#MID#",self.mid)
              img_out=job[3].replace("#MID#",self.mid)
                
              #print("#I 1 ")
              hash_path, hash_filename = os.path.split(img_out)
              #print("#I 2 ")
              file_hash_old = str("A")
              file_hash_new = str("B")
              if hash_filename in file_checksums:
                  file_hash_old = str(file_checksums[hash_filename])

              #print("#I 3 ")
              if os.path.isfile(img_out):
                file_hash_new = str(file_timestamp(img_in))
                print(("#I: getting timestamp from file: "+img_out))
              else:
                print(("#W: the file '"+img_out+"' does not exist"))

              #print("#I 4 ")
              

    
              img_ref=references[trafo_type]
              if not os.path.isfile(img_in):
                  print("#W: "+img_in+" is not a file, skipping")
              else:
                print(("#W: old hash :"+file_hash_old))
                print(("#W: new hash :"+file_hash_new))
                #if False:
                if (file_hash_old == file_hash_new) and (os.path.isfile(img_out)):
                    print(("#W: "+hash_filename+" is up-to-date, skipping"))
                else:
                    print(("#W: updating "+hash_filename))
                    #if not os.path.isfile(img_in):
                    #raise CPipeError(img_in+" is not a file")
                    if not os.path.isfile(img_ref):
                        raise CPipeError(img_ref+" is not a file")
                    
                    out_img_folder, out_img_fname=os.path.split(img_out)  
                    if not os.path.isdir(out_img_folder):
                        print("#W: "+out_img_folder+" does not exist; creating folder")
                        self.local_mkdir(out_img_folder)
                    
                            
                    if len(job) == 5 and job[4]: # then its RGB
                        command = antsRGB+' -r "addpath /disk/k_raid/KAKUSHIN-NOU-DATA/SOFT/pipeline/pipeline_local/matlab/; \
                        ants_register_rgb(\''+img_in+'\',\''+img_out+'\',\' -r '+img_ref+' -n '+interp_type+' -t '+trafos[trafo_type]+' \');exit;"'
                        print(("#I {}".format(command)))
                        
                        #command = antsRGB+' -r "addpath /disk/k_raid/SOFTWARE/KAKUSHI-NOU/pipeline/tissuecyte; exit;'
                        print("#I registering an RGB image")
                    else:        
                        #command=ants+" "+img_in+" "+img_out+" -R "+img_ref+" "+interp_type+" "+trafos[trafo_type]
                        command=ants+" --float -v 1 -i "+img_in+" -o "+img_out+" -r "+img_ref+" -n "+interp_type+" -t "+trafos[trafo_type]
                        print("#I registering a single channele image")
                    
                    if True:            
                        print("#I: "+command)
                        success  = pipetools.bash_run_and_print(command)
                        if not (success):
                            raise CPipeError("error applying the transformation")
            
                
                    #md5_hash = md5(file_checksums)
                    #print("#I 5 ")
                    #print("#I hash_filename :"+hash_filename)
                    #print("#I hash :"+str(file_hash_new))
                    #print("{}".format(file_checksums))
                    file_hash_new = str(file_timestamp(img_in))
                    file_checksums[hash_filename] = str(file_hash_new)
                    #print("#I 6 ")
            progress += 1
            self.update_progress("run",100*float(progress)/len(self.jobs))
        #print("#I 7 ")
        #print("{}".format(file_checksum_states))
        #print("{}".format(file_checksums))
        pipetools.json_write(file_checksums,file_checksum_states)
        #print("#I 8 ")
          
    def batch_clean(self):
        #pass
        #ofolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/";
        clearme=[]
        for job in self.jobs:
          img_out=job[3].replace("#MID#",self.mid)
          clearme=clearme+[img_out]
        
        deldir_basedir=pipedef.PIPELINE_KN_RAID_DEL+"/"
        deldir=self.mid+pipetools.get_folder_timestamp()
        self.local_mkdir(deldir_basedir+deldir)
        
        for delme in clearme:
          print("#W: deleting "+delme+"")
          if not os.path.isfile(delme):
            print("#W: skipping "+delme+", does not exist")
          else:  
            self.local_mv(delme,deldir_basedir+deldir)
              
        SLURM_command={"cd "+deldir_basedir+" && rm "+deldir+" -r"}
        
        res, success=pipetools.slurm_submit(SLURM_command,self.ofile,name=self.mid+"-CLEAN-"+self.shortname,queue="kn_pipe_cleanup")
        if not success:
            raise CPipeError("submitting cleaning script failed "+format(res[0]));              
        
        
try:
    #pipe_step=CPipeStepTrafos({'kn_pipeline_meso_reg2TCstd.py','kn_pipeline_meso_inj_seg.py','kn_pipeline_meso_axonfilt_3D.py'},shortname="meso-atrafo");
    #pipe_step=CPipeStepTrafos({'kn_pipeline_meso_reg2TCstd.py','kn_pipeline_meso_inj_seg.py'},shortname="meso-atrafo")
    pipe_step=CPipeStepTrafos({'kn_pipeline_meso_reg2TCstd.py','kn_pipeline_meso_inj_seg.py','kn_pipeline_meso_NN_tracerseg_3D.py','kn_pipeline_meso_NN_cells_3D.py'},shortname="meso-atrafo")
    print("#I: scriptname is \""+pipe_step.name()+"\"")
    pipe_step.print_settings()
    #print("222")
    #print("bla {}".format(pipe_step.jobs))
    #print("2222")
    slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':4,'mem':32000,'gres':"KN:5",'feature':''}
    #pipe_step.run(slurm_params,{'kn_pipeline_meso_create_labels.py',"kn_pipeline_meso_nifti_convert.py"})
    pipe_step.run(slurm_params,{'kn_pipeline_meso_create_labels.py',"kn_pipeline_meso_inj_center.py"})
    
    
    
except CPipeError as e:
    print("#E: "+e.value)



