function ishii_pipeline_NN_tracer_3D(mid,varargin)


pid = feature('getpid');
fprintf('MATLAB PID: %d\n',pid);

[pathstr, name, ext]=fileparts([mfilename('fullpath'),'.m']);
addpath(pathstr);
%addpath([pathstr,'/..']);
%addpath([pathstr,'/filter']);
%addpath([pathstr,'/globaltrack']);
%addpath([pathstr,'/filter/sdeconv']);
addpath([pathstr,'/../nifti_tool/']);

threshold = 0.75;

channel=1;
progress_parm=[0,1];
  
meso_global_common

weighted_img = false;
weighted2_img = false;

addpath(pipescipts);

foldername='NN_tracer';
foldername_tracer='c2_50mu';
foldername_bg='c1_50mu';
foldername_inj='c3_50mu';

for k = 1:2:length(varargin),
            eval(sprintf('%s=varargin{k+1};',varargin{k}));
end;

try 
    
        if exist('weighted_signal_name','var')
            fprintf('creating weighted signals as well');
            weighted_img = true;
        end
        
        if exist('weighted_signal_name_single_channel','var')
            fprintf('creating weighted signals based on tracer signal channel only as well');
            weighted_img2 = true;
        end

        ifolder=[dbfolder,'/',mid,'/','/tissuecyte/slice/',foldername,'/'];
        
        
        
        ifolder_tracer=[dbfolder,'/',mid,'/','/tissuecyte/slice/',foldername_tracer,'/'];
        ifolder_bg=[dbfolder,'/',mid,'/','/tissuecyte/slice/',foldername_bg,'/'];
        ifolder_inj=[dbfolder,'/',mid,'/','/tissuecyte/slice/',foldername_inj,'/'];

        progress_old=-1;

        %files=dir([ifolder,'/slice*png']);
        files=dir([ifolder_bg,'/slice*png']);

        ofolder=[dbfolder,'/',mid,'/','/tissuecyte/3d/',foldername,'/'];
        
        
        cell_density_file=[dbfolder,'/',mid,'/','/tissuecyte/3d/inj/cell_density_TC_org.nii.gz'];
        cell_density = load_untouch_nii(cell_density_file);
        cell_density = single(cell_density.img>1);
        
        
        ref_img = load_untouch_nii(ref);
        
        shape2D = size(ref_img.img);
        shape2D = shape2D([1,2]);

        tr_img=zeros(size(ref_img.img),'single');
        
        
        if weighted_img
            tr_img_weighted=zeros(size(ref_img.img),'single');
            
        end
        if weighted_img2
            tr_img_weighted2=zeros(size(ref_img.img),'single');
        end

        
        
        for f=1:numel(files)
            fprintf('procissing slice %d of %d\n',f,numel(files));
            tic
            prediction=(imread([ifolder,'/',files(f).name]));
            fprintf('loading image took %d seconds\n',ceil(toc));
            
           
            cell_density_2D = squeeze(cell_density(:,:,f));
            
            if max(cell_density_2D(:)) > 0.5 
                tic
                %cell_density_2D = imresize(cell_density_2D,size(prediction),'nearest');
                cell_density_2D = myimresize(cell_density_2D,size(prediction),'nearest');
                
                fprintf('resizing injection site mask took %d seconds\n',ceil(toc));
                prediction_mask = max(single(prediction>threshold*256),cell_density_2D);
            else
                prediction_mask = single(prediction>threshold*256);    
            end
            %########################################
            %           NEW
            %########################################
            
            tr_img(:,:,f) = pipeline_downscale(single(prediction_mask),shape2D,true,'sum');
            
           
            
            if weighted_img || weighted_img2
           
                prediction_tr=(imread([ifolder_tracer,'/',files(f).name]));
                if weighted_img
                    tic
                    prediction_bg=(imread([ifolder_bg,'/',files(f).name]));
                    prediction = max(prediction_tr - prediction_bg,0);
                    fprintf('loading tracer image took %d seconds\n',ceil(toc));
                    prediction = single(prediction).*prediction_mask;
                    
                    %########################################
                    %           NEW
                    %########################################
                     tr_img_weighted(:,:,f)=pipeline_downscale(single(prediction),shape2D,true,'sum');
                    

                end
                if weighted_img2
                    tic
                    prediction = max(prediction_tr ,0);
                    fprintf('loading tracer image took %d seconds\n',ceil(toc));
                    prediction = single(prediction).*prediction_mask;
                    
                    %########################################
                    %           NEW
                    %########################################
                    tr_img_weighted2(:,:,f)=pipeline_downscale(single(prediction),shape2D,true,'sum');
                    
                end
                
             
            end
            
            progress=ceil(100*(progress_parm(1)+progress_parm(2)*f/numel(files)));
            if progress~=progress_old
                progress_old=progress;
                fprintf('#PROGRESS#%d#\n',progress); 
            end
        end

        tr_img(tr_img(:)<0) = 0;
        img_mask = get_mask(tr_img);
        
        
        ref_img.hdr.dime.datatype=16;
        ref_img.hdr.dime.bitpix=32;
        ref_img.hdr.dime.glmax=max(tr_img(:));
        ref_img.hdr.dime.glmin=min(tr_img(:));        
        ref_img.img = tr_img;
        save_untouch_nii(ref_img,[ofolder,'/',signal_name]);
        
        ref_img.img = tr_img.*img_mask;
        save_untouch_nii(ref_img,[ofolder,'/',strrep(signal_name,'.nii.gz','_masked.nii.gz')]);       
        
        fprintf('MIN: %f\n',min(tr_img(:)));
        fprintf('MAX: %f\n',max(tr_img(:)));
        
        
        if weighted_img
             tr_img_weighted(tr_img_weighted(:)<0) = 0;
          

            ref_img.hdr.dime.datatype=16;
            ref_img.hdr.dime.bitpix=32;
            ref_img.hdr.dime.glmax=max(tr_img_weighted(:));
            ref_img.hdr.dime.glmin=min(tr_img_weighted(:));        
            ref_img.img = tr_img_weighted;
            save_untouch_nii(ref_img,[ofolder,'/',weighted_signal_name]);
            
            ref_img.img = tr_img_weighted.*img_mask;
            save_untouch_nii(ref_img,[ofolder,'/',strrep(weighted_signal_name,'.nii.gz','_masked.nii.gz')]);

            fprintf('MIN: %f\n',min(tr_img_weighted(:)));
            fprintf('MAX: %f\n',max(tr_img_weighted(:)));
        end
        
        if weighted_img2
            tr_img_weighted2(tr_img_weighted2(:)<0) = 0;

            ref_img.hdr.dime.datatype=16;
            ref_img.hdr.dime.bitpix=32;
            ref_img.hdr.dime.glmax=max(tr_img_weighted2(:));
            ref_img.hdr.dime.glmin=min(tr_img_weighted2(:));        
            ref_img.img = tr_img_weighted2;
            save_untouch_nii(ref_img,[ofolder,'/',weighted_signal_name_single_channel]);
            
            ref_img.img = tr_img_weighted2.*img_mask;
            save_untouch_nii(ref_img,[ofolder,'/',strrep(weighted_signal_name_single_channel,'.nii.gz','_masked.nii.gz')]);

            fprintf('MIN: %f\n',min(tr_img_weighted2(:)));
            fprintf('MAX: %f\n',max(tr_img_weighted2(:)));
        end
      
catch ME
    fprintf('an error occured: %s\n',ME.message);
    for s=1:numel(ME.stack)
    fprintf('file: %s\nname: %s\nline: %d\n',ME.stack(s).file,ME.stack(s).name,ME.stack(s).line)
    end;
    if usejava('jvm') && ~feature('ShowFigureWindows')
    exit(1);
    end;
end;


function img_mask = get_mask(tr_img)
        img_bw = single(tr_img>1);
        rad = 5;
        [x,y,z] = ndgrid(-rad:rad);
        se = strel(sqrt(x.^2 + y.^2 + z.^2) <=rad);
        img_bw = imdilate(imdilate(img_bw,se),se);
        CC = bwconncomp(img_bw);
        members = [cellfun(@(x)numel(x),CC.PixelIdxList)];
        [v, indx] = sort(members);
        img_mask = zeros(size(img_bw),'single');
        img_mask(CC.PixelIdxList{indx(end)}) = 1;
        

    
    
