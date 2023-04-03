function pipeline_reg_mask(id)


try   
    threshold = 500;
    %threshold = 1000;
    signal_treshold = 10000;

    db = '/disk/k_raid/KAKUSHIN-NOU-DATA/database/';
    img_c1 = load_untouch_nii([db,id,'/tissuecyte/3d/c1/img3D_raw_TC_org.nii.gz']);
    img_c2 = load_untouch_nii([db,id,'/tissuecyte/3d/c2/img3D_raw_TC_org.nii.gz']);


    %%
    mask = single(img_c2.img) -single(img_c1.img);
    mask = (mask > threshold) | (img_c1.img > signal_treshold);
    %%

    mask_nii = img_c1;
    mask_nii.img(:) = uint16(mask);
    oname = [db,id,'/tissuecyte/3d/reg/img3D_bg_TC_org_mask.nii.gz'];
    save_untouch_nii(mask_nii,oname);

    mask_nii = img_c1;
    mask_nii.img(:) = uint16(~mask);
    oname = [db,id,'/tissuecyte/3d/reg/img3D_bg_TC_org_mask_inverse.nii.gz'];
    save_untouch_nii(mask_nii,oname);
    %%
catch ME
    fprintf('an error occured: %s\n',ME.message);
    for s=1:numel(ME.stack)
        fprintf('file: %s\nname: %s\nline: %d\n',ME.stack(s).file,ME.stack(s).name,ME.stack(s).line)
    end;
    if usejava('jvm') && ~feature('ShowFigureWindows')
        exit(1);
    end;
end;    