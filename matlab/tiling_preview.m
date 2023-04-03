function tiling_preview(preview_name,fix_nifti,moved_nifti, res)

try 
  %%
[pathstr, name, ext]=fileparts([mfilename('fullpath'),'.m']);
addpath(pathstr);
addpath([pathstr,'/nifti_tool/']);

imgA = double(preview_nifti(fix_nifti));
imgB = double(preview_nifti(moved_nifti));


imgA = (imgA - min(imgA(:)))/(max(imgA(:)) - min(imgA(:)));
imgB = (imgB - min(imgB(:)))/(max(imgB(:)) - min(imgB(:)));

t1 = imgA;
t2 = imgB;

t1 = imadjust(t1);
t2 = imadjust(t2);

RGB=pipe_checkerboard(t1,t2,res);

CB = rgb2gray(RGB);

imwrite(CB,strcat(preview_name,'normal.png'));

%imwrite(imresize(CB,0.25,'bicubic'),strcat(preview_name,'small.jpg'));
imwrite(imresize(RGB,0.25,'bicubic'),strcat(preview_name,'small.jpg'));

shape=size(CB);
shape=shape(1:2);
newshape=shape./max(shape);
new_shape=ceil([60,60].*newshape);

%imwrite(imresize(CB,new_shape,'bicubic'),strcat(preview_name,'tiny.jpg'));
imwrite(imresize(RGB,new_shape,'bicubic'),strcat(preview_name,'tiny.jpg'));

imwrite(RGB,strcat(preview_name,'color.jpg'));

catch ME
    fprintf('an error occured: %s\n',ME.message);
    for s=1:numel(ME.stack)
    fprintf('file: %s\nname: %s\nline: %d\n',ME.stack(s).file,ME.stack(s).name,ME.stack(s).line)
    end;
    if usejava('jvm') && ~feature('ShowFigureWindows')
    exit(1);
    end;

end
