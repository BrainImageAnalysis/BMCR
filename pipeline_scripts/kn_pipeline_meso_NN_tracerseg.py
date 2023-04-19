#!/usr/bin/env python

import sys
import os
import re
import math
from os.path import isfile, join, isdir
import time

from kn_common import pipetools,pipedef
from kn_pipeline_class import CPipeError,CPipeStep


class CPipeStepAxonFilt(CPipeStep):
    



    jobids=[];

    def wait_for_jobs(self,progress_scale=(0,1)):
        progress_old=-1;
        is_running=True;
        while (is_running):
          is_running, success, progress =  pipetools.wait_for_jobs(self.jobids);
          if not success:
            jobids=",".join([str(f) for f in self.jobids])
            print("#W: warning, killing jobs")
            job_state, success=pipetools.bash_run('scancel '+jobids)
            if not success:
              print("#W: "+job_state[1])
          else:
            if progress!=progress_old:
              progress_old=progress;
              self.update_progress("run",int(100*(progress_scale[0]+progress_scale[1]*progress)));
          if is_running:    
            time.sleep( 10 )
          
        if not success:
            raise CPipeError("tracking jobs failed");  
  
    subfolder="NN_tracer";
    #skip_last_n_slides=20    
    def batch_run(self):
        # KAWASE CORRECTED
        #tracer_channel = 'c5'
        #bg_channel = 'c4'
        # BF ESTIMATATION BASED CORRECTION
        tracer_channel = 'c2'
        bg_channel = 'c1'

        
        #subfolder="axionfilter2";
      
        print("#I: creating dest folder")
    
        folder_name=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/"+self.subfolder;
        mkdir="mkdir -p "+folder_name;
        print("#I: "+mkdir)
        res , folder_success  = pipetools.bash_run(mkdir)
        if not (folder_success):
                raise CPipeError("creating folder failed")
                  
                  
        
        ifolder=pipedef.PIPELINE_DATABSE_FOLDER+self.mid+"/tissuecyte/slice/";


        #allfiles_and_folders=os.listdir(ifolder+"/c1/");
        #allfiles=[f for f in allfiles_and_folders if (os.path.isfile(os.path.join(ifolder+"/c1/", f)) and ("toplayer_1" in f))];
        
        allfiles_and_folders=os.listdir(ifolder+"/"+bg_channel+"/");
        allfiles_and_folders.sort()
        all_bg_files=[f for f in allfiles_and_folders if (os.path.isfile(os.path.join(ifolder+"/"+bg_channel+"/", f)) and ("toplayer_1" in f))];
        
        allfiles_and_folders=os.listdir(ifolder+"/"+tracer_channel+"/");
        allfiles_and_folders.sort()
        all_fg_files=[f for f in allfiles_and_folders if (os.path.isfile(os.path.join(ifolder+"/"+tracer_channel+"/", f)) and ("toplayer_1" in f))];
        
        if len(all_fg_files) != len(all_bg_files):
            raise CPipeError("number of fg files ({}) differs from number of bg files ({})".format(len(all_fg_files),len(all_bg_files)));
        
        #all_bg_files = (all_bg_files[0:len(all_bg_files)-self.skip_last_n_slides])
        #all_fg_files = (all_fg_files[0:len(all_fg_files)-self.skip_last_n_slides])

        test=0;
        append_file=False;
        self.jobids=[];
        
        collect = len(all_fg_files)
        sliceid = 0
        
        fg_list = ""
        bg_list = ""
        out_list = ""
        slice_list =""
        for file_indx in range(0,len(all_fg_files)):
            
            bg_f = os.path.join(ifolder+"/"+bg_channel+"/",all_bg_files[file_indx].split("_")[0]+".png")
            fg_f = os.path.join(ifolder+"/"+tracer_channel+"/",all_fg_files[file_indx].split("_")[0]+".png")
            
            
            ofolder=pipedef.PIPELINE_DATABSE_FOLDER+'/'+self.mid+'/'+'/tissuecyte/slice/'+self.subfolder+'/';
            ofile=ofolder+"/slice"+str(10000+sliceid)+".png";
            
            
            #if True:
            if not os.path.isfile(ofile):
                fg_list += " "+fg_f+" "
                bg_list += " "+bg_f+" "
                out_list += " "+ofile+" "
                slice_list += "_"+all_bg_files[file_indx].split("_")[0]+"_"
            
            collect -= 1
            if (collect%10 == 0):# and (test==0):
                if len(out_list) > 0:
                    COMMAND =  [
                            "source /disk/soft/MODULES/init.sh",
                            "source /etc/profile.d/modules.sh",
                            "module load dev/cuda10", 
                            "echo ${WORKON_HOME}",
                            "workon pipeline3",
                            "which python",
                            "cd "+pipedef.matlab_tools+"/NN_tracer/",
                            "python detect_tracer.py --pipe --model ./model_2019_04_16_state_01/tracer_net --fg "+fg_list+" --bg "+bg_list+" --out "+out_list+" --chkpt  175000  --min_size 4 "   
                            ]               
                    COMMAND =  [
                            "cd "+pipedef.matlab_tools+"/NN_tracer/",
                            "python detect_tracer.py --pipe --model ./model_2019_04_16_state_01/tracer_net --fg "+fg_list+" --bg "+bg_list+" --out "+out_list+" --chkpt  175000  --min_size 4 "   
                            ]               
                    
                    res, success=pipetools.slurm_submit(COMMAND,ofile.replace(".png","_GPU_"+slice_list+".txt"),name=self.mid+"-"+format(self.SLURM_JOBID)+"-GPU-"+self.shortname,\
                                queue="kn_pipe_slave_GPU",cores=2,mem=26000,gres="gpu:1",append=append_file)                
                    #res, success=pipetools.slurm_submit(COMMAND,ofile.replace(".png","_CPU_"+slice_list+".txt"),name=self.mid+"-"+format(self.SLURM_JOBID)+"-CPU-"+self.shortname,\
                    #            queue="kn_pipe_slave",cores=4,mem=26000,append=append_file)                
                    
                    fg_list = ""
                    bg_list = ""
                    out_list = ""      
                    slice_list =""

                   # print(COMMAND)
                    
                    test+=1
                    if not success:
                      print(format(res))
                      print(format(self.jobids))
                      raise CPipeError("submitting GPU script failed ");
                   # else:
                   #    print(res)
                       
                    self.jobids.append(int(res));
            
            
            
            sliceid += 1
            
      
        self.sql_add_custome_data("JOBCHILDS",format(self.jobids));
        print(format(self.jobids).replace(',',' '))
        sys.stdout.flush();
        self.wait_for_jobs([0,1])

              
        #self.local_chgrp(pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/"+self.subfolder+" -R")
        #self.local_chmod(" +Xr ",pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/"+self.subfolder+" -R")

          
    def batch_clean(self):
        
        ofolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/"+self.subfolder;
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
    pipe_step=CPipeStepAxonFilt({'kn_pipeline_meso_get_t2n.py'},shortname="meso-tracerNN");
    print("#I: scriptname is \""+pipe_step.name()+"\"")
    pipe_step.print_settings()
    #slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':8,'mem':30000,'gres':"gpu:1",'feature':'pk'};
    #slurm_params={'queue':"kn_pipe_master",'time':"unlimited"};
    slurm_params={'queue':"kn_pipe_master",'time':"unlimited",'cores':1,'mem':2000,'gres':""};
    pipe_step.run(slurm_params,{'kn_pipeline_meso_NN_tracerseg_3D.py'})
    
    
except CPipeError as e:
    print("#E: "+e.value)



