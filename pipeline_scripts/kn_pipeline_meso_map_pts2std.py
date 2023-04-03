#!/usr/bin/env python

import sys
import os
import math
import re
import subprocess
#import pandas as pd
from os.path import isfile, join, isdir
from os import listdir
from kn_common import pipetools, pipedef
from kn_pipeline_class import CPipeError, CPipeStep
import json
import nibabel as nib
import numpy as np
import csv
import pandas as pd
import scipy
from scipy.io import loadmat

def json_write(data,filename):
    with open(filename, 'w') as data_file:
        json.dump(data, data_file, indent=4, sort_keys=True, separators=(',', ':'))

def json_read(filename):
    if (os.path.isfile(filename)):
        with open(filename) as data_file:
            data = json.load(data_file)
        isfile=True;
    else:
        data={}
        isfile=False;
    return data, isfile

#def bash_run(command):#
#
#        proc = subprocess.Popen(['/bin/bash'],text=True ,stdin=subprocess.PIPE, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
#        return proc.communicate(command) , (proc.returncode == 0)


class CPipePts(CPipeStep):

         

    def progress_update(self, txt):
        if re.match(r'#PROGRESS#\d*#', txt):
            progress = int(re.search(r'\d+', txt).group())
            self.update_progress("run", progress)
        else:
            print("#I: " + txt)
            sys.stdout.flush()

    jobs = [
            ['CELLS','NN_tracer_reversed','labels','NN_tracer_reversed'],
            ['Retrograde01','Retrograde01_reversed','','NN_tracer_reversed'],
            
            ]
    def batch_run(self):
        for job in self.jobs:

            src_dir = job[0]
            dest_dir = job[1]
            sub_dir = job[2]
            std_ref_files = job[3]
            
            db_folder = pipedef.PIPELINE_DATABSE_FOLDER
            MID = self.mid

            if isdir(join(db_folder,MID,'tissuecyte/slice/'+sub_dir+'/'+src_dir+'/')):
                pt_files = [f for f in listdir(join(db_folder,MID,'tissuecyte/slice/'+sub_dir+'/'+src_dir+'/')) if (isfile(join(db_folder,MID,'tissuecyte/slice/'+sub_dir+'/'+src_dir+'/',f)) and ("csv" in f) and ("slice" in f))] 
                pt_files.sort()
                if (len(pt_files)<1):
                    raise CPipeError("not cell labels in org space")

                xres = 1.385689385
                yres = 1.339262803
                tc_file = join(db_folder,MID,'meta/TC_info.json')
                if isfile(tc_file):
                    jdata,ok = (json_read(tc_file))
                    if 'xres:' in jdata['Mosaic']:
                        xres = jdata['Mosaic']['xres:']
                        yres = jdata['Mosaic']['yres:']
                    
                    if 'Xres:' in jdata['Mosaic']:
                        xres = jdata['Mosaic']['Xres:']
                        yres = jdata['Mosaic']['Yres:']



                stitch_info = scipy.io.loadmat(db_folder+MID+'/tissuecyte/slice/c1/slice10000_info_toplayer_1_res_50_.mat');
                rot = stitch_info['img_info']['trafo'][0][0][0][0]    
                if rot == 90:
                    yres_ = yres
                    yres = xres
                    xres = yres_                

                print("#I: "+str([xres,yres]))


                positions_3D = np.zeros([0,3],dtype=np.float32) 
                z_index = 0
                for pt_file in  pt_files:
                    pt_file_ = join(db_folder,MID,'tissuecyte/slice/'+sub_dir+'/'+src_dir+'/',pt_file)    
                    ok = False
                    #print("#I: "+pt_file_)
                    try:
                        file = pd.read_csv(pt_file_, header=None) 
                        positions = np.array(file.iloc[:,:2],dtype=np.float32)
                        #positions[0,:] *= -xres
                        #positions[1,:] *= -yres
                        positions = np.concatenate((positions,z_index*np.ones([positions.shape[0],1],dtype=np.float32)),axis=1)
                        ok = True 
                        
                    except:
                        pass
                    
                    if ok:
                        positions_3D = np.concatenate((positions_3D,positions),axis=0)   
                    #else:
                    #    print("#I: "+pt_file_)

                    z_index += 1    

                #if not ok:
                #   raise CPipeError("could not read cell positions")

                #print("W: "+str(positions_3D))
                if positions_3D.shape[0] == 0:
                    raise CPipeError("no point positions")
                    #print("W: "+str(positions_3D.shape[0]))
                

                print(join(db_folder,MID,'tissuecyte/slice/labels/CELLS/shape.csv'))
                print(join(db_folder,MID,'tissuecyte/slice/'+sub_dir+'/'+src_dir+'/shape.csv'),)
                
                shape_ref_f = pd.read_csv(join(db_folder,MID,'tissuecyte/slice/labels/CELLS/shape.csv'),header=None)
                shape_data_f = pd.read_csv(join(db_folder,MID,'tissuecyte/slice/'+sub_dir+'/'+src_dir+'/shape.csv'),header=None)
                shape_ref = np.array(shape_ref_f.iloc[:,:],dtype=np.float32)[0]
                shape_data = np.array(shape_data_f.iloc[:,:],dtype=np.float32)[0]
                shape_rescale = shape_ref / shape_data
                print("#I: shape scale : {}".format(shape_rescale))

                ref_img = nib.load(db_folder+MID+'/tissuecyte/3d/c1/img3D_vis_TC_org.nii.gz')
                scale_fact_x = (xres/50.0) * shape_rescale[0]
                scale_fact_y = (yres/50.0) * shape_rescale[1]

                #scale_fact_x = (xres)
                #scale_fact_y = (yres)

                T = ref_img.header.get_sform()    

                if np.any(positions_3D < 0) :
                        print("#I: 3D coordinates with coordinates < 0")

                P = np.concatenate((positions_3D,np.ones([positions_3D.shape[0],1])),axis=1)
                #P[:,0] *= scale_fact_x
                #P[:,1] *= scale_fact_y
                P[:,0] = (P[:,0]-0.5) * scale_fact_x 
                P[:,1] = (P[:,1]-0.5) * scale_fact_y 
                P[:,2] *= 1

                #P[:,2] *= 1

                P_ants = P
                P_ants = np.transpose(np.matmul(T,np.transpose(P)))
                #print("#I: pts ants:"+str(P_ants))
                csv_out =  db_folder+MID+"/meta/pts_"+src_dir+"__org_ants_mu.csv"
                print("#I: csv_out: "+str(csv_out))
                with open(csv_out, 'w', newline='') as csvfile:
                    fieldnames = ['x', 'y', 'z','t']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                # writer.writeheader()
                    for pi in range(P_ants.shape[0]):
                        p = P_ants[pi,:]                
                        writer.writerow({'x':-p[0],  'y':-p[1],'z':p[2],'t':0})
                        #print("#I:wtf ")

                TRAFO = join(db_folder,MID,'meta/trafos/reg2TC/trafo-final')
                MOVE =   db_folder+MID+"/meta/pts_"+src_dir+"__org_ants_mu.csv"
                OUT =   db_folder+MID+"/meta/pts_"+src_dir+"_TC_std_ants_mu.csv"

                cmd = [' /disk/soft//ANTS/bin//antsApplyTransformsToPoints','-d 3  ',
                        '-i ',MOVE,' ',
                        '-o ',OUT,' ',
                        ' -t '+TRAFO+'InverseComposite.h5 ']
                cmd = " ".join(cmd)

                #print(cmd)
                result, success = pipetools.bash_run(cmd)
                
                if not success:
                    print(cmd)
                    print(result)
                    raise CPipeError("cError mapping points from org to std space")
                #assert(success)
                #print(OUT)


                positions = [] 
                with open(OUT, newline='') as csvfile:
                    fieldnames = ['x', 'y', 'z','t']
                    reader = csv.DictReader(csvfile,fieldnames=fieldnames)
                    for row in reader:
                        #print(row)
                        pts = (-float(row['x']),-float(row['y']),float(row['z']))
                        #print(type(float(row['x'])))
                        positions.append(pts)

                positions_3D = np.array(positions)
                positions_3D = positions_3D[:,:3]


                OUT_std =   db_folder+MID+"/meta/pts_"+src_dir+"_TC_std_50mu_world_space.csv"
                
                with open(OUT_std, 'w', newline='') as csvfile:
                    fieldnames = ['x', 'y', 'z']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                # writer.writeheader()
                    for pi in range(positions_3D.shape[0]):
                        p = P[pi,:]
                        writer.writerow({'x':p[0],  'y':p[1],'z':p[2]})

                if True:
                    ref_img_std = nib.load(db_folder+'/model/avg_TC_std.nii.gz')
                    T = ref_img_std.header.get_sform()

                    #print(T)
                    P = np.concatenate((positions_3D,np.ones([positions_3D.shape[0],1])),axis=1)
                    P = np.transpose(np.matmul(np.linalg.pinv(T),np.transpose(P)))

                    OUT_std =   db_folder+MID+"/meta/pts_"+src_dir+"_TC_std_50mu_voxel_space.csv"
                    
                    with open(OUT_std, 'w', newline='') as csvfile:
                        fieldnames = ['x', 'y', 'z']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    # writer.writeheader()
                        for pi in range(P.shape[0]):
                            p = P[pi,:]
                            writer.writerow({'x':p[0],  'y':p[1],'z':p[2]})

                            
                    T[1,1] = 0.050000
                    T[0,0] = 0.003000
                    T[2,2] = 0.003000    

                    P = np.concatenate((positions_3D,np.ones([positions_3D.shape[0],1])),axis=1)
                    P = np.transpose(np.matmul(np.linalg.pinv(T),np.transpose(P)))
                        
                    positions_3D_std = np.zeros([0,3],dtype=np.float32) 

                    os.makedirs(join(db_folder,MID,'tissuecyte/slice/reg/'+dest_dir+'/'),exist_ok=True)

                    shape2D = [8166, 9666]
                    shape3D = ref_img_std.shape 

                    #std_files = [f for f in listdir(join(db_folder,MID,'tissuecyte/slice/reg/'+dest_dir+'/')) if (isfile(join(db_folder,MID,'tissuecyte/slice/reg/'+dest_dir+'/',f)) and ("png" in f))] 
                    std_files = [f for f in listdir(join(db_folder,MID,'tissuecyte/slice/reg/'+std_ref_files+'/')) if (isfile(join(db_folder,MID,'tissuecyte/slice/reg/'+std_ref_files+'/',f)) and ("png" in f))] 
                    
                    
                    std_files.sort()
                    for s in std_files:
                        z_ind = shape3D[1] - (1+int(s.replace(".png",""))-10000)
                        
                        valid = np.abs(P[:,1]-z_ind)<1.0
                        P_ = P[valid,:]
                        
                        P_[:,0] = shape2D[1] -  P_[:,0]
                        P_[:,2] = shape2D[0] -  P_[:,2]
                        
                        positions_3D = np.concatenate((positions_3D,P_[:,:3]),axis=0)  
                            
                        OUT_std = join(db_folder,MID,'tissuecyte/slice/reg/'+dest_dir+'/',s.replace('png','csv'))
                        with open(OUT_std, 'w', newline='') as csvfile:
                            fieldnames = ['x', 'y','z']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            for pi in range(P_.shape[0]):
                                p = P_[pi,:]
                                writer.writerow({'x':p[2],  'y':p[0],'z':1})

                    OUT_inj = join(db_folder,MID,'tissuecyte/slice/reg/'+dest_dir+'/pts_'+src_dir+'.csv')    
                    inj_site = np.mean(positions_3D,axis=0)
                    with open(OUT_inj, 'w', newline='') as csvfile:
                            fieldnames = ['x', 'y','z']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writerow({'x':inj_site[2],  'y':inj_site[0],'z':shape3D[1]-1-np.round(inj_site[1])})
                            
                    OUT_inj = join(db_folder,MID,'tissuecyte/slice/reg/'+dest_dir+'/shape.csv')    
                    inj_site = np.mean(positions_3D,axis=0)
                    with open(OUT_inj, 'w', newline='') as csvfile:
                            fieldnames = ['x', 'y']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writerow({'x':shape2D[0],  'y':shape2D[1]})        
                    #print("done")
            else:
                print(join(db_folder,MID,'tissuecyte/slice/'+sub_dir+'/'+src_dir+'/'))
                print("does not exist, skipping")
                
    def batch_clean(self):
        pass

try:
    pipe_step = CPipePts(
        {'kn_pipeline_meso_NN_cells_3D.py'}, shortname="meso-points")
        #{'kn_pipeline_meso_NN_cells_3D.py','kn_pipeline_meso_map_highres.py'}, shortname="meso-points")


    print("#I: scriptname is \"" + pipe_step.name() + "\"")
    pipe_step.print_settings()
    slurm_params = {'queue': "kn_pipe_slave", 'time': "10-00:00:00",
                    'cores': 2, 'mem': 16000, 'gres': "KN:5", 'feature': ''}
    pipe_step.run(slurm_params, {"kn_pipeline_meso_DWI.py"})


except CPipeError as e:
    print("#E: " + e.value)
