function tracer_seg_preview(mid,ofolder)


try 
    

        %%
        addpath  /disk/k_raid/SOFTWARE/KAKUSHI-NOU/nifti_tool/


        database='/disk/k_raid/KAKUSHIN-NOU-DATA/database/';
        %infile=[mid,'/tissuecyte/3d/c3/img3Dcubic_org.nii.gz'];
        infile=[mid,'/tissuecyte/3d/c3/img3D_vis_TC_org.nii.gz'];
        %ofile=[mid,'/tissuecyte/3d/inj/inj_mask.nii.gz'];
        ofile=[mid,'/tissuecyte/3d/inj/inj_mask_TC_org.nii.gz'];




        img_back=load_nii([database,infile]);
        img_sig=load_nii([database,ofile]);
        
        img{1}=single(img_back.img);
        img{2}=single(img_sig.img);
        
        shape=size(img{2});
        imgRGB=zeros([shape(1:2),3]);

        
        for a=1:2
           img{a}=img{a}-min(img{a}(:));
           img{a}=img{a}./(max(img{a}(:))+eps);
           img2D=squeeze(max(img{a},[],3));
           imgRGB(:,:,a)=img2D;
        end
        
        
        
        
        img2D=imgRGB;
        
        ofname=[ofolder,'_t_normal.jpg'];
        imwrite(img2D,ofname);

        ofname=[ofolder,'_t_small.jpg'];
        imwrite(imresize(img2D,0.25,'bicubic'),ofname);


        shape=size(img2D);
        shape=shape(1:2);
        newshape=shape./max(shape);
        new_shape=ceil([60,60].*newshape);
        ofname=[ofolder,'_t_tiny.jpg'];
        imwrite(imresize(img2D,new_shape,'bicubic'),ofname);
        fprintf('done\n');
        
        
        
        
        
        
        
        


catch ME
   % gpu=gpuDevice;
   % gpu
    fprintf('an error occured: %s\n',ME.message);
    for s=1:numel(ME.stack)
    fprintf('file: %s\nname: %s\nline: %d\n',ME.stack(s).file,ME.stack(s).name,ME.stack(s).line)
    end;
    if usejava('jvm') && ~feature('ShowFigureWindows')
    exit(1);
    end;
end;

