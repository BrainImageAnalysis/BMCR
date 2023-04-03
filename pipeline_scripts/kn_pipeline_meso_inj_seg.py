#!/usr/bin/env python


import sys
import os
import math
import re
from os.path import isfile, join, isdir


from kn_common import pipetools,pipedef
from kn_pipeline_class import CPipeError,CPipeStep


class CPipeStepInjSeg(CPipeStep):
    foldername="inj"
    signal_name="inj_mask_TC_org.nii.gz"

    def batch_run(self):
        matlab_tools=pipedef.matlab_tools
        matlab_tools2=pipedef.matlab_tools_
        matlab_bin=pipedef.matlab_bin


        if True:
            print("#I: creating dest folders")
            mkdir="mkdir -p "+pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"+self.foldername
            print("#I: "+mkdir)
            res , folder_success  = pipetools.bash_run(mkdir)

            if not (folder_success):
                raise CPipeError("creating folders failed")


            success=True

            MCOMMAND='cd '+matlab_tools+"/; addpath(pwd);"
            MCOMMAND+='cd '+matlab_tools2+"/; addpath(pwd);"
            MCOMMAND+="tracer_seg(\'"+self.mid+"\');"
            MCOMMAND+='exit;'

            COMMAND=matlab_bin+" -r \""+MCOMMAND+"\"";

            print("#I: "+COMMAND)

            success  = pipetools.bash_run_and_print(COMMAND)

            if not success:
                print(res[0])
                print(res[1])
                raise CPipeError("3D stitching of channel tracer signal failed");



        self.create_previews()

    def create_previews(self):
        matlab_tools=pipedef.matlab_tools
        matlab_tools2=matlab_tools+"/inject_side/"
        matlab_bin=pipedef.matlab_bin

        print("#I: creating preview images")
        preview_folder=pipedef.PIPELINE_DATABSE_FOLDER+"/preview/"+format(self.mid)+"/";
        mkdir="mkdir -p "+preview_folder;
        print("#I: "+mkdir)
        res , folder_success  =  pipetools.bash_run(mkdir)
        if not (folder_success):
            raise CPipeError("#E: creating folders failed")

        success=True;
        print("#I: creating preview image ")




        MCOMMAND='cd '+matlab_tools+'/; addpath(pwd);'
        MCOMMAND='cd '+matlab_tools2+'/; addpath(pwd);'
        MCOMMAND+="tracer_seg_preview(\'"+self.mid+"\',\'"+preview_folder+"/"+pipe_step.name()+"\');"
        MCOMMAND+='exit;'

        print("#I: "+MCOMMAND)

        command=matlab_bin+" -r \""+MCOMMAND+"\"";

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



        prev_path="\{PREVIEWFOLDER\}"+"/"+self.mid+"/"+pipe_step.name();


        print("#I: creating html code")

        html="";

        html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';";
        #html+="echo 'bla';";
        html+="echo '<img src=\""+prev_path+"_t_normal.jpg\" style=\"image-rendering: pixelated;\" width=100%>';";
        #html+="echo 'bla';";
        html+="echo '</div><br>';";


        print("#I: adding detailed preview data to table")
        self.sql_add_custome_data("details",html.replace("'","\\\'"),"VARCHAR(20000)");
        print("#I: done")

    def batch_clean(self):
        ofolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"+self.foldername+"/";
        clearme={
          ofolder+"/"+self.signal_name,
          ofolder+"/inj_mask.nii.gz"

        }

        deldir_basedir=pipedef.PIPELINE_KN_RAID_DEL+"/";
        deldir=self.mid+pipetools.get_folder_timestamp();
        self.local_mkdir(deldir_basedir+deldir)

        somethingtodo = False
        for delme in clearme:
            if not os.path.isfile(delme):
                print("#W: skipping "+delme+", does not exist")
            else:
                somethingtodo = True
                self.local_mv(delme,deldir_basedir+deldir)

        if somethingtodo:
            SLURM_command={"cd "+deldir_basedir+" && rm "+deldir+" -r"};

            res, success=pipetools.slurm_submit(SLURM_command,self.ofile,name=self.mid+"-CLEAN-"+self.shortname,queue="kn_pipe_cleanup")
            if not success:
                raise CPipeError("submitting cleaning script failed "+format(res[0]));

try:
    pipe_step=CPipeStepInjSeg({'kn_pipeline_meso_get_t2n.py'},shortname="meso-injseg");
    print("#I: scriptname is \""+pipe_step.name()+"\"")
    pipe_step.print_settings()
    #slurm_params={'queue':"kn_pipe_IO",'time':"10-00:00:00",'cores':8,'mem':10000,'gres':"KN:10",'feature':'2.4GH'};
    slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':8,'mem':10000,'feature':''};
    pipe_step.run(slurm_params,{'kn_pipeline_meso_NN_cells.py'})


except CPipeError as e:
    print("#E: "+e.value)
