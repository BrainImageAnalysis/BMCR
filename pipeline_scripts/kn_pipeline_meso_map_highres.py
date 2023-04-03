#!/usr/bin/env python

import sys
import os
import math
import re
from os.path import isfile, join, isdir
import imageio
import numpy as np


from kn_common import pipetools,pipedef
from kn_pipeline_class import CPipeError,CPipeStep


class CPipeStepHighResMap(CPipeStep):


    matlab_tools=pipedef.maltab_tools
    matlab_bin=pipedef.maltab_bin
    data = [["c1_50mu","c1_50mu",-1],["c2_50mu","c2_50mu",-1],["c3_50mu","c3_50mu",-1],["NN_tracer","NN_tracer",-1],]
    #data = [["c1_50mu","c1_50mu",-1],["c2_50mu","c2_50mu",-1],["c3_50mu","c3_50mu",-1],["NN_tracer","NN_tracer",-1],["Backlit/first_match","Backlit",-1],["Nissl/first_match","Nissl_R",1],["Nissl/first_match","Nissl_G",2],["Nissl/first_match","Nissl_B",3]]
    data_merge_2_rgb = [{"R":"Nissl_R","G":"Nissl_G","B":"Nissl_B","RGB":"Nissl_RGB"}]
    data_merge_2_rgb = []
   # data = [["Backlit/first_match","Backlit",-1],["Nissl/first_match","Nissl_R",1],["Nissl/first_match","Nissl_G",2],["Nissl/first_match","Nissl_B",3]]

    #data = ["c1_50mu"]
    def batch_run(self):


        success=True
        progress = 0
        for data_ in self.data:
            print(data_)
            channel = -1
            data_in = data_[0]
            data_out = data_[1]
            channel = data_[2]
            
           
            ofolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/reg/"+data_out+"/"

            if not os.path.isdir(ofolder):

                MCOMMAND='cd '+self.matlab_tools+'/; addpath(pwd);'
                MCOMMAND+="tissuecute_slice_map_to_slice_TC_std_ANTS('"+self.mid+"','"+data_in+"','"+data_out+"',"+str(channel)+");"
                MCOMMAND+='exit;'

                COMMAND=self.matlab_bin+" -r \""+MCOMMAND+"\""

                success  = pipetools.bash_run_and_print(COMMAND)

                if not success:
                    raise CPipeError("highres mapping data "+format(data_in)+" failed")
            else:
                print("folder for "+data_out+" already exisits. skipping ..")

            allfiles_and_folders =os.listdir(ofolder)
            allfiles_and_folders.sort()
            allslices = [f for f in allfiles_and_folders if isfile(join(ofolder, f)) and "slice" in f and "png" in f]
            num_slices = len(allslices)
            #allfiles_and_folders.reverse()
            #if channel != -1:
            #    data = data+str(channel)
            files_order_reversed = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/reg/"+data_out+"_reversed/"
            if not os.path.isdir(files_order_reversed) and os.path.isdir(ofolder):
                print("creating reversed symlinks")            
                os.mkdir(files_order_reversed)
                for f in range(num_slices):
                    
                    link_from = "../"+data_out+"/"+"slice"+str(10000+num_slices-f-1)+".png"
                    link_to = files_order_reversed+"/"+str(10000+f)+".png"
                    os.symlink(link_from,link_to)
                    print("from {}".format(link_from))
                    print("to {}".format(link_to))
                    
        
            
            progress += 90.0 / float(len(self.data))
            self.update_progress("run",int(progress))

        for data_ in self.data_merge_2_rgb:
            dataR = data_["R"]
            dataG = data_["G"]
            dataB = data_["B"]
            dataRGB = data_["RGB"]
            ofolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/reg/"+dataRGB+"_reversed/"
            
            if not os.path.isdir(ofolder):
                os.makedirs(ofolder,exist_ok=True)
                
                channel_R_dir = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/reg/"+dataR+"_reversed/"
            # print("channel R dir: {}".format(channel_R_dir))
                
                allfiles_and_folders =os.listdir(channel_R_dir)
                allfiles_and_folders.sort()
            # print("channel R dir: {}".format(allfiles_and_folders))
                
                allslices = [f for f in allfiles_and_folders if isfile(join(channel_R_dir, f))  and "png" in f]
                #num_slices = len(allslices)
                files_order_reversed = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/reg/"+data_out+"_reversed/"

                for f in allslices:
                    imgR = imageio.imread(pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/reg/"+dataR+"_reversed/"+f)
                    imgG = imageio.imread(pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/reg/"+dataG+"_reversed/"+f)
                    imgB = imageio.imread(pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/reg/"+dataB+"_reversed/"+f)
                    imgRGB = np.concatenate((imgR[:,:,np.newaxis],imgG[:,:,np.newaxis],imgB[:,:,np.newaxis]),axis=2)
                    print("writing RGB image "+ofolder+f)
                    imageio.imwrite(ofolder+f,imgRGB)
            else:
                 print("folder  "+ofolder+" already exisits. skipping ..")

                
            progress = 100
            self.update_progress("run",int(progress))

    def batch_clean(self):
        pass

try:
    pipe_step=CPipeStepHighResMap({'kn_pipeline_meso_reg2TCstd.py'},shortname="meso-HR")
    print("#I: scriptname is \""+pipe_step.name()+"\"")
    pipe_step.print_settings()
    slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':20,'mem':1000000,'gres':"KN:5"}
    pipe_step.run(slurm_params,{''})


except CPipeError as e:
    print("#E: "+e.value)
