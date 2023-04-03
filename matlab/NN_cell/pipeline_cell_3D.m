function pipeline_cell_3D(mid)
%%


pid = feature('getpid');
fprintf('MATLAB PID: %d\n',pid);




[pathstr, name, ext]=fileparts([mfilename('fullpath'),'.m']);
addpath(pathstr);
addpath([pathstr,'/..']);
%addpath([pathstr,'/filter']);
%addpath([pathstr,'/globaltrack']);
%addpath([pathstr,'/filter/sdeconv']);
[pathstr, name, ext]=fileparts([mfilename('fullpath'),'.m']);
    addpath(pathstr);
    addpath([pathstr,'/../nifti_tool/']);

%mid = 'R01_0048_CM1011F';

try 

    %bg_img = load_untouch_nii(['/disk/k_raid/KAKUSHIN-NOU-DATA/database/',mid,'/tissuecyte/3d/c1/img3Dcubic_org.nii.gz']);
    %ofile = ['/disk/k_raid/KAKUSHIN-NOU-DATA/database/',mid,'/tissuecyte/3d/inj/cell_density.nii.gz'];
    bg_img = load_untouch_nii(['/disk/k_raid/KAKUSHIN-NOU-DATA/database/',mid,'/tissuecyte/3d/reg/img3D_bg_TC_org.nii.gz']);
    ofile = ['/disk/k_raid/KAKUSHIN-NOU-DATA/database/',mid,'/tissuecyte/3d/inj/cell_density_TC_org.nii.gz'];
    ofile_center = ['/disk/k_raid/KAKUSHIN-NOU-DATA/database/',mid,'/tissuecyte/3d/inj/inj_center_TC_org.nii.gz'];
    ofile_cell_counts = ['/disk/k_raid/KAKUSHIN-NOU-DATA/database/',mid,'/tissuecyte/3d/inj/cell_counts_raw_TC_org.nii.gz'];
    


    cell_dir = ['/disk/k_raid/KAKUSHIN-NOU-DATA/database/',mid,'/tissuecyte/slice/labels/CELLS/'];

    shape2D = csvread([cell_dir,'/shape.csv']);

    shape2D_target = size(bg_img.img);
    shape2D_target = shape2D_target(1:2);
    shape2D_scale = shape2D_target./shape2D; 

    files = dir([cell_dir,'slice*.csv']);


    %%
    %bg_img.img(:) = 0;
    cells3D = zeros(size(bg_img.img),'single');

    inj_center = [0,0,0];
    num_samples = 0;
    
    for f = 1:numel(files)
        success = false;
        try
        cell_pos = csvread([cell_dir,'/',files(f).name]);
        %fprintf('%d %d\n',size(cell_pos));
        fprintf('%d %d\n',size(cell_pos));
        success = true;
         catch

        end

        if success
            %cell_pos = cell_pos(cell_pos(:,3) == 0.5,1:2);
            cell_pos = cell_pos(cell_pos(:,3) >= 0.5,1:2);
            %fprintf('cell pos : %d \n',numel(cell_pos));
            if numel(cell_pos) > 0
            
                cell_pos  = ceil(cell_pos .*(repmat(shape2D_scale,size(cell_pos,1),1)));
                cell_pos  = max(cell_pos,1);
                cell_pos (:,1) = min(cell_pos (:,1),shape2D(1));
                cell_pos (:,2) = min(cell_pos (:,2),shape2D(2));

                sid = str2num(files(f).name(6:9))+1 - 1000;

                inj_center = inj_center + [sid*size(cell_pos,1),sum(cell_pos(:,1)),sum(cell_pos(:,2))];
                num_samples = num_samples + size(cell_pos,1);

                IND = sub2ind(shape2D_target,cell_pos(:,1),cell_pos(:,2));
                slice2D = zeros(shape2D_target,'uint16');
                for ind_ = 1:numel(IND)
                    ind = IND(ind_ );
                 %bg_img.img(ind,sid) = bg_img.img(ind,sid) + 1;   
                 %fprintf(':)');
                 slice2D(ind) = slice2D(ind) + 1;
                end
                %if (numel(cell_pos)>2)
                %    slice2D_ = slice2D;
                %end
                    
                %fprintf('\n');
                cells3D(:,:,sid) = slice2D;   
            end
            %bg_img.img(IND,sid) = bg_img.img(IND,sid) + 1;
        end

    end

    %%
    
    inj_center = inj_center/num_samples;
    
    
    %%
    inj_center = max(min(round(inj_center),size(bg_img.img)),1);

    inj3D = zeros(size(bg_img.img),'single');
    
    inj3D(inj_center(2),inj_center(3),inj_center(1)) = 1;
    inj3D = single((bwdist(inj3D)<5));
    bg_img.hdr.dime.datatype=16;
    bg_img.hdr.dime.bitpix=32;
    bg_img.hdr.dime.glmax=max(inj3D(:));
    bg_img.hdr.dime.glmin=min(inj3D(:));        
    bg_img.img = inj3D;
    save_untouch_nii(bg_img,ofile_center);
    
    
    
    %%
    cells3Ds = pipeline_im_smooth2D(cells3D,1.5,'normalize',false);
    cells3Ds = cells3Ds .*(cells3Ds>5);

    [L, NUM] = bwlabeln(cells3Ds>0);
    max_id = -1;
    max_members = 0;
    for l=1:NUM
        members = sum(L(:) == l);
        if members > max_members
            max_id = l;
            max_members = members;
        end
    end
    cells3Ds = cells3Ds .* (L == max_id);


    bg_img.hdr.dime.datatype=16;
    bg_img.hdr.dime.bitpix=32;
    bg_img.hdr.dime.glmax=max(cells3Ds(:));
    bg_img.hdr.dime.glmin=min(cells3Ds(:));        
    bg_img.img = cells3Ds;
    save_untouch_nii(bg_img,ofile);
    
    bg_img.hdr.dime.datatype=512;
    bg_img.hdr.dime.bitpix=16;
    bg_img.hdr.dime.glmax=uint16(max(cells3D(:)));
    bg_img.hdr.dime.glmin=uint16(min(cells3D(:)));        
    bg_img.img = uint16(cells3D);
    save_untouch_nii(bg_img,ofile_cell_counts);   

catch ME
    fprintf('an error occured: %s\n',ME.message);
    for s=1:numel(ME.stack)
    fprintf('file: %s\nname: %s\nline: %d\n',ME.stack(s).file,ME.stack(s).name,ME.stack(s).line)
    end;
    if usejava('jvm') && ~feature('ShowFigureWindows')
    exit(1);
    end;
end;
