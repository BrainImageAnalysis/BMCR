function img=unet_enlarge_region(img,radius,varargin)  
pad=false;


element_size=[1,1,1];

for k = 1:2:length(varargin),
        eval(sprintf('%s=varargin{k+1};',varargin{k}));
end;
classname=class(img);




if pad
    shape=size(img);
    img=padarray(img,ceil(2*radius+1),'symmetric','post');
end;



imgsz = size(img);
dim=numel(imgsz);

switch dim
    case 2
    [X Y] = ndgrid(0:(imgsz(1)-1),0:(imgsz(2)-1));
    X = X - ceil(imgsz(1)/2);
    Y = Y - ceil(imgsz(2)/2);
    R2 = cast(X.^2/element_size(1)^2 + Y.^2/element_size(2)^2, classname);
    case 3
    [X Y Z] = ndgrid(0:(imgsz(1)-1),0:(imgsz(2)-1),0:(imgsz(3)-1));
    X = X - ceil(imgsz(1)/2);
    Y = Y - ceil(imgsz(2)/2);
    Z = Z - ceil(imgsz(3)/2);
    R2 = cast(X.^2*element_size(1)^2 + Y.^2*element_size(2)^2 + Z.^2*element_size(3)^2,classname);
end;
clear X Y Z;

tmp = single(R2 < (radius*radius+0.25) );
%tmp = tmp / sum(tmp(:));
gaussin = (fftshift( tmp ));
gaussin_ft= fftn(gaussin);
clear gaussin;

img=ifftn(fftn(img).*gaussin_ft,'symmetric');    
    
if  pad
    if numel(size(img))==3
        img=img(1:shape(1),1:shape(2),1:shape(3));
    else
        img=img(1:shape(1),1:shape(2));
    end;
end;

img = single(img>0.5);



