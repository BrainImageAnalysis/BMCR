#!/usr/bin/env python

import sys
import os
import math
import re
from os.path import isfile, join, isdir
import pickle
import time
import numpy as np
import scipy
import scipy.ndimage
import scipy.misc
from kn_common import pipetools,pipedef
from kn_pipeline_class import CPipeError,CPipeStep
from PIL import Image, ImageFile
import nibabel as nib
import imageio
from os import listdir
from os.path import isfile, join, isdir
import sys
import scipy
from scipy.spatial import distance_matrix


class CPipeNissl2D(CPipeStep):

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

    def progress_update(self,txt):
        if re.match(r'#PROGRESS#\d*#', txt):
            progress=int(re.search(r'\d+', txt).group())
            self.update_progress("run",progress)
        else:
            print("#I: "+txt)
            sys.stdout.flush()

    def pre_check(self):
        zipfile = pipedef.NISSL_ZIPS+"/"+str(self.mid)+".zip"
        if os.path.isfile(zipfile):
            return True
        print("#W: ##############################################")
        print("#W: the NISSLE zip file "+zipfile)
        print("#W: does not exist, cannot be submited to pipeline")

    def verify(self,check_folder):
        print("#I verifying "+check_folder)
        nissl_raw =  pipedef.PIPELINE_LOCAL_RAW_FOLDER+format(self.mid)+"/Nissl/Nissl/"
        allfiles_and_folders =os.listdir(nissl_raw)
        allfiles = [
                    f for f in allfiles_and_folders if isfile(join(nissl_raw, f))]
        slices = [int(f[0:len(f) - 4]) for f in allfiles if (f[len(f) - 3:len(f)] == 'tif')]
        slices.sort()
        min_sliceid = np.min(slices)
        max_sliceid = np.max(slices)
        #slice10444.png
        invalid = [not isfile(join(check_folder,"slice"+str(f+10000-1)+".png")) for f in range(min_sliceid,max_sliceid)]

        print((format(invalid)))
        #print format(np.any(not valid))
        if np.any(invalid):
            for f in range(min_sliceid,max_sliceid):
                if not isfile(join(check_folder,"slice"+str(f+10000-1)+".png")):
                    print((join(check_folder,"slice"+str(f+10000-1)+".png")+ " is missing"))
            return False
        return True


    def batch_run(self):
        matlab_tools=pipedef.matlab_tools+'/NISSL/'
        matlab_bin=pipedef.matlab_bin

        ifolder = pipedef.PIPELINE_LOCAL_RAW_FOLDER+"/"+format(self.mid)+"/Nissl"
        ofolder = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/"
        ofolder3D = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"
        tmpfolder = pipedef.PIPELINE_LOCAL_TMP_FOLDER+"/"+format(self.mid)+"/Nissl/"
        tmpfolder_debug_imgs = pipedef.PIPELINE_LOCAL_TMP_FOLDER+"/"+format(self.mid)+"/Nissl/imgs/"

        #parallel_jobs = 4



        folders = [ ifolder,
                    ofolder+"/Nissl/first_match/",
                    ofolder+"/Backlit/first_match/",
                    ofolder3D+"/Nissl/",
                    tmpfolder,
                    tmpfolder_debug_imgs]

        print("#I: creating dest folder")

        for f in folders:
            mkdir="mkdir -p "+f
            print("#I: "+mkdir)
            res , folder_success  = pipetools.bash_run(mkdir)

            if not (folder_success):
                raise CPipeError("creating folders failed")
       # if True:
        if not os.path.isdir(ifolder+"/Nissl"):
            unzip = "unzip "+pipedef.NISSL_ZIPS+"/"+str(self.mid)+".zip -d "+ifolder
            print("#I: "+unzip)
            success  = pipetools.bash_run_and_print(unzip)
            if not (success):
                raise CPipeError("error unzipping files")


        bl_dir = ifolder+'/Backlit/'
        n_dir = ifolder+'/Nissl/'
        tc_dir = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/c1_50mu/"
        tc_ref = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/c1/img3D_raw_TC_org.nii.gz"

        tmp = tmpfolder

        if True:
            perform = {
                    'BestMatch':True,
                   '3DNisslNN':True,
                    '3DBacklitNN':True,
                    'fillup':True,
                    'verify':True,
                    'preview':True,
                    }
            perform = {
                    'BestMatchTorch':True,
                    'BestMatch':False,
                   '3DNisslNN':True,
                    '3DBacklitNN':True,
                    'fillup':True,
                    'verify':True,
                    'preview':True,
                    }
            perform = {
                    'BestMatchTorch':True,
                    'BestMatch':False,
                   '3DNisslNN':True,
                    '3DBacklitNN':True,
                    'fillup':True,
                    'verify':True,
                    'preview':True,
                    }


            perform_ = {
                    'BestMatchTorch':False,
                    'BestMatch':False,
                   '3DNisslNN':True,
                    '3DBacklitNN':True,
                    'fillup':False,
                    'verify':False,
                    'preview':True,
                    }

        self.jobids=[]
        test = 0
        if perform['BestMatchTorch']:
            success=True
            out_N_dir = ofolder+"/Nissl/first_match/"
            out_BL_dir = ofolder+"/Backlit/first_match/"
            MID = self.mid            
            RAWF = "/disk/k_raid/KAKUSHIN-NOU-DATA/database_raw/"
            RAWTC = "/disk/k_raid/KAKUSHIN-NOU-DATA/database/"
            TMP = "/disk/k_raid/KAKUSHIN-NOU-DATA/database_tmp/"
            TMPd = join(TMP,MID,"Nissl2")
            if not isdir(TMPd):
                os.makedirs(TMPd)

            fd = join(RAWF,MID,"Nissl/Nissl")
            raw_files_nissl = [int(f.replace(".tif","")) for f in listdir(fd) if (isfile(join(fd,f)) and ("tif" in f))] 
            raw_files_nissl.sort()
            raw_files_nissl_n = np.array(raw_files_nissl)
            fd = join(RAWTC,MID,"tissuecyte/slice/c1_50mu")
            raw_files_tc = [int(f.replace("slice","").replace(".png",""))-10000+1 for f in listdir(fd) if (isfile(join(fd,f)) and ("png" in f))] 
            raw_files_tc.sort()
            raw_files_tc_n = np.array(raw_files_tc)

            raw_files_tc_n = raw_files_tc_n[raw_files_tc_n>=raw_files_nissl_n[0]]
            raw_files_tc_n = raw_files_tc_n[raw_files_tc_n<=raw_files_nissl_n[-1]]

            D = scipy.spatial.distance_matrix(raw_files_nissl_n[:,np.newaxis],raw_files_tc_n[:,np.newaxis])

            nissl_indx = np.argsort(D, axis=0)[0,:]
            tc_2_nissl_index = raw_files_nissl_n[nissl_indx]

            for ids_ in range(len(raw_files_tc_n)):
            #for ids_ in range(0,len(raw_files_tc_n),33):
                
                print("submitting {} -> {}".format(ids_,raw_files_tc_n[ids_] - 1))
            #for ids_ in range(0,len(raw_files_tc_n),35):
                CMD = "python "+matlab_tools+"/NISSL/reg2D.py --mid "+MID+" --sid "+str(ids_)+" "

                #res, success=pipetools.slurm_submit({CMD},TMPd+"/BestMatch_"+str(test)+".txt",name=self.mid+"-"+format(self.SLURM_JOBID)+"-BestMatch-"+self.shortname,\
                #            queue="kn_pipe_slave",cores=16,mem=32000,append=False)

                res, success=pipetools.slurm_submit({CMD},TMPd+"/BestMatch_"+str(ids_)+".txt",name=self.mid+"-"+format(self.SLURM_JOBID)+"-BestMatch-"+self.shortname,\
                            queue="kn_pipe_slave",cores=16,mem=32000,append=False)

                test+=1
                if not success:
                    print(format(res))
                    print(format(self.jobids))
                    raise CPipeError("submitting script failed ")
                self.jobids.append(int(res))
                #break

            self.sql_add_custome_data("JOBCHILDS",format(self.jobids))
            print(format(self.jobids).replace(',',' '))
            sys.stdout.flush()
            self.wait_for_jobs([0,0.30])


        if perform['BestMatch']:
            # BEST MATCH
            success=True
            out_N_dir = ofolder+"/Nissl/first_match/"
            out_BL_dir = ofolder+"/Backlit/first_match/"


            MCOMMAND="nissl_pipeline_register(\
                    \'mid\',\'"+self.mid+"\', \
                    \'bl_dir\',\'"+bl_dir+"\', \
                    \'n_dir\',\'"+n_dir+"\', \
                    \'tmp\',\'"+tmp+"\', \
                    \'out_N_dir\',\'"+out_N_dir+"\', \
                    \'out_BL_dir\',\'"+out_BL_dir+"\', \
                    \'tc_dir\',\'"+tc_dir+"\', \
                    \'mode\',\'first\' \
                    );"
            MCOMMAND = MCOMMAND.replace(" ","")
            MCOMMAND= 'cd '+matlab_tools+'/; addpath(pwd);' + MCOMMAND + 'exit;'
            COMMAND=matlab_bin+" -r \""+MCOMMAND+"\""
            print(COMMAND)
            mat_commands, success  = pipetools.bash_run(COMMAND)

            #with open('/home/kakushin/debug_nissl.pkl', 'wb') as f:
            #    pickle.dump([mat_commands,success], f)

            self.jobids=[];
            test = 0
            for r in mat_commands[0].split("\n"):
                if "#SUBMITCMD" in r:# and (test < 1):
                    #print(r[10:])
                    MCOMMAND = r[10:] #.replace("'","\\'")
                    MCOMMAND = MCOMMAND.replace(" ","")
                    #MCOMMAND= 'cd '+matlab_tools+'/; addpath(pwd);' + MCOMMAND + 'exit;'
                    #COMMAND=matlab_bin+" -r \""+MCOMMAND+"\""
                    MCOMMAND= 'cd '+matlab_tools+'/; addpath(pwd);'+MCOMMAND+';exit;'

                    #MCOMMAND= 'cd '+matlab_tools+'/; addpath(pwd);'+"ls"+';exit;'
                    COMMAND=matlab_bin+" -r \\\""+MCOMMAND+"\\\""
                    print(COMMAND)
                    print("")

                    res, success=pipetools.slurm_submit({COMMAND},tmpfolder+"/BestMatch_"+str(test)+".txt",name=self.mid+"-"+format(self.SLURM_JOBID)+"-BestMatch-"+self.shortname,\
                                queue="kn_pipe_slave",cores=16,mem=32000,append=False)

                    test+=1
                    if not success:
                        print(format(res))
                        print(format(self.jobids))
                        raise CPipeError("submitting script failed ");
                    self.jobids.append(int(res));

            self.sql_add_custome_data("JOBCHILDS",format(self.jobids));
            print(format(self.jobids).replace(',',' '))
            sys.stdout.flush();
            self.wait_for_jobs([0,0.30])



            #success  = pipetools.bash_run_and_print(COMMAND)

            if not success:
                raise CPipeError("registering the Nissl images failed")

        if True:
            if not self.verify(ofolder+"/Nissl/first_match/") or not self.verify(ofolder+"/Backlit/first_match/"):
                raise CPipeError("verifying the  registration of the Nissl images failed (first match)")


        self.update_progress("run",75)




        if perform['3DNisslNN']:
            # Nissl 3D
            success=True
            #tc_ref
            in_dir_first = ofolder+"/Nissl/first_match/"
            in_dir_second = ofolder+"/Nissl/second_match/"
            combined_out_dir = ofolder+"/Nissl/interpolated/"
            out_N_dir = ofolder+"/Nissl/first_match/"
            out_BL_dir = ofolder+"/Backlit/first_match/"

            #output_file_3D = ofolder+"/Nissl/second_match/"
            input_dir_3D = ofolder+"/Nissl/first_match/"
            output_file_3D = ofolder3D+"/Nissl/Nissl_NN_org.nii.gz"

            MCOMMAND="nissl_pipeline_register(\
                    \'mid\',\'"+self.mid+"\', \
                    \'output_file_3D\',\'"+output_file_3D+"\', \
                    \'input_dir_3D\',\'"+input_dir_3D+"\', \
                    \'ref_file_3D\',\'"+tc_ref+"\', \
                    \'is_rgb\',true, \
                    \'bl_dir\',\'"+bl_dir+"\', \
                    \'n_dir\',\'"+n_dir+"\', \
                    \'tmp\',\'"+tmp+"\', \
                    \'out_N_dir\',\'"+out_N_dir+"\', \
                    \'out_BL_dir\',\'"+out_BL_dir+"\', \
                    \'tc_dir\',\'"+tc_dir+"\', \
                    \'in_dir_first\',\'"+in_dir_first+"\', \
                    \'in_dir_second\',\'"+in_dir_second+"\', \
                    \'combined_out_dir\',\'"+combined_out_dir+"\', \
                    \'mode\',\'3D\' \
                    );"
            MCOMMAND = MCOMMAND.replace(" ","")
            MCOMMAND= 'cd '+matlab_tools+'/; addpath(pwd);' + MCOMMAND + 'exit;'
            COMMAND=matlab_bin+" -r \""+MCOMMAND+"\""
            #print COMMAND
            success  = pipetools.bash_run_and_print(COMMAND)

            if not success:
                raise CPipeError("creating 3D NN Nissl images failed")




        self.update_progress("run",97)

        if perform['3DBacklitNN']:
            # Backlit 3D
            success=True
            #tc_ref
            in_dir_first = ofolder+"/Backlit/first_match/"
            in_dir_second = ofolder+"/Backlit/second_match/"
            combined_out_dir = ofolder+"/Backlit/interpolated/"
            out_N_dir = ofolder+"/Nissl/first_match/"
            out_BL_dir = ofolder+"/Backlit/first_match/"

            #output_file_3D = ofolder+"/Backlit/second_match/"
            input_dir_3D = ofolder+"/Backlit/first_match/"
            output_file_3D = ofolder3D+"/Nissl/Backlit_NN_org.nii.gz"

            MCOMMAND="nissl_pipeline_register(\
                    \'mid\',\'"+self.mid+"\', \
                    \'output_file_3D\',\'"+output_file_3D+"\', \
                    \'input_dir_3D\',\'"+input_dir_3D+"\', \
                    \'ref_file_3D\',\'"+tc_ref+"\', \
                    \'is_rgb\',false, \
                    \'bl_dir\',\'"+bl_dir+"\', \
                    \'n_dir\',\'"+n_dir+"\', \
                    \'tmp\',\'"+tmp+"\', \
                    \'out_N_dir\',\'"+out_N_dir+"\', \
                    \'out_BL_dir\',\'"+out_BL_dir+"\', \
                    \'tc_dir\',\'"+tc_dir+"\', \
                    \'in_dir_first\',\'"+in_dir_first+"\', \
                    \'in_dir_second\',\'"+in_dir_second+"\', \
                    \'combined_out_dir\',\'"+combined_out_dir+"\', \
                    \'mode\',\'3D\' \
                    );"
            MCOMMAND = MCOMMAND.replace(" ","")
            MCOMMAND= 'cd '+matlab_tools+'/; addpath(pwd);' + MCOMMAND + 'exit;'
            COMMAND=matlab_bin+" -r \""+MCOMMAND+"\""
            #print COMMAND
            success  = pipetools.bash_run_and_print(COMMAND)

            if not success:
                raise CPipeError("creating 3D NN Backlit images failed")

        if perform['fillup']:
            success=True

            folder = ofolder+"/c1_50mu/"
            refs =os.listdir(folder)
            refs.sort()
            refs = [
                f for f in refs if isfile(join(folder, f))]
            refs = [f for f in refs if (f[len(f) - 3:len(f)] == 'png')]


            folder = ifolder+"/Nissl/"
            nissl =os.listdir(folder)
            nissl.sort()
            nissl = [
                f for f in nissl if isfile(join(folder, f))]
            nissl = [int(f[:len(f)-4]) for f in nissl if (f[len(f) - 3:len(f)] == 'tif')]
            nissl = np.sort(nissl)

            nissl_key = ['slice'+str(10000+f)+".png" for f in nissl]
            nissl = ['slice'+str(10000+f)+".png" for f in range(nissl[0]-1,nissl[len(nissl)-1])]

            img = np.array(imageio.imread(ofolder+"/Nissl/first_match/"+nissl[0]))
            
            #img = np.array(scipy.ndimage.imread(ofolder+"/Nissl/first_match/"+nissl[0]))
            img[:] = 255
            print("{}".format(img.shape))

            if True:
                slice_folders = [
                        ofolder+"/Nissl/first_match/",
                        ofolder+"/Backlit/first_match/",
                ]
                for folder in slice_folders:
                    meta = {}
                    #print "#############################################"
                    for r in refs:
                        if r not in nissl:
                            print("#I adding {}".format(r))
                            ofile = folder+"/"+r
                            if not isfile(ofile):
                                imageio.imwrite(ofile, img.astype(np.uint8))
                                #scipy.misc.imsave(ofile, img.astype(np.uint8))
                        else:
                            print("#I exists  {}".format(r))
                        if r not in nissl_key:
                            meta[r] = 'added'
                        else:
                            meta[r] = 'keyframe'

                    pipetools.json_write(meta,folder+"/sliceinfo.json")

                #print "{}".format(img.shape)
            print("{}".format(img.shape))
            if not success:
                raise CPipeError("filling up images failed")

        self.update_progress("run",99)



        #self.local_chgrp(ofolder+"/Nissl/"+" -R")
        #self.local_chgrp(ofolder+"/Backlit/"+" -R")
        self.local_chmod(" +Xr ",ofolder+"/Nissl/"+" -R")
        self.local_chmod(" +Xr ",ofolder+"/Backlit/"+" -R")

        if perform['verify']:
            #%%
            check_folder = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/Nissl/first_match/"
            #check_folder = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/Nissl/interpolated/"
            ref_folder = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/c1_50mu/"

            allfiles_and_folders =os.listdir(ref_folder)
            allfiles_and_folders.sort()

            allfiles = [
                        f for f in allfiles_and_folders if isfile(join(ref_folder, f))]

            slices = [f for f in allfiles if (f[len(f) - 3:len(f)] == 'png') ]
            #%%
            invalid = [not isfile(join(check_folder,f)) for f in slices]
            print(format(invalid))
            #print format(np.any(not valid))
            if np.any(invalid):
                for i in range(0,len(invalid)):
                    if invalid[i]:
                        print(slices[i]+ " is missing")
                raise CPipeError("computing Nissl DATA")


        if perform['preview']:
            self.create_previews()

    def create_previews(self):

        print("#I: creating preview images")
        preview_folder=pipedef.PIPELINE_DATABSE_FOLDER+"/preview/"+format(self.mid)+"/";
        mkdir="mkdir -p "+preview_folder;
        print("#I: "+mkdir)
        res , folder_success  =  pipetools.bash_run(mkdir)
        if not (folder_success):
            raise CPipeError("#E: creating folders failed")

        success=True;
        print("#I: creating preview image ")

        nissl_file = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/Nissl/Nissl_NN_org.nii.gz"
        img_nissl = nib.load(nissl_file)
        img_nissl = img_nissl.get_data()
        #%%
        img_nissl_RGB = np.concatenate((img_nissl['R'][:,:,:,np.newaxis],img_nissl['R'][:,:,:,np.newaxis],img_nissl['B'][:,:,:,np.newaxis]),axis=3)
        #%%
        img_X = img_nissl_RGB[math.ceil(img_nissl_RGB.shape[0]/2),:,:,:]
        img_Y = img_nissl_RGB[:,math.ceil(img_nissl_RGB.shape[1]/3),:,:]
        img_Z = img_nissl_RGB[:,:,math.ceil(img_nissl_RGB.shape[2]/2),:]


        im_d = Image.fromarray(img_X, mode='RGB')
        im_d.save(preview_folder+"/"+pipe_step.name()+"_nissl_x.jpg", "JPEG", quality=90)
        im_d = Image.fromarray(img_Y, mode='RGB')
        im_d.save(preview_folder+"/"+pipe_step.name()+"_nissl_y.jpg", "JPEG", quality=90)
        im_d = Image.fromarray(img_Z, mode='RGB')
        im_d.save(preview_folder+"/"+pipe_step.name()+"_nissl_z.jpg", "JPEG", quality=90)

        #img_X_small = scipy.misc.imresize(img_X,0.2)
        #img_X_tiny = scipy.misc.imresize(img_X,0.1)

        #img_X_small = scipy.misc.imresize(img_X,0.2)
        #img_X_tiny = scipy.misc.imresize(img_X,0.1)
        im_shape = img_X.shape

        img_X_small = np.array(Image.fromarray(img_X).resize((math.ceil(0.2*im_shape[0]),math.ceil(0.2*im_shape[1]))))
        img_X_tiny = np.array(Image.fromarray(img_X).resize((math.ceil(0.1*im_shape[0]),math.ceil(0.1*im_shape[1]))))


        im_d = Image.fromarray(img_X_tiny, mode='RGB')
        im_d.save(preview_folder+"/"+pipe_step.name()+"_tiny.jpg", "JPEG", quality=90)
        im_d = Image.fromarray(img_X_small, mode='RGB')
        im_d.save(preview_folder+"/"+pipe_step.name()+"_small.jpg", "JPEG", quality=90)

        #self.local_chgrp(preview_folder+" -R")

        print("#I: adding preview data to table")
        if True:
            self.sql_add_custome_data("icon",pipe_step.name()+"tiny.jpg")
            self.sql_add_custome_data("preview",pipe_step.name()+"small.jpg")


        #supported variables:  \{PREVIEWFOLDER\}, \{DATABASEFOLDER\}" and \{MID\}"


        prev_path="\{PREVIEWFOLDER\}"+"/"+self.mid+"/"+pipe_step.name();


        print("#I: creating html code")

        html="";

        html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';"
        html+="echo '<img src=\""+prev_path+"_nissl_x.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
        html+="echo '<img src=\""+prev_path+"_nissl_y.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
        html+="echo '<img src=\""+prev_path+"_nissl_z.jpg\" style=\"image-rendering: pixelated;\" width=100%>';"
        html+="echo '</div><br>';"


        print("#I: adding detailed preview data to table")
        self.sql_add_custome_data("details",html.replace("'","\\\'"),"VARCHAR(20000)");
        print("#I: done")

    def batch_clean(self):
        root_folder = pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/"
        root_folder2 = pipedef.PIPELINE_LOCAL_RAW_FOLDER+"/"+format(self.mid)+"/"

        clearme={
        pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/Nissl",
        pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/Backlit",
        pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/Nissl",
        pipedef.PIPELINE_LOCAL_RAW_FOLDER+"/"+format(self.mid)+"/Nissl",
        }

        #deldir_basedir=pipedef.PIPELINE_KN_RAID_DEL+"/";
        #deldir=self.mid+pipetools.get_folder_timestamp();
        #self.local_mkdir(deldir_basedir+deldir)

        for delme in clearme:
            if not os.path.isdir(delme):
                print("#W: skipping "+delme+", does not exist")
            else:
                if (root_folder in delme) or (root_folder2 in delme):
                    print("#W: deleting "+delme)
                    COMMAND = "rm -rv "+delme
                    success  = pipetools.bash_run_and_print(COMMAND)

                    if not success:
                        raise CPipeError("error cleaning Nissl data")
                else:
                    print("#W: skipping "+delme+", foldername is invalid")

try:
    pipe_step=CPipeNissl2D({'kn_pipeline_meso_get_t2n.py'},shortname="meso-Nissl-2D")    
    #pipe_step=CPipeNissl2D({'kn_pipeline_meso_get_t2n.py','kn_pipeline_meso_stitch_preview.py'},shortname="meso-Nissl-2D")
    print("#I: scriptname is \""+pipe_step.name()+"\"")
    pipe_step.print_settings()
    #slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':10,'mem':32000,'gres':"KN:5",'feature':'2.4GH'}
    #slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':16,'mem':128000,'gres':"KN:5",'feature':'2.4GH'}
    #slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':2,'mem':16000,'gres':"KN:5",'feature':'2.4GH'}

    slurm_params={'queue':"kn_pipe_slave",'time':"10-00:00:00",'cores':2,'mem':16000,'gres':"KN:1"}
    #slurm_params={'queue':"gpucpu",'time':"1-00:00:00",'cores':2,'mem':16000}
    #if pipe_step.pre_check():
    #    pipe_step.run(slurm_params,{})
    
    pipe_step.run(slurm_params,{})


except CPipeError as e:
    print("#E: "+e.value)
