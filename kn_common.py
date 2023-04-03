import subprocess
import math
import sys
import argparse #https://docs.python.org/2/library/argparse.html
import json
import time
import datetime
import os
import re
import nibabel as nib
import numpy as np
from pathlib import Path
#import resource
_HONE_=str(Path.home())

sys.path.append(_HONE_+"/pipeline_passwd/")
from pipedefs import mypipedef
# you need to define your own mypipedef class to provide your folders

class pipedef:
    

    NISSL_ZIPS=mypipedef.NISSL_ZIPS

    PIPELINE_OFOLDER=mypipedef.PIPELINE_OFOLDER

    PIPELINE_KN_RAID_DEL=mypipedef.PIPELINE_KN_RAID_DEL
   
   
    PIPELINE_DATABSE_FOLDER=mypipedef.PIPELINE_DATABSE_FOLDER
    PIPELINE_LOCAL_RAW_FOLDER=mypipedef.PIPELINE_LOCAL_RAW_FOLDER
    PIPELINE_LOCAL_TMP_FOLDER=mypipedef.PIPELINE_LOCAL_TMP_FOLDER
    


    RIKEN_PIPELINE_RAW_FOLDER=mypipedef.RIKEN_PIPELINE_RAW_FOLDER
    RIKEN_PIPELINE_INFO_FOLDER=mypipedef.RIKEN_PIPELINE_INFO_FOLDER
    RIKEN_PIPELINE_DATABASE_INFO_FOLDER=mypipedef.RIKEN_PIPELINE_DATABASE_INFO_FOLDER
    RIKEN_PIPELINE_DATABASE_FOLDER=mypipedef.RIKEN_PIPELINE_DATABASE_FOLDER
     
    RIKEN_PIPELINE_SYNC_FOLDER=mypipedef.RIKEN_PIPELINE_SYNC_FOLDER
    RIKEN_PIPELINE_BACKUP_FOLDER=mypipedef.RIKEN_PIPELINE_BACKUP_FOLDER


    RSYNC_SSH_OPTIONS=mypipedef.RSYNC_SSH_OPTIONS

    matlab_tools=mypipedef.matlab_tools
    matlab_bin=mypipedef.matlab_bin
    

    ants_reg=mypipedef.ants_reg
    ants_apply=mypipedef.ants_apply


class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False

class pipetools:

    @staticmethod
    def nifti_get_bit_and_id(dtype):
        if dtype == np.uint8:
            return 8,2
        if dtype == np.int16:
            return 16,4
        if dtype == np.int32:
            return 32,8
        if dtype == np.float32:
            return 32,16
        if dtype == np.complex64:
            return 64,32
        if dtype == np.float64:
            return 64,64
        if dtype == np.int8:
            return 8,256
        if dtype == np.uint16:
            return 16,512
        if dtype == np.uint32:
            return 32,768
        if dtype == np.complex128:
            return 128,1792
        assert(False)
    
    @staticmethod
    def nifti_convert(fin,fout,dtype=np.uint16,autoscale=False,marmonet_info=None):
        #dtype = np.uint16
        max_v  = np.iinfo(dtype).max
        #fn = '/disk/k_raid/KAKUSHIN-NOU-DATA/database/R01_0026_CM692F/tissuecyte/3d/reg/tracer_weighted_2020_masked_TC_org_2_MRI_std.nii.gz'
        img_p =  nib.load(fin)
        #%%
        #%%
        img = np.array(img_p.get_fdata())
        #%%
        
        header = img_p.header
        #%%
        
        if autoscale:
            #bscale = 2**(np.dtype(dtype).itemsize*8)-1
            #img_scale = bscale * max_v/img.max()
            img_scale = max_v/float(img.max()+0.00000001)
            new_image = nib.Nifti1Image((img*img_scale).astype(dtype), affine=img_p.affine)
            new_image.header['scl_slope'] = 1.0/img_scale
            new_image.header['scl_inter'] = 0.0
            print("fout :{}".format(fout))
            print("img_scale :{}".format(img_scale))
            print("max_v :{}".format(max_v))
        else:
            new_image = nib.Nifti1Image(img.astype(dtype), affine=img_p.affine)
            new_image.header['scl_slope'] = 1.0
            new_image.header['scl_inter'] = 0.0
            
        if marmonet_info is not None:
            xmlpre = b'<?xml version="1.0" encoding="UTF-8"?> <CaretExtension> <Date><![CDATA[2013-07-14T05:45:09]]></Date> '
            body = '<Marmonet MID="'+marmonet_info["MID"]+'" ImageSpace="'+marmonet_info["ImageSpace"]+'">'
            
            body = bytearray(body.encode())

            xmlpost = b'</Marmonet></CaretExtension>'
            
            
            hdr_ext = nib.nifti1.Nifti1Extension(30, xmlpre+body+xmlpost)
            new_image.header.extensions.append(hdr_ext)

        nib.save(new_image, fout)

   

    @staticmethod
    def json2table(jobj):
            #print "!! "+format(jobj)
        s="";
        s+="<table class=\"infotable2\" style=\" font-size:18px;border-width:1px;border-style:solid;border-color:#9e9e9e;border-radius: 2px; \">";
        for o in jobj:
            #print " * "+format(o)+"  "+format(type(o))
            try:
                iterator = iter(o.items())
            except:
                pass
            else:
                #print "** "+format(o)+"  "+format(type(o))
                for attribute, value in o.items():
                    if hasattr(value, '__len__') and len(value)>0:
                        if not isinstance(value, str):
                            s+="<tr><td style=\"text-align: left;\">"+attribute+"</td><td>></td><td>"+pipetools.json2table(value)+"</td></tr>" # example usage
                        else:
                            s+="<tr><td style=\"text-align: left;\">"+attribute+"</td><td>></td><td  style=\"text-align: left;\">"+value+"</td></tr>" # example usage
        s+="</table>";

        return s


    @staticmethod
    def query_yes_no(question, default=False):
        print(question+" [y/n]?")
        yes = set(['yes','y'])
        no = set(['no','n'])

        sys.stdin = open('/dev/tty')
        choice = input().lower()
        if choice in yes:
            return True
        elif choice in no:
            return False
        else:
            print("Please respond with 'yes' or 'no'")
            return default



    @staticmethod
    def json_write(data,filename):
        with open(filename, 'w') as data_file:
            json.dump(data, data_file, indent=4, sort_keys=True, separators=(',', ':'))

    @staticmethod
    def json_read(filename):
        if (os.path.isfile(filename)):
            with open(filename) as data_file:
                data = json.load(data_file)
            isfile=True;
        else:
            data={}
            isfile=False;
        return data, isfile



    @staticmethod
    def check_dependencies(depends,mid):

        if len(depends) > 0:
            for dep in depends:
                json_file=pipedef.PIPELINE_OFOLDER+"/SLURM-"+format(mid)+"-"+dep+".json"
                json_data, isfile=pipetools.json_read(json_file)
                if not isfile:
                    print("#E: missing :"+dep)
                    return False
                if (json_data['state']!='finished'):
                    print("#E: not completed :"+dep)
                    return False

        return True

    @staticmethod
    def get_timestamp():
        now=datetime.datetime.now();
        return '/'.join(str(x) for x in (now.year,now.month,now.day));

    @staticmethod
    def get_folder_timestamp():
        now=datetime.datetime.now();
        return '-'.join(str(x) for x in (now.year,now.month,now.day,now.hour,now.minute,now.second));

    @staticmethod
    def bash_run_and_print(command,fun=None,executable=None):
        if executable is None:
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,shell=True,text=True)
        else:
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,shell=True,text=True,executable=executable)


        print("#I: output of the command "+command)
        while proc.poll() is None:
            output = proc.stdout.readline()
            if fun is not None:
                fun(output.replace('\n', ''));
            else:
                print("#I: "+output.replace('\n', ''))
                sys.stdout.flush();

        proc.wait()
        print("#I: return code of the command "+command+" is "+format(proc.returncode))
        #print(proc.stderr)
        #print(proc.stdout)
        #print("################")
        return (proc.returncode == 0)


    @staticmethod
    def bash_run(command):

        proc = subprocess.Popen(['/bin/bash'],text=True ,stdin=subprocess.PIPE, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        #print format(proc.returncode)
        #result = proc.communicate(command.encode())
        #return result[0].encode(), result[1].encode() , (proc.returncode == 0)
        #return proc.communicate(command.encode()) , (proc.returncode == 0)
        return proc.communicate(command) , (proc.returncode == 0)



    @staticmethod
    def slurm_submit(commands,ofile,**kwargs):
        params={};
        params['quiet']=False;
        params['debug']=False;
        #params['debug']=True;
        params['mem']=5000;
        params['cores']=2;
        params['append']=False;
        params['name']='kakushin pipeline';
        params['time']='01-00:00:00';
        params['queue']='kn_pipe_master';
        params['feature']='';
        params['gres']='';
        params['nodelist']='';
        params['exclude']='';


        if kwargs is not None:
            for key, value in kwargs.items():
            #print "%s == %s" %(key,value)
                params[key]=value;

        #if 'commands' not in params:
        #       print 'ERROR: no commands given'
        #       return


        if not (os.access(os.path.dirname(ofile), os.W_OK)):
            print("#E: cannot write to the folder "+os.path.dirname(ofile))
            print("#E: to store the file "+ofile)
            return "0", False;

        #params['queue']='gpucpu';
        #params['time']='01-00:00:00';

        params['name']=params['name'].replace(' ','-');

        batch='printf "';
        batch=batch+'#!/bin/bash \\n';

        batch=batch+'#SBATCH --job-name=\"'+format(params['name'])+'\"\\n';
        #batch=batch+'#SBATCH --job-name=\"sds\"\\n';
        batch=batch+'#SBATCH -c '+format(params['cores'])+'\\n';
        batch=batch+'#SBATCH --mem '+format(params['mem'])+'\\n';
        batch=batch+'#SBATCH -t '+format(params['time'])+'\\n';
        batch=batch+'#SBATCH --error '+ofile+'\\n';
        batch=batch+'#SBATCH --output '+ofile+'\\n';
        batch=batch+'#SBATCH -p '+format(params['queue'])+'\\n';
        if len(params['feature'])>0:
            batch=batch+'#SBATCH --constraint=\"'+format(params['feature'])+'\"\\n';

        if len(params['nodelist'])>0:
            batch=batch+'#SBATCH --nodelist='+format(params['nodelist'])+'\\n';
        if len(params['exclude'])>0:
            batch=batch+'#SBATCH --exclude='+format(params['exclude'])+'\\n';


        if len(params['gres'])>0:
            batch=batch+'#SBATCH --gres=\"'+format(params['gres'])+'\"\\n';

        #batch=batch+'echo job id is :${SLURM_JOBID}\\n';

        if params['append']:
            batch=batch+'#SBATCH --open-mode append\\n';
        else:
            batch=batch+'#SBATCH --open-mode truncate\\n';

        for command in commands:
            #command = command.replace('"','\"'); #should be added, but for compatibility is not (yet)
            command = command.replace('$','\$');
            #print command
            batch=batch+command+'\\n';

        #batch=batch+"sacct -o reqmem,maxrss,averss,elapsed -j \$SLURM_JOBID\\n";
        #batch=batch+"sacct -o reqmem,maxrss,averss,AllocCPUs,AveCPU,AveCPUFreq,MaxDiskWrite,MaxDiskRead,AveDiskRead,elapsed -j \$SLURM_JOBID\\n";
        #sacct -p -o  JobID,reqmem,maxrss,averss,AllocCPUs,AveCPU,AveCPUFreq,MaxDiskWrite,AveDiskWrite,MaxDiskRead,AveDiskRead,elapsed -j 32997

        batch=batch+'" | sbatch';
        #batch=batch+'" ';

        if      params['debug']:
            batch="";
            for command in commands:
                command.replace('"','\"');
                batch=batch+command+';';
                res, success=pipetools.bash_run(batch);
                res="0";

        else:

            if not params['quiet']:
                print("#I: BATCH SCRIPT: ---------------------------------")
                print(batch)
                print("#I: -----------------------------------------------")
            batch='histchars=;'+batch+';unset histchars;'
            res, success=pipetools.bash_run(batch);

            print(format(res))
            if success:
                #print res
                res=res[0].split()[-1];
                if not params['quiet']:
                    print(res)
                job_state, success=pipetools.bash_run('squeue -h  --job '+res+'  -o "%t"')
                if success:
                    job_state=[f for f in job_state[0].split("\n") if (len(f)>0)];
                    if len(job_state)==1:
                        success = ( job_state[0] in {'R','PD','CF','CG'} )
                    else:
                        print("#E: cannot find the JOB in the queue")
                        success=False

        return res, success;



    @staticmethod
    def print_session_info():
                #print "\n"
        now=datetime.datetime.now();
        job_start='/'.join(str(x) for x in (now.year,now.month,now.day,now.hour))+":"+format(now.minute);
        print("#I: ----------------------------------------")
        SID=os.getenv('SLURM_JOBID','NO SLURM SESSION');
        print("#I: SLURM JOB: "+SID+" ("+job_start+")")
        print("#I: ----------------------------------------")




    #returns triple running? success? progress
    # job_ids=['21213','123213','2']
    @staticmethod
    def wait_for_jobs(job_ids):
        if len(job_ids)==0:
            return False, True, 1

        jobids=",".join([str(f) for f in job_ids])

        job_state, success=pipetools.bash_run('squeue -h  --job '+jobids+'  -o "%t"')

        is_running=False;

        if success:
            job_state=[f for f in job_state[0].split("\n") if (len(f)>0)];
            progress=len(job_ids)-len(job_state);
            for job in job_state:
                running = ( job  in {'R','PD','CF','CG'} )
                if not running:
                    progress += 1;
                if ( job in {'F','CA','TO','NF','SW'} ):
                    return False,False, 0
                is_running=(is_running or running)

        else:
            progress = len(job_ids);

        return is_running, True, (float(progress)/float(len(job_ids)))

    @staticmethod
    def get_jobid_string(jobids):
        job_str="";
        count=1;
        prev_id=-1;
        for f in jobids:
            current_id=int(f);
            if count==1:
                job_str+='{'+format(current_id)+'.'
                prev_id=current_id;

            if (current_id-prev_id)>1:
                job_str+='.'+format(prev_id)+'} '+'{'+format(current_id)+'.'
            if count==len(jobids):
                job_str+='.'+format(current_id)+'}'

            prev_id=current_id;
            count=count+1;
        return job_str
