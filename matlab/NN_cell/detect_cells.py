#   this software is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.


#python detect_terminals.py --fg ../uemura-sensei/2018_corrected_terminals/Fused_180130_ppkGal4_UAS-mCD8GFP_TrpA1K_8Y_4_A3m/Fused_180130_ppkGal4_UAS-mCD8GFP_TrpA1K_8Y_#4_A3m_159-234.tif  --cout output/myout.jpg --model ./model/ --prob 0.001 --dout output/dmyout.jpg  --csv output/my.csv



import signal
import numpy as np
#import tensorflow as tf

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()

import scipy
import scipy.misc
import sys
import os
import argparse
from PIL import Image
import imageio
import csv
import imp
import imageio
Image.MAX_IMAGE_PIXELS = None

#from net_params import *

#params = set_params();

scale_intensity = 1.0 / 2.0**16
#output_shape = [572, 572]




def dsp(txt):
    print(txt)
    sys.stdout.flush()


global terminate
terminate = False


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

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

parser = argparse.ArgumentParser()

parser.add_argument(
    "--fg", help="input image (if RGB, it will be converted to an intensity image)")

parser.add_argument("--prob", default=0.5, type=float,
                    help="probability threshold")

parser.add_argument("--out", default="",
                    help="a binary image with the detected locations")

parser.add_argument("--model", default="./model/",
                    help="network model directory")

parser.add_argument("--chkpt", default="newest",
                    help="model checkpoint")


args = parser.parse_args()


model_name = args.model
model_dir =  os.path.dirname(model_name)+"/"

print("using network params from "+model_dir)
module = imp.load_source('net_params', model_dir+'/net_params.py')
params = module.set_params()
dsp = module.dsp


output_shape = params['output_shape']

if True:
    dsp("reading the image")
    img_fg_ = np.array(
                    imageio.imread(args.fg, pilmode='F')).astype(float)
    #img_fg_ = np.array(scipy.misc.imread(args.fg, mode='F')).astype(float)
    dsp("image shape {}".format(img_fg_.shape))
    print(args.fg)
    print(args.out)


    img_fg_ *= scale_intensity

    # pad the image with zero borders
    #img_shape = np.maximum(img_fg_.shape, output_shape) + \
    #    (output_shape - np.asarray([452, 452]))
    img_shape = np.maximum(img_fg_.shape, output_shape) + output_shape 


    img_shape += img_shape % 2
    print("temporary image shape  {}".format(img_shape))
    img_fg = np.zeros(img_shape, dtype=img_fg_.dtype)

    img_offset = (((img_shape) - (img_fg_.shape))/2).astype(int)
    print("offset {}".format(img_offset))
    img_fg[img_offset[0]: img_offset[0] + img_fg_.shape[0],
           img_offset[1]: img_offset[1] + img_fg_.shape[1]] = img_fg_

    dsp("preparing NN")
    full_shape = img_fg.shape
    new_graph = tf.Graph()
    with tf.Session(graph=new_graph) as sess:
        # First let's load meta graph and restore weights
        saver = tf.train.import_meta_graph(model_name+'-0.meta')

        graph = tf.get_default_graph()

        # x is our input image, y the prediction
        #y = graph.get_tensor_by_name("loss_layer"+str(0)+"ypred:0")
        x = graph.get_tensor_by_name("x:0")
        y = graph.get_tensor_by_name("prediction:0")


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
            img = img_fg[np.newaxis, :, :, np.newaxis]

            # we cannot process the image at once
            # --> we work on smaller image tiles of size "output_shape"
            patch_size = np.array([output_shape[0], output_shape[1]])
            output_size = None
            shape_offset = None
            offset = [0, 0]

            # in rimg we store the results (predictions of the NN)
            rimg = np.zeros(full_shape)
    

            count = 0
            stop_x = 0
            # here we run the image and search for terminals
            while (offset[0] + patch_size[0]-1) < full_shape[0] and (stop_x < 2) and not terminate:

                stop_y = 0
                while (offset[1] + patch_size[1]-1) < full_shape[1] and (stop_y < 2) and not terminate:
                    dsp("predicting {} {}".format(offset[0], offset[1]))
                    count += 1
                    current_img = img[:, offset[0]: offset[0] + patch_size[0],
                                      offset[1]: offset[1] + patch_size[1], :]

                    feed_dict = {x: current_img,
                                 dropout_down: 1,
                                 dropout_up: 1,
                                 is_training: False}
                    prediction = sess.run([y], feed_dict)

                    if output_size is None:
                        output_size = np.array(prediction[0].shape[1:3])
                        shape_offset = (patch_size - output_size)//2

                    rimg[offset[0] + shape_offset[0]: offset[0] + shape_offset[0] + output_size[0],
                          offset[1] + shape_offset[1]: offset[1] + shape_offset[1] + output_size[1]] = (prediction[0][0,:,:, 0]).astype(float)

                    offset[1] = offset[1] + output_size[1]

                    if (offset[1] + patch_size[1]) > full_shape[1] and (offset[1] + patch_size[1]-1) < full_shape[1]+patch_size[1]:
                        offset[1] = full_shape[1] - patch_size[1]
                        stop_y += 1

                offset[1] = 0
                offset[0] = offset[0] + output_size[0]

                if (offset[0] + patch_size[0]) > full_shape[0] and (offset[0] + patch_size[0]-1) < full_shape[0]+patch_size[0]:
                    offset[0] = full_shape[0] - patch_size[0]
                    stop_x += 1

            # now we determine the locations of the predictions
            if not terminate:
                
                # we have temporarily increase the image size,
                # now we crop the image to its original dimension
                rimg = rimg[img_offset[0]: img_offset[0] + img_fg_.shape[0],
                            img_offset[1]: img_offset[1] + img_fg_.shape[1]]  #>= args.prob
                
                if len(args.out) > 0:
                    dsp("writing predictions into the image {}".format(args.out))
                    #scipy.misc.imsave(args.out, rimg.astype(float))
                    
                    rimg = np.maximum(rimg,0)
                    # saving image as float SCALES THE INTENSITY RANGE !!! WTF!
                    rimg *= 255
                    #scipy.misc.imsave(args.out, rimg.astype(np.uint8))
                    imageio.imwrite(args.out, rimg.astype(np.uint8))

                dsp("done")


print("gracefully exiting program")
