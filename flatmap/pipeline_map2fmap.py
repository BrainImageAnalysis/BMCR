#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 16:15:31 2019

@author: skibbe-h
"""

#pip install matplotlib scipy nibabel

from nibabel import gifti as gi
import nibabel as nib
import os
import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
#import scipy
#import skimage
from PIL import Image
import imageio
from matplotlib import cm
#%matplotlib qt
from scipy.io import loadmat
import argparse

#%%
#~/data/flatmap
#pip install numpy matplotlib nibabel scikit-image scipy 


def sub2ind(ix,iy,iz,shape):
    return ((iz.astype(np.uint64) * shape[1]+iy.astype(np.uint64))*shape[2] + ix.astype(np.uint64)).astype(np.uint64)


def pimg(img,mask,mode=0,alpha=1.0,gamma=1.0):
    if mode == 0:
        return ((alpha)*(img**gamma)+(1-alpha)*mask)
    else: 
        if mode == 1:
            maskc = np.concatenate((mask[:,:,np.newaxis],mask[:,:,np.newaxis],mask[:,:,np.newaxis],mask[:,:,np.newaxis]),axis=2)
            #return ((1-maskc)+cm.hot(img**gamma))[:,:,0:3]
            #return ((1-maskc)+cm.hot(img**gamma))[:,:,0:3]
            return np.maximum((1-maskc),cm.hot(img**gamma))[:,:,0:3]
        
        
#%%
parser = argparse.ArgumentParser()

parser.add_argument(
    "--images", help="input image (TC std space)",nargs='+', type=str, required=True)

parser.add_argument(
    "--flatmaps", help="output flatmaps",nargs='+', type=str, required=True)

parser.add_argument("--hashika", help="colormap",  action='store_true')



args = parser.parse_args()


nifti_files = args.images
flatmap_names = args.flatmaps


wfolder = os.path.dirname(os.path.realpath(__file__))


coords_X =  gi.read(wfolder+'/avg_SURF_std_X.shape.gii')
coords_Y =  gi.read(wfolder+'/avg_SURF_std_Y.shape.gii')
coords_Z =  gi.read(wfolder+'/avg_SURF_std_Z.shape.gii')
template =  gi.read(wfolder+'/avg_SURF_std_X.shape.gii')




#%%
X = coords_X.darrays[0].data.copy() 
Y = coords_Y.darrays[0].data.copy() 
Z = coords_Z.darrays[0].data.copy() 

#%%

for file_idx in range(0,len(nifti_files)):
        nifti_f = nifti_files[file_idx]
        flatmap_name = flatmap_names[file_idx]
        
        #%%
        if False:
            #%%
            nifti_f = nifti_files
            flatmap_name = flatmap_names
        
        print(("input: " + nifti_f))
        print(("output: " + flatmap_name))
        
        img = nib.load(nifti_f)    
        data = img.get_fdata() 
        #%%
        Xm = data.shape[0] - X - 1
        #%%
        
        
        indeces = sub2ind(Z,Y,X,data.shape)
        indeces_m = sub2ind(Z,Y,Xm,data.shape)
        
        
        template.darrays[0].data[:] = data.flatten()[indeces]
        gi.write(template,flatmap_name+"-left.shape.gii")
        template.darrays[0].data[:] = data.flatten()[indeces_m]
        gi.write(template,flatmap_name+"-right.shape.gii")
        
        
        #%%
        
        
        mapping = sio.loadmat('gifti_data_2_surface_coordinates.mat')
        
        X_2d = mapping['flatmap_coordsX']
        Y_2d = mapping['flatmap_coordsY']
        Z_2d = mapping['flatmap_coordsZ']
        mask = mapping['mask']
        
        X_2d_m = data.shape[0] - X_2d - 1
        
        #%%
        
        indeces = sub2ind(Z_2d,Y_2d,X_2d,data.shape).flatten()
        indeces_m = sub2ind(Z_2d,Y_2d,X_2d_m,data.shape).flatten()
        valid = mask.flatten()>0
        
        #%%
        gy, gx = np.meshgrid(np.arange(0, mask.shape[0]), np.arange(0,mask.shape[1]))
        
        x_min = np.min(gx.flatten()[valid])
        x_max = np.max(gx.flatten()[valid])
        y_min = np.min(gy.flatten()[valid])
        y_max = np.max(gy.flatten()[valid])
        
        #px = np.multiply(mask,gx)
        #py = np.multiply(mask,gy)
        #%%
        mask2D = mask.copy()
        mask2D = mask2D[x_min:x_max+1,y_min:y_max+1]
        mask2D = np.flip(mask2D,axis=0)
        
        
        #%%
        
        #%%
        
        
        
        if not args.hashika:
            img2D = np.zeros(X_2d.size)
            img2D[valid] = data.flatten()[indeces[valid]]
            img2D = np.reshape(img2D,X_2d.shape)
            img2D = img2D[x_min:x_max+1,y_min:y_max+1]
            img2D = np.flip(img2D,axis=0)
            img2D_l = img2D.copy()
            
            img2Di = img2D.copy()
            img2Di /=  (np.max(img2Di) + 0.0000000000001)
            
            f_out = flatmap_name+'-left.png'
            imageio.imwrite(f_out,((2**16-1)*pimg(img2Di,mask2D)).astype(np.uint16)) 
            f_out = flatmap_name+'-left_hot.png'
            imageio.imwrite(f_out,((2**8-1)*pimg(img2Di,mask2D,mode=1)).astype(np.uint8)) 
            f_out = flatmap_name+'-left_hot_sqrt.png'
            imageio.imwrite(f_out,((2**8-1)*pimg(img2Di,mask2D,mode=1,gamma=0.5)).astype(np.uint8))
                    
            img2D = np.zeros(X_2d.size)
            img2D[valid] = data.flatten()[indeces_m[valid]]
            img2D = np.reshape(img2D,X_2d.shape)
            img2D = img2D[x_min:x_max+1,y_min:y_max+1]
            img2D = np.flip(img2D,axis=0)
            img2D_r = img2D.copy()
            
            img2Di = img2D.copy()
            img2Di /=  (np.max(img2Di) + 0.0000000000001)
            
            
            f_out = flatmap_name+'-right.png'
            imageio.imwrite(f_out,((2**16-1)*pimg(img2Di,mask2D)).astype(np.uint16)) 
            f_out = flatmap_name+'-right_hot.png'
            imageio.imwrite(f_out,((2**8-1)*pimg(img2Di,mask2D,mode=1)).astype(np.uint8)) 
            f_out = flatmap_name+'-right_hot_sqrt.png'
            imageio.imwrite(f_out,((2**8-1)*pimg(img2Di,mask2D,mode=1,gamma=0.5)).astype(np.uint8))
        else:
            #%%
            img2D = np.zeros(X_2d.size)
            img2D[valid] = data.flatten()[indeces[valid]]
            img2D = np.reshape(img2D,X_2d.shape)
            img2D = img2D[x_min:x_max+1,y_min:y_max+1]
            img2D = np.flip(img2D,axis=0)
            img2D_l = img2D.copy()
            
            cmap_r = loadmat('./mycmap.mat')['cmap_r'][0]
            cmap_g = loadmat('./mycmap.mat')['cmap_g'][0]
            cmap_b = loadmat('./mycmap.mat')['cmap_b'][0]
            
            #img2D_l[img2D_l>10000] = 255
            img2D_l[img2D_l>=10000]  += 786 - 10000 
            
            #imgRGB = np.concatenate((cmap_r[img2D_l[:,:,np.newaxis].astype(np.uint32)],cmap_g[img2D_l[:,:,np.newaxis].astype(np.uint32)],cmap_b[img2D_l[:,:,np.newaxis].astype(np.uint32)]),axis=2);
            imgRGB = np.concatenate(       (np.multiply(mask2D[:,:,np.newaxis],cmap_r[img2D_l[:,:,np.newaxis].astype(np.uint32)]),
                                            np.multiply(mask2D[:,:,np.newaxis],cmap_g[img2D_l[:,:,np.newaxis].astype(np.uint32)]),
                                            np.multiply(mask2D[:,:,np.newaxis],cmap_b[img2D_l[:,:,np.newaxis].astype(np.uint32)]))
                                            ,axis=2);
            f_out = flatmap_name+'-labels_left.png'
            imageio.imwrite(f_out,imgRGB.astype(np.uint8))
            
            
            img2D = np.zeros(X_2d.size)
            img2D[valid] = data.flatten()[indeces_m[valid]]
            img2D = np.reshape(img2D,X_2d.shape)
            img2D = img2D[x_min:x_max+1,y_min:y_max+1]
            img2D = np.flip(img2D,axis=0)
            img2D_r = img2D.copy()
            
            #img2D_r[img2D_r>10000] = 255
            img2D_r[img2D_r>=10000]  += 786 - 10000 
            
            
            imgRGB = np.concatenate(       (np.multiply(mask2D[:,:,np.newaxis],cmap_r[img2D_r[:,:,np.newaxis].astype(np.uint32)]),
                                            np.multiply(mask2D[:,:,np.newaxis],cmap_g[img2D_r[:,:,np.newaxis].astype(np.uint32)]),
                                            np.multiply(mask2D[:,:,np.newaxis],cmap_b[img2D_r[:,:,np.newaxis].astype(np.uint32)]))
                                            ,axis=2);
            f_out = flatmap_name+'-labels_right.png'
            imageio.imwrite(f_out,imgRGB.astype(np.uint8))
            
        
        

