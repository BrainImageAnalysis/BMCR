function pipeline_nn_cell(mid,ofolder)

try 
    
    
    [pathstr, name, ext]=fileparts([mfilename('fullpath'),'.m']);
    addpath(pathstr);
    addpath([pathstr,'/nifti_tool/']);
    nn_tools = pathstr;
    addpath(nn_tools)
    
    tmp_fd = ['/disk/k_raid/KAKUSHIN-NOU-DATA/tmp/',mid,'/CELLS/'];
    mkdir(tmp_fd);
    
    
                

    %%
    



    folder = ['/disk/k_raid/KAKUSHIN-NOU-DATA/database/',mid,'/tissuecyte/'];

    fprintf('ofolder: %s\n',ofolder);


    %ifile = [folder,'/3d/inj/inj_mask.nii.gz'];
    ifile = [folder,'/3d/inj/inj_mask_TC_org.nii.gz'];
    slicesC3_ = dir([folder,'/slice/c3/*_1_*']);


    img_ni = load_untouch_nii(ifile);
    img_ni  = single(img_ni.img);
    %img_ni = unet_enlarge_region(img_ni,20,'element_size',[1,1,1]);
	img_ni = unet_enlarge_region(img_ni,40,'element_size',[1,1,1]);

    
    for a = [1:1:size(img_ni,3)]%[1,67]%[1:1:size(img_ni,3)]%[1,67]%
        mask_s = squeeze(img_ni(:,:,a));
        num_samples = sum(mask_s(:));
        
        cds = [];
        if a==1
            tmp=strsplit(slicesC3_(a).name,'_');
            fn = [folder,'/slice/c3/',tmp{1},'.png'];
            slicesC3 = imread(fn);
            full_shape = size(slicesC3);
            ofile = [ofolder,'/shape.csv'];
            csvwrite(ofile,full_shape);
            %return
        end
        
        %http://localhost:8080?x=-16083.706826789092&y=-4978.8405873122065&s=1.2122785219175556&filter=tracer1&label1=CELLS&label2=none&gamma=0.5&mask=0&grid=-1&C01l=0&C01u=0.15&C03l=0&C03u=1&la1=0.5&la2=0.5&slice=169&mid=R01_0083_CM1352F
        
        if (num_samples  > 0)
                %%
                tmp = [tmp_fd,mid,'_',num2str(a),'_cell.png'];
                tmp2 = [tmp_fd,mid,'_',num2str(a),'_cell_pred.png'];
                
                
                
                img_gt = (imresize(single(mask_s),full_shape,'nearest')) > 0.5;
                [X,Y]=ndgrid(1:full_shape(1),1:full_shape(2));
                bounds = [max(min(X(img_gt(:))),1), min(max(X(img_gt(:))),full_shape(1)),...
                          max(min(Y(img_gt(:))),1), min(max(Y(img_gt(:))),full_shape(2))];
                if true
                %if false
                    if exist(tmp,'file')
                        rm_cmd = ['rm ',tmp,' ',tmp2 ];
                        fprintf('%s\n',rm_cmd);
                        [status,result] = system(rm_cmd);
                    end
                    
                    tmp_=strsplit(slicesC3_(a).name,'_');
                    fn = [folder,'/slice/c3/',tmp_{1},'.png'];
                    slicesC3 = imread(fn);

                    %full_shape = size(slicesC3);



                    

                    %tmp = ['/tmp/',mid,'_cell.png'];


                    data = slicesC3(bounds(1):bounds(2),bounds(3):bounds(4));
                    fprintf('writing tempfile to %s\n',tmp);
                    imwrite(data,tmp);
                    %cmd = ['source ~/.bashrc;',nn_tools,'pipeline_nn_cell_apply.sh ',tmp,' ',tmp2 ];
                    cmd = [nn_tools,'pipeline_nn_cell_apply.sh ',tmp,' ',tmp2 ];
                    fprintf('%s\n',cmd);
                    [status,result] = system(cmd);
                    if (status~=0)
                       fprintf('%s\n',result);
                       assert(status==0);
                    end
                end
                
                distance_threshold = 5;
                img_in = single(imread(tmp2));
                %cds = [];
                for thresh = [15:-1:0]%[0:1:10] %[0.1:0.1:0.9]
                    thresh_f = 0.25 + 0.05*thresh;
                    fprintf('threshold %f\n',thresh_f);
                    img = img_in >= thresh_f * 2^8;
                    CC=bwconncomp(img);
                    numPixels = cellfun(@numel,CC.PixelIdxList);
                    detections = zeros(size(img));
                    detections([CC.PixelIdxList{numPixels==1}]) = 1;
                    pixel_groups = {CC.PixelIdxList{numPixels>1}};
                    %max_size = 100;
                    max_size = 200;
                    for p = 1:numel(pixel_groups)

                        [X,Y]=ind2sub(CC.ImageSize,pixel_groups{p});
                        confidence = single(img_in(pixel_groups{p}));
                        confidence = confidence ./ sum(confidence);
                        if numel(X) <= max_size
                            %center=sub2ind(CC.ImageSize,round(mean(X)),round(mean(Y)));
                            center=sub2ind(CC.ImageSize,round(sum(X.*confidence)),round(sum(Y.*confidence)));
                            detections(center) = 1;
                        end
                        
                    end
                    img = detections;

					%scores =img_in(img(:)>0)/2^8;

                    img_ = zeros(full_shape,'uint16');
                    img_ (bounds(1):bounds(2),bounds(3):bounds(4)) = img;
                    loc = find(img_(:)>0);
                    [I,J] = ind2sub(full_shape,loc);
                    if numel(cds)>0
                        DM=distmat(cds(:,1:2),[I,J]);
                        %valid = (min(DM,[],2)>distance_threshold*distance_threshold);
                        valid = (min(DM,[],2)>distance_threshold*distance_threshold);
                        I = I(valid);
                        J = J(valid);
					%	scores = scores(valid);
                    end
                    
                    cds = [cds; [I,J,ones(size(I))*thresh_f]];
                    %size(I)
                    %size(cds)
					%cds = [cds; [I,J,scores]];
                                        


                    %fprintf('%d %d %d\n',cds);
                    if thresh == 5
                        fprintf('num of detections %d\n',numel(loc));
                        ofile = [ofolder,'/slice',num2str(1000+a-1),'.png'];
                        fprintf('saving image %s\n',ofile);
                        imwrite(img_,ofile);
                    end
                end
                %size(cds)
                ofile = [ofolder,'/slice',num2str(1000+a-1),'.csv'];
                %fprintf('num of detections %d\n',numel(loc));
                fprintf('saving cvs file %s\n',ofile);
                csvwrite(ofile,cds);
                
                progress=ceil(100*a/size(img_ni,3));
                fprintf('#PROGRESS#%d#\n',progress); 
                %return
        else
            img_ = zeros(full_shape,'uint16');
            ofile = [ofolder,'/slice',num2str(1000+a-1),'.png'];
            
            if ~exist('empty_ofile','var')
                empty_ofile  = ofile ;
            
                imwrite(img_,ofile);
            else
               [status,result] = system(['cp ',empty_ofile,' ',ofile]); 
               assert(status==0)
            end
            ofile = [ofolder,'/slice',num2str(1000+a-1),'.csv'];
            
            csvwrite(ofile,cds);
            fprintf('skipping slice %d \n',a);
        end
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



function dmat=distmat(b,a)
  dmat=(-2.*(a*b'))+repmat(sum(a.^2,2),1,size(b,1))+(repmat(sum(b.^2,2)',size(a,1),1));
  dmat(dmat(:)<0)=0;




