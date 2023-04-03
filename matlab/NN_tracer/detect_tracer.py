#   this software is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.



import imp

import signal
import numpy as np
#import tensorflow as tf
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()

import scipy
import sys
import os
import argparse
from PIL import Image
import csv
import scipy.io as sio
#Image.MAX_IMAGE_PIXELS = 1000000000 
import socket
import skimage
from myunet import tracer_cnn
import imageio
Image.MAX_IMAGE_PIXELS = None

#from net_params import *

#params = set_params();

scale_intensity = 1.0 /  2.0**16
#scale_intensity = 1.0 /  2.0**8
#output_shape = [572, 572]



#def dsp(txt,o=False):
#    if o:
        #sys.stdout.write('%s\r' % txt)
        #sys.stdout.flush()
        #print(txt, end='\r')
#        print("'\r{0}".format(txt), end='')
#    else:
#        print(txt)
#    sys.stdout.flush()


global terminate
terminate = False




parser = argparse.ArgumentParser()

parser.add_argument(
    "--fg", help="input image (tracer channel)",nargs='+', type=str, required=True)

parser.add_argument(
    "--bg", help="input image (background channel)",nargs='+', type=str, required=True)

parser.add_argument("--prob", default=0.5, type=float,
                    help="probability threshold")

parser.add_argument("--sprob", default=-1, type=float,
                    help="probability (soft) threshold")

parser.add_argument("--loss_layer", default=-1, type=int,
                    help="use a different output layer than default")




#parser.add_argument("--skip_threshold", default=-1, type=float,
parser.add_argument("--skip_threshold", default=0.003, type=float,
                    help="skip tile if intensity is below threshold")

parser.add_argument("--skip_percent", default=-1, type=float,
                    help="skip tile if less than skip_percent pixels are below threshold")



parser.add_argument("--min_size", default=4, type=int,
                    help="min island size")


parser.add_argument("--out", default="",
                    help="a binary image with the detected locations",nargs='+', type=str, required=True)

parser.add_argument("--model", default="./model/",
                    help="network model directory")

parser.add_argument("--chkpt", default="newest",
                    help="model checkpoint")

parser.add_argument("--pipe", action='store_true', help="")


parser.add_argument("--nomask", action='store_true', help="")

parser.add_argument("--max_if_exists", action='store_true', help="")







args = parser.parse_args()


model_name = args.model
model_dir =  os.path.dirname(model_name)+"/"

print("using network params from "+model_dir)
module = imp.load_source('net_params', model_dir+'/net_params.py')
params = module.set_params()
dsp = module.dsp


#for key, value in params.items():
#    print(key + " --> "+format(value))

#print("::::"+params['downscale_input'])

def signal_handler(signal, frame):
    dsp('terminating program')
    global terminate
    terminate = True


dsp("")
dsp("")
dsp("this software is distributed in the hope that it will be useful,")
dsp("but WITHOUT ANY WARRANTY; without even the implied warranty of")
dsp("MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.")
dsp("")
dsp("")
dsp("HOSTNAME: {}".format(socket.gethostname()))
dsp("")
dsp("")

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


output_shape = params['output_shape']

if len(args.fg) != len(args.bg) and  len(args.fg) != len(args.out):
    dsp("please provide the same number of filenames for fg, bg, and out")

else:
    for file_idx in range(0,len(args.fg)):
        if not terminate:
            f_fg = args.fg[file_idx]
            f_bg = args.bg[file_idx]
            f_out = args.out[file_idx]
            
            
            dsp("reading the foreground image {}".format(f_fg))
            #img_fg_ = np.array(scipy.misc.imread(args.fg, mode='F')).astype(np.float32)
            #img_fg_ = np.array(scipy.misc.imread(f_fg, mode='F')).astype(np.float32)
            img_fg_ = np.array(
                    imageio.imread(f_fg, pilmode='F')).astype(np.float32)

            dsp("image shape {}".format(img_fg_.shape))
            img_fg_ *= scale_intensity
            
            dsp("reading the background image {}".format(f_bg))
            #img_bg_ = np.array(scipy.misc.imread(args.bg, mode='F')).astype(np.float32)
            #img_bg_ = np.array(scipy.misc.imread(f_bg, mode='F')).astype(np.float32)
            img_bg_ = np.array(
                    imageio.imread(f_bg, pilmode='F')).astype(np.float32)
            
           # if False:
           # 	print("computing intensity mask")           	 
	#			img_mask = np.invert(skimage.morphology.remove_small_objects(img_bg_<(100),min_size=500))
            #	img_mask = skimage.morphology.remove_small_objects(img_mask,min_size=5000)
            
            dsp("image shape {}".format(img_bg_.shape))
            img_bg_ *= scale_intensity
            
            
            print("MIN MAX : {} {}".format(np.min(img_fg_),np.max(img_fg_)))
            
            #img_fg_ = img_fg_ [::2,::2]
            #img_bg_ = img_bg_ [::2,::2]
            
            print("scaleing : {}".format(scale_intensity))
        
            # pad the image with zero borders
            img_shape = np.maximum(img_fg_.shape, output_shape) + \
                (output_shape - np.asarray([452, 452]))
        
            img_shape += img_shape % 2
            print("temporary image shape  {}".format(img_shape))
            img_fg = np.zeros(img_shape, dtype=img_fg_.dtype)
            img_bg = np.zeros(img_shape, dtype=img_fg_.dtype)
            
        
            img_offset = (((img_shape) - (img_fg_.shape))/2).astype(int)
            print("offset {}".format(img_offset))
            img_fg[img_offset[0]: img_offset[0] + img_fg_.shape[0],
                   img_offset[1]: img_offset[1] + img_fg_.shape[1]] = img_fg_
        
            img_bg[img_offset[0]: img_offset[0] + img_bg_.shape[0],
                   img_offset[1]: img_offset[1] + img_bg_.shape[1]] = img_bg_
                   
        
            print("computing valid pixel mask")
            img_fg_filt = scipy.ndimage.filters.maximum_filter(img_fg,51)
            #img_fg_valid = np.logical_not(scipy.ndimage.filters.maximum_filter(img_fg_filt==0,51))
            #img_fg_valid = np.logical_not(scipy.ndimage.filters.maximum_filter(img_fg_filt==0,101))
            img_fg_valid = np.logical_not(scipy.ndimage.filters.maximum_filter(img_fg_filt==0,151))
            img_bg_filt = scipy.ndimage.filters.maximum_filter(img_bg,51)
            #img_bg_valid = np.logical_not(scipy.ndimage.filters.maximum_filter(img_bg_filt==0,51))
            #img_bg_valid = np.logical_not(scipy.ndimage.filters.maximum_filter(img_bg_filt==0,101))
            img_bg_valid = np.logical_not(scipy.ndimage.filters.maximum_filter(img_bg_filt==0,151))
            
            img_fg_maxfilt = np.logical_and(img_fg_valid,img_bg_valid)
            
            if args.nomask:
                img_fg_maxfilt[:] = True
	            
            #if False:
           # 	print("applying intensity pixel mask")
           # 	#scipy.misc.imsave('/home/skibbe-h/wtf1.png', (255*img_fg_maxfilt).astype(np.uint8))
           # 	#scipy.misc.imsave('/home/skibbe-h/wtf2.png', (255*img_mask).astype(np.uint8))
           # 	img_fg_maxfilt[img_offset[0]: img_offset[0] + img_bg_.shape[0],
           #     	   img_offset[1]: img_offset[1] + img_bg_.shape[1]] = np.multiply(img_fg_maxfilt[img_offset[0]: img_offset[0] + img_bg_.shape[0],
           #     	   img_offset[1]: img_offset[1] + img_bg_.shape[1]],img_mask)
       
            #scipy.misc.imsave('/home/skibbe-h/wtf3.png', (255*img_fg_maxfilt).astype(np.uint8))
        
            
            #img_fg *= img_fg_maxfilt
            #img_bg *= img_fg_maxfilt
            
            
            
            #img_fg_maxfilt = scipy.ndimage.filters.maximum_filter(img_fg,size=5)
            
            
            
            #img_bg_maxfilt = scipy.ndimage.filters.maximum_filter(img_bg,size=5)
            
            #scipy.misc.imsave("debugme.png", img_fg_maxfilt/np.max(img_fg_maxfilt).astype(np.float32))
                   
                   
            print("MIN MAX : {} {}".format(np.min(img_fg),np.max(img_fg)))
            print("TYPE {} ".format(img_fg.dtype))
        
            dsp("preparing NN")
            full_shape = img_fg.shape
            new_graph = tf.Graph()
            with tf.Session(graph=new_graph) as sess:
                # First let's load meta graph and restore weights
                saver = tf.train.import_meta_graph(model_name+'-0.meta')
        
                graph = tf.get_default_graph()
        
                # x is our input image, y the prediction
                #y = graph.get_tensor_by_name("loss_layer"+str(0)+"ypred:0")
                
                if args.loss_layer > -1:
                    d = args.loss_layer 
                    y = graph.get_tensor_by_name("loss_layer"+str(d)+"ypred:0")
                    for s in range(0,d+params['network']['downscale_input']):
                        y = tracer_cnn.upscale(y, k=2, features_in=1, features_out=1)
                    
                else:  # (default)
                    y = graph.get_tensor_by_name("prediction:0")
                
                
                    
                
                x = graph.get_tensor_by_name("x:0")
        
        
                dropout_up = graph.get_tensor_by_name("dropout_up:0")
                dropout_down = graph.get_tensor_by_name("dropout_down:0")
                is_training = graph.get_tensor_by_name("is_training:0")
        
                sess.run(tf.global_variables_initializer())
        
                # define the model of the NN
                if args.chkpt == "newest":
                    chkpt = tf.train.latest_checkpoint(
                        model_dir, latest_filename="checkpoint")
                    dsp("using most recent checkpoint {}".format(chkpt))
                else:
                    chkpt = model_name + "-" + args.chkpt
                    dsp("using the recent checkpoint {}".format(chkpt))
        
                if chkpt is not None:
                    # load and restore the model
                    saver.restore(sess, chkpt)
                    img = np.concatenate([img_bg[np.newaxis, :, :, np.newaxis],img_fg[np.newaxis, :, :, np.newaxis]],axis=3)
        
                    # we cannot process the image at once
                    # --> we work on smaller image tiles of size "output_shape"
                    patch_size = np.array([output_shape[0], output_shape[1]])
                    output_size = None
                    shape_offset = None
                    offset = [0, 0]
        
                    # in rimg we store the results (predictions of the NN)
                    rimg = np.zeros(full_shape)
            
                    skip_by_area = (args.skip_percent > 0)
        
                    count = 0
                    stop_x = 0
                    #rimg = np.copy(img_fg_maxfilt)
                    if True:
                    # here we run the image and search for terminals
                        while (offset[0] + patch_size[0]-1) < full_shape[0] and (stop_x < 2) and not terminate:
            
                            stop_y = 0
                            while (offset[1] + patch_size[1]-1) < full_shape[1] and (stop_y < 2) and not terminate:
                                
                                count += 1
                                current_img = img[:, offset[0]: offset[0] + patch_size[0],
                                                  offset[1]: offset[1] + patch_size[1], :]
                                
                                threshold_test_ok = True
                                if (skip_by_area):
                                    #dsp("")
                                    #dsp("")
                                    #dsp("{} - {}".format(np.sum(current_img > args.skip_threshold) ,(patch_size[0]*patch_size[1] * args.skip_percent)))
                                    #dsp("")
                                    #dsp("")
                                    threshold_test_ok  = (np.sum(current_img > args.skip_threshold) > (patch_size[0]*patch_size[1] * args.skip_percent))
                                else:
                                    threshold_test_ok  = np.max(current_img ) > args.skip_threshold
                                
                                if args.skip_threshold<0 or threshold_test_ok or (count == 1):
                                    if not args.pipe:
                                        dsp("predicting {} {}".format(offset[0], offset[1]),True)
                                        #dsp("predicting {} {} / {}".format(offset[0], offset[1],np.max(current_img )))
                
                                    feed_dict = {x: current_img,
                                                 dropout_down: 1,
                                                 dropout_up: 1,
                                                 is_training: False}
                                    prediction = sess.run([y], feed_dict)
                
                                    if output_size is None:
                                        output_size = np.array(prediction[0].shape[1:3])
                                        shape_offset = (patch_size - output_size)//2
                                        
                                        
                
                                    if threshold_test_ok: #and args.channel_check:
                                        #mask = np.logical_and(
                                        #        img_fg[offset[0] + shape_offset[0]: offset[0] + shape_offset[0] + output_size[0],
                                        #               offset[1] + shape_offset[1]: offset[1] + shape_offset[1] + output_size[1]] > 0,
                                        #               img_bg[offset[0] + shape_offset[0]: offset[0] + shape_offset[0] + output_size[0],
                                        #               offset[1] + shape_offset[1]: offset[1] + shape_offset[1] + output_size[1]] > 0)
                                        
                                        
                                        mask = img_fg_maxfilt[offset[0] + shape_offset[0]: offset[0] + shape_offset[0] + output_size[0],
                                                       offset[1] + shape_offset[1]: offset[1] + shape_offset[1] + output_size[1]] > 0
                                        #mask = np.logical_and(
                                        #        img_fg_maxfilt[offset[0] + shape_offset[0]: offset[0] + shape_offset[0] + output_size[0],
                                        #               offset[1] + shape_offset[1]: offset[1] + shape_offset[1] + output_size[1]] > 0,
                                        #        img_bg_maxfilt[offset[0] + shape_offset[0]: offset[0] + shape_offset[0] + output_size[0],
                                        #               offset[1] + shape_offset[1]: offset[1] + shape_offset[1] + output_size[1]] > 0)  
                                        #mask = np.logical_and(
                                        #        img_fg[offset[0] + shape_offset[0]: offset[0] + shape_offset[0] + output_size[0],
                                        #               offset[1] + shape_offset[1]: offset[1] + shape_offset[1] + output_size[1]]>50*scale_intensity,
                                        #        img_bg[offset[0] + shape_offset[0]: offset[0] + shape_offset[0] + output_size[0],
                                        #               offset[1] + shape_offset[1]: offset[1] + shape_offset[1] + output_size[1]]>50*scale_intensity
                                                #scipy.misc.imfilter(current_img[0,:,:,0]>scale_intensity,np.array([[1,1],[1,1]]) ) > 3,
                                                #scipy.misc.imfilter(current_img[0,:,:,1]>scale_intensity,np.array([[1,1],[1,1]]) ) > 3
                                        #        )
                                        
                                        #rimg[offset[0] + shape_offset[0]: offset[0] + shape_offset[0] + output_size[0],
                                        #      offset[1] + shape_offset[1]: offset[1] + shape_offset[1] + output_size[1]] = np.multiply(mask,(prediction[0][0,:,:, 0]).astype(float))
                                        rimg[offset[0] + shape_offset[0]: offset[0] + shape_offset[0] + output_size[0],
                                              offset[1] + shape_offset[1]: offset[1] + shape_offset[1] + output_size[1]] = np.minimum(mask,(prediction[0][0,:,:, 0]).astype(float))
                                        #rimg[offset[0] + shape_offset[0]: offset[0] + shape_offset[0] + output_size[0],
                                        #      offset[1] + shape_offset[1]: offset[1] + shape_offset[1] + output_size[1]] = (prediction[0][0,:,:, 0]).astype(float)
                                else:
                                    if not args.pipe:
                                        dsp("skipping {} {}".format(offset[0], offset[1]),True)
                                #print("MIN: {} MAX: {}".format(np.min(prediction[0][0,:,:, 0]),np.max(prediction[0][0,:,:, 0])))
            
                                offset[1] = offset[1] + output_size[1]
            
                                if (offset[1] + patch_size[1]) > full_shape[1] and (offset[1] + patch_size[1]-1) < full_shape[1]+patch_size[1]:
                                    offset[1] = full_shape[1] - patch_size[1]
                                    stop_y += 1
            
                            offset[1] = 0
                            offset[0] = offset[0] + output_size[0]
            
                            if (offset[0] + patch_size[0]) > full_shape[0] and (offset[0] + patch_size[0]-1) < full_shape[0]+patch_size[0]:
                                offset[0] = full_shape[0] - patch_size[0]
                                stop_x += 1
        
                        dsp("")
                        dsp("input patch shape : {}".format(output_shape))
                        dsp("outpu patch shape : {}".format(output_size))
                        dsp("")
                    # now we determine the locations of the predictions
                    if not terminate:
                        
                        # we have temporarily increase the image size,
                        # now we crop the image to its original dimension
                        rimg = rimg[img_offset[0]: img_offset[0] + img_fg_.shape[0],
                                    img_offset[1]: img_offset[1] + img_fg_.shape[1]] # >= args.prob
                        
                        print("MIN: {} MAX: {}".format(np.min(rimg),np.max(rimg)))
                        
                        if True:
                        #if False:
                            if args.sprob>0:
                                #rimgl, num_labels = scipy.ndimage.measurements.label(rimg>1.0/255)
                                #labeld_areas = scipy.ndimage.find_objects(rimgl, num_labels)
                                if args.min_size>1:
                                    rin = rimg>args.sprob
                                    print("pixel in  {}:".format(np.sum(rin)))
                                    rimg_mask = skimage.morphology.remove_small_objects(rin,min_size=args.min_size)
                                    print("pixel out {}:".format(np.sum(rimg_mask)))
                                    rimg = np.multiply(rimg_mask,rimg)
                                else:
                                    rimg[rimg<args.sprob] = 0
                        
                        
                        #if len(f_out) > 0:
                        dsp("writing predictions into the image {}".format(f_out))
                        
                        if False:
                            adict = {}
                            adict['rimg'] = rimg
                            sio.savemat(f_out.replace(".png",".mat"), adict)
                        
                        #rimg[:] = 0.1
                        #rimg = rimg - np.min(rimg)
                        #rimg = rimg / (np.max(rimg)+0.0000001)
                        rimg = np.maximum(rimg,0)
                        #scipy.misc.imsave(args.out, rimg.astype(np.float32))
                        
                        # saving image as float SCALES THE INTENSITY RANGE !!! WTF!
                        #if args.sprob>0:
                            #rimg[rimg<args.sprob] = 0
                            
                        
                        rimg *= 255
                        
                        if args.max_if_exists and os.path.isfile(f_out):
                            dsp("updating existing map with max")
                            #rimg_old = np.array(scipy.misc.imread(f_out, mode='F')).astype(np.float32)
                            rimg_old = np.array(
                                    imageio.imread(f_out, pilmode='F')).astype(np.float32)
                            rimg = np.maximum(rimg,rimg_old)
                            if args.sprob>0:
                                rimg[rimg<(255*args.sprob)] = 0
                            
                        
                        #scipy.misc.imsave(f_out, rimg.astype(np.uint8))
                        imageio.imwrite(f_out, rimg.astype(np.uint8))
        
                        dsp("done")


print("gracefully exiting program")
