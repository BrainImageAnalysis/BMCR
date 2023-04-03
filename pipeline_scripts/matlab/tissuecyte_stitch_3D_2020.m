function tissuecyte_stitch_3D_2020(ifolder,ofolder,channel,varargin)
%%

make_my_nii = @(ifile,ofile,varargin)tissuecute_make_nii(ifile,ofile,varargin{:});

pid = feature('getpid');
fprintf('MATLAB PID: %d\n',pid);
%%
tmp_ = mfilename('fullpath');
[filepath,name,ext] = fileparts([tmp_,'.m']);
addpath(filepath)


progress_parm=[0,1];
threshold=10000;
metadata=ifolder;
ofolder=[ofolder,'/c',num2str(channel),'/'];
ifolder=[ifolder,'/c',num2str(channel),'/'];

element_size_xy = [50,50];

debug = false;
%%
    for k = 1:2:length(varargin),
            eval(sprintf('%s=varargin{k+1};',varargin{k}));
    end;
%%    
if ~exist('metadata_folder','var')
   metadata_folder = [metadata,'/../../']; 
end

    %%
try     

switch (channel)
    
        
    otherwise
        %%
        ofile2=[ofolder,'/img3D_vis_TC_org.nii.gz'];
        ofile1=[ofolder,'/img3D_raw_TC_org.nii.gz'];
        
        mat_name_in = [ifolder,'/slice10000_info_toplayer_1_res_50_.mat'];
        
        slice_sample = imread([ifolder,'/slice10000.png']);
        slice_info = load(mat_name_in);
        meta.pixelres = [1.385689385 ,1.339262803];
        meta.crop = [50,50,50,50];
        meta = get_TC_json_info(metadata_folder, meta);
        if slice_info.img_info.trafo == 90
            meta.pixelres = meta.pixelres([2,1]);
        end
        fprintf('with rotation  %d\n',slice_info.img_info.trafo);
        fprintf('the pixel resolution is [%f %f]\n',meta.pixelres);
        data.pixelres = meta.pixelres;
        data.shape = size(slice_sample);

        
        json_str = jsonencode(data);
        if ~debug
            fname = [ifolder,'/slice_info.json'];
            fid = fopen(fname,'w');
            fwrite(fid,json_str);
            fclose(fid); 
        end
        pixelres = data.pixelres;
       
        if exist(ofile2,'file') %&& false
            fprintf('WARNING: the file %s exist.\n Delete them first to create new version\n',ofile2);
            fprintf('WARNING: skipping computations');
        else    
            
            
            [img3D_raw,img3D_vis]=stitch3D(ifolder,'threshold',threshold,'pixelres',pixelres,'progress_parm',progress_parm,'element_size_xy',element_size_xy);
            img3D_vis=min(max(img3D_vis,0)*2^16-1,2^16-1);
            img3D_raw=min(max(img3D_raw,0)*2^16-1,2^16-1);
            
            if nargout==0
                fprintf('channel %d\n',channel);
                if channel==1
                    fprintf('saving trafofile %s\n',trafo_file);
                    make_my_nii(img3D_vis,ofile2,varargin{:},'savetrafo',trafo_file);
                    make_my_nii(img3D_raw,ofile1,varargin{:},'loadtrafo',trafo_file);
                else
                    fprintf('using trafofile %s\n',trafo_file);
                    make_my_nii(img3D_vis,ofile2,varargin{:},'loadtrafo',trafo_file);
                    make_my_nii(img3D_raw,ofile1,varargin{:},'loadtrafo',trafo_file);                    
                end
            end
        end

end;

catch ME
    fprintf('an error occured: %s\n',ME.message);
    for s=1:numel(ME.stack)
    fprintf('file: %s\nname: %s\nline: %d\n',ME.stack(s).file,ME.stack(s).name,ME.stack(s).line)
    end;
    if usejava('jvm') && ~feature('ShowFigureWindows')
    exit(1);
    end;
end;


function [img3D_raw,img3D_vis]=stitch3D(ifolder,varargin)
    progress_parm=[0,1];
    for k = 1:2:length(varargin),
            eval(sprintf('%s=varargin{k+1};',varargin{k}));
    end;

    filenames=get_filenames(ifolder);
    
    
    progress_old=-1;
    
    for a=1:numel(filenames)
        fprintf('proccessing slice %d of %d (%s)',a,numel(filenames),filenames{a})
        tic
        img2D=single(imread([ifolder,'/',filenames{a}]));
        fprintf('(imread in %d seconds)',ceil(toc));
        tic
        scales = 1./[element_size_xy./pixelres];
        newshape = round(size(img2D).*scales);
        
        img2D_raw = pipeline_downscale(img2D,newshape,true,'sharp');
     
        img2D(img2D>threshold)=threshold;
        img2D_vis = pipeline_downscale(img2D,newshape,true,'sharp');
        fprintf('(resized in %d seconds)',ceil(toc));
        
        if (a==1)
            shape=[size(img2D_raw),numel(filenames)];
            img3D_vis=zeros(shape,'single');
            img3D_raw=zeros(shape,'single');
            %return
        end
        
        img3D_vis(:,:,a) = img2D_vis./threshold;
        img3D_raw(:,:,a) = img2D_raw/2^16;
        fprintf('\n');
        
        progress=ceil(100*(progress_parm(1)+progress_parm(2)*a/numel(filenames)));
        if progress~=progress_old
            progress_old=progress;
            fprintf('#PROGRESS#%d#\n',progress); 
        end;
        
    end;
    
    

function filenames=get_filenames(ifolder)
    imglist=dir([ifolder,'/*_*_*_1_*_*_.mat']);
    
    filenames={};
    
    for a=1:numel(imglist)
        
        sinfo=strsplit(imglist(a).name,'_');
        zres=str2num(sinfo{end-1});
        cuting_layer=str2num(sinfo{end-3});
        img_name=[sinfo{1},'.png'];
        if (cuting_layer~=1)
            fprintf('not a cuting_layer!\n');
            assert(cuting_layer==1);
        end;
        
            if (zres~=50)
                fprintf('zres~=50!\n');
                assert(zres==50);
            end;
            filenames{numel(filenames)+1}=img_name;
        %end;
    end;
    
    

