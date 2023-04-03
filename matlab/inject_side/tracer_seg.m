function tracer_seg(mid)


try 
    

        %%
        addpath  /disk/k_raid/SOFTWARE/KAKUSHI-NOU/nifti_tool/


        database='/disk/k_raid/KAKUSHIN-NOU-DATA/database/';
        infile=[mid,'/tissuecyte/3d/c3/img3D_raw_TC_org.nii.gz'];
        
        ofile=[mid,'/tissuecyte/3d/inj/inj_mask_TC_org.nii.gz'];




        bla=load_untouch_nii([database,infile]);
        img1 = medfilt3(bla.img);
        img2=(mhs_smooth_img(single(img1>min(max(img1(:))*0.5,4500)),3,'normalize',true));

        
        BW = (img2 > (0.5 * max(img2(:))));

        %%

        [L,NUM] = bwlabeln(BW);
        labels=unique(L(:)); 
        u=[];for l = 1:numel(labels); u(l)=sum(L(:)==labels(l));end;
        [v,indx]=max(u);u(indx)=-1;
        [v,indx]=max(u);
        L2=(L==labels(indx));

        %%

        bla.img=uint16(L2);
        %save_nii(bla,[database,ofile]);
        save_untouch_nii(bla,[database,ofile]);



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




    



