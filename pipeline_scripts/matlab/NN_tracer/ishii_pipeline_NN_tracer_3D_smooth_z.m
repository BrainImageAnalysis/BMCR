function ishii_pipeline_NN_tracer_3D_smooth_z(mid,varargin)


pid = feature('getpid');
fprintf('MATLAB PID: %d\n',pid);

[pathstr, name, ext]=fileparts([mfilename('fullpath'),'.m']);
addpath(pathstr);
addpath([pathstr,'/../nifti_tool/']);

threshold = 0.75;

channel=1;
progress_parm=[0,1];
  
meso_global_common

weighted_img = false;
weighted2_img = false;

addpath(pipescipts);

foldername='NN_tracer';

for k = 1:2:length(varargin),
            eval(sprintf('%s=varargin{k+1};',varargin{k}));
end

try 
    
ofolder=[dbfolder,'/',mid,'/','/tissuecyte/3d/',foldername,'/'];
files = {'NN_tracer_2020_masked.nii.gz',...
    'NN_tracer_2020.nii.gz',...
    'NN_tracer_weighted_2020_masked.nii.gz',...
    'NN_tracer_weighted_2020.nii.gz',...
    'NN_tracer_weighted_C2_2020_masked.nii.gz',...
    'NN_tracer_weighted_C2_2020.nii.gz'};        

for i = 1:numel(files)
    f = [ofolder,files{i}];
    fprintf('processing %s\n',f);
    img = load_untouch_nii(f);
    assert(strcmp(class(img.img),'single'));
    img.img = smooth_tracer_3D(img.img);
    save_untouch_nii(img,strrep(f,'.nii.gz','_smoothz.nii.gz'));
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
