#!/usr/bin/env python

import sys
import os
import math
import re
from os.path import isfile, join, isdir


from kn_common import pipetools,pipedef
from kn_pipeline_class import CPipeError,CPipeStep


class CPipeStepStitch3D(CPipeStep):
	reg_name = "img3D_bg_TC_org.nii.gz"
	reg_channel=1



	def progress_update(self,txt):
	  if re.match(r'#PROGRESS#\d*#', txt):
	    progress=int(re.search(r'\d+', txt).group())
	    self.update_progress("run",progress)
	  else:
	    print("#I: "+txt)
	    sys.stdout.flush()

	matlab_tools=pipedef.matlab_tools
	matlab_bin==pipedef.matlab_bin
	channels = [1,2,3]      
	def batch_run(self):
		#matlab_tools='/disk/k_raid/KAKUSHIN-NOU-DATA/SOFT/pipeline/pipeline_local/matlab/'
		#matlab_bin="/disk/soft/MATLAB/matlab2019/bin/matlab"
	  
		print("#I: creating dest folders")
		ofolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/"
		metafolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/meta"        
		trafo_file=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/meta/tif2nii_trafo.mat"
		regfile=ofolder+self.reg_name #"/img3D_vis_TC_org.nii.gz";
		cmd = 'mkdir -p '+ofolder+" "+metafolder
		res , folder_success  = pipetools.bash_run(cmd)
		if not (folder_success):
		    raise CPipeError(" mkdir failed")
        

		#for channel in range(1, 7):
		for channel in self.channels:        
			mkdir="mkdir -p "+pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/c"+format(channel)
			print("#I: "+mkdir)
			res , folder_success  = pipetools.bash_run(mkdir)

			if not (folder_success):
					raise CPipeError("creating folders failed")
	  
	  
		success=True
		#for channel in range(1, 7):
		for channel in self.channels:
		  #if channel==1:
			      ifolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/slice/"
			      ofolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"
		
			      poff=(float(channel)-1)/len(self.channels)
			      pscale=float(1)/float(len(self.channels))

			      MCOMMAND='cd '+self.matlab_tools+'/; addpath(pwd);'
			      #MCOMMAND+="tissuecyte_stitch_3D(\'"+ifolder+"\',\'"+ofolder+"\',"+format(channel)+',\'progress_parm\',['+\
			      MCOMMAND+="tissuecyte_stitch_3D_2020(\'"+ifolder+"\',\'"+ofolder+"\',"+format(channel)+',\'progress_parm\',['+\
					format(poff)+','+format(pscale)+'],\'trafo_file\',\''+trafo_file+'\');'
			      MCOMMAND+='exit;'
      
			      COMMAND=self.matlab_bin+" -r \""+MCOMMAND+"\""

			      success  = pipetools.bash_run_and_print(COMMAND,self.progress_update)
	      
			      if not success:
				      raise CPipeError("3D stitching of channel "+format(channel)+" failed")
			      #else:
				#      progress=int(math.ceil(95*(float(channel)/float(6))));
				 #     self.update_progress("run",progress)
	    


		ofile_rel="../c"+format(self.reg_channel)+"/"+"/img3D_vis_TC_org.nii.gz";    
		if os.path.islink(regfile):
		    print("#I: symlink exists, updating ...")
		    cmd = "rm "+regfile
		    print("#I: running command ("+cmd+")")
		    res , folder_success  = pipetools.bash_run(cmd)
		    if not (folder_success):
		        print(res[0])
		        print(res[1])
		        raise CPipeError(" removing symlink failed")
		cmd = 'ln -s '+ofile_rel+" "+regfile
		print("#I: running command ("+cmd+")")
		res , folder_success  = pipetools.bash_run(cmd)
		if not (folder_success):
				print(res[0])
				print(res[1])
				raise CPipeError(" symlink failed")
	  
		self.create_previews()  
		#self.local_chgrp(pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/ "+" -R")
		#self.local_chmod(" +Xr ",pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/ ")
		#self.local_chmod(" +Xr ",pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d -R")

	def create_previews(self):
		#matlab_tools='/disk/k_raid/SOFTWARE/KAKUSHI-NOU/nakae_pipeline/';
		#matlab_tools='/disk/k_raid/SOFTWARE/KAKUSHI-NOU/pipeline/tissuecyte/'
		#matlab_bin="/disk/k_raid/SOFTWARE/MATLAB/matlab2015a//bin/matlab"

		print("#I: creating preview images")
		preview_folder=pipedef.PIPELINE_DATABSE_FOLDER+"/preview/"+format(self.mid)+"/"
		mkdir="mkdir -p "+preview_folder
		print("#I: "+mkdir)
		res , folder_success  =  pipetools.bash_run(mkdir)
		if not (folder_success):
		    raise CPipeError("#E: creating folders failed")

		success=True;    
		print("#I: creating preview image ")

		ofolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/reg/"
		#ofile=ofolder+"/img3D_vis_TC_org.nii.gz";
		ofile=ofolder+self.reg_name #"/img3D_vis_TC_org.nii.gz";

		ifolder=ofile

		MCOMMAND='cd '+self.matlab_tools+'/; addpath(pwd);'
		MCOMMAND+="thumbnail_nifti(\'"+preview_folder+"/"+pipe_step.name()+"\',\'"+ifolder+"\');"
		MCOMMAND+='exit;'

		print("#I: "+MCOMMAND)

		command=self.matlab_bin+" -r \""+MCOMMAND+"\""

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
            

     
		prev_path="\{PREVIEWFOLDER\}"+"/"+self.mid+"/"+pipe_step.name()

		bla, table, blu=res[0].split('####')


		print("#I: creating html code")

		html=""

		html+="echo '<div class=\"group2\"  style=\"font-size:16px;background-color:black;\">';"
		html+="echo '<table width=\"100%\">';"
		html+="echo '<tr>';"
		html+="echo '<td><img src=\""+prev_path+"normal_1-1.png\" style=\"image-rendering: pixelated;\" width=100%></td>';"
		html+="echo '<td><img src=\""+prev_path+"normal_1-2.png\" style=\"image-rendering: pixelated;\"  width=100%></td>';"
		html+="echo '<td><img width=100%></td>';"
		#html+="echo '<td>TXT</td>';";
		html+="echo '</tr>';"
		html+="echo '<tr>';"
		html+="echo '<td><img src="+prev_path+"normal_2-1.png style=\"image-rendering: pixelated;\" width=100%></td>';"
        #html+="echo '<td><img src=\""+prev_path+"normal_2-2.png\" width=100%></td>';";
		html+="echo '<td style=\"align: center;\">"+table+"</td>';"
		html+="echo '<td></td>';"
		html+="echo '</tr>';"
		html+="echo '</table>';"
		html+="echo '</div><br>';"

            
		print("#I: adding detailed preview data to table")
		self.sql_add_custome_data("details",html.replace("'","\\\'"),"VARCHAR(20000)")
		print("#I: done") 
 
	def batch_clean(self):
		ofolder=pipedef.PIPELINE_DATABSE_FOLDER+"/"+format(self.mid)+"/tissuecyte/3d/"
		clearme={
		ofolder+"/c1/img3D_vis_TC_org.nii.gz",
		ofolder+"/c1/img3D_raw_TC_org.nii.gz",
		ofolder+"/c2/img3D_vis_TC_org.nii.gz",
		ofolder+"/c2/img3D_raw_TC_org.nii.gz",
		ofolder+"/c3/img3D_vis_TC_org.nii.gz",
		ofolder+"/c3/img3D_raw_TC_org.nii.gz",
		}
	    
		deldir_basedir=pipedef.PIPELINE_KN_RAID_DEL+"/"
		deldir=self.mid+pipetools.get_folder_timestamp()
		self.local_mkdir(deldir_basedir+deldir)
		
		for delme in clearme:
		  if not os.path.isfile(delme):
		    print("#W: skipping "+delme+", does not exist")
		  else:  
		    self.local_mv(delme,deldir_basedir+deldir)
		      
		SLURM_command={"cd "+deldir_basedir+" && rm "+deldir+" -r"}
		
		res, success=pipetools.slurm_submit(SLURM_command,self.ofile,name=self.mid+"-CLEAN-"+self.shortname,queue="kn_pipe_cleanup")
		if not success:
		    raise CPipeError("submitting cleaning script failed "+format(res[0]));	
		  
try:
	pipe_step=CPipeStepStitch3D({'kn_pipeline_meso_type.py'},shortname="meso-S3D")
	print("#I: scriptname is \""+pipe_step.name()+"\"")
	pipe_step.print_settings()
	slurm_params={'queue':"kn_pipe_IO",'time':"10-00:00:00",'cores':40,'mem':50000,'gres':"KN:10"}
	pipe_step.run(slurm_params,{'kn_pipeline_meso_inj_seg.py','kn_pipeline_meso_reg2TCstd.py','kn_pipeline_meso_NN_tracerseg.py'})
	
	
except CPipeError as e:
	print("#E: "+e.value)







