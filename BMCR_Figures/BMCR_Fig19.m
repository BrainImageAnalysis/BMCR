%%

mapping = 'BMA';

BMCR_data='/disk/skibbe/nextcloud/BIA/Henrik/Marmonet/BMCR_tracer/';

base = [BMCR_data,'/auxiliary_data/flatmap_stack_mapping_data/'];

surface_d = load_untouch_nii([base,'results/',mapping,'/debug05_layers_discrete.nii.gz']);
surface = load_untouch_nii([base,'results/',mapping,'/debug04_equidistant_layers_continous.nii.gz']);

indx = load_untouch_nii([base,'results/',mapping,'/fm_stack_index_1000_TC_std.nii.gz']);
%%

odir = './BMCR_Figures/Fig19/';
mkdir(odir);

%%
shape3 = size(surface.img);
mask_seeds = zeros(shape3);
ind = indx.img(:,:,:);
stack_shape = size(indx.img);
[X_,Y_,Z_] = ndgrid(1:stack_shape(1),1:stack_shape(2),1:stack_shape(3));
sdist = 25;
sdist = 50;
%sdist = 40;
indm = (mod(X_,sdist)==0) &(mod(Y_,sdist)==0) & (ind>0);
mask_seeds(ind(indm(:))) = 1;

seed_img2D = zeros(stack_shape);
seed_img2D(~(ind>0)) = -1;
seed_img2D(indm) = 1;


figure(3);
imagesc(squeeze(max(seed_img2D,[],3)));

%%
depth = [5,25,45];


for ddd = 1:numel(depth)
    drawnow
    dddd = depth(ddd);

    pf = ['_',num2str(dddd)];
    
    ddddn = ceil(10*dddd/50);
    mask = (single(abs(surface.img-(ddddn+1))<0.5).*(abs(single(surface_d.img)-(ddddn+1))<2));

    mask(end/2+1:end,:,:)=0;
    mask4 = ((mask));
    mask4s = imdilate(mask_seeds,strel('sphere',2));

    bg = surface_d.img>0;
    start_VIannotator({max(mask4,0.5*bg),mask4s.*mask4,mask4});

    seeds = mask4s.*mask4;
    CC = bwconncomp(seeds>0.5);
    seeds_single = zeros(size(seeds));
    indx = cellfun(@(x)x(1),CC.PixelIdxList);
    seeds_single(indx(:)) = 1;

    spimg = bwdist(seeds_single);
    current_s = spimg;
    mask2_s = single(mask4);
    %%
    
    current_sRGB = max(cat(4,mask2_s,mask2_s,mask2_s),0);

    current_sRGB_full = zeros(size(current_sRGB));
    r = [5,10,15];
    mA = (current_s<r(1));
    mB = ((current_s<r(2))&(current_s>=r(1)));
    mC = ((current_s<r(3))&(current_s>=r(2)));
    
    current_sRGB(:,:,:,1) = mask2_s&(~mA);
    current_sRGB(:,:,:,2) = mask2_s&(~mC);
    current_sRGB(:,:,:,3) = mask2_s&(~mB);


    hide = (mA|mB|mC);
    current_sRGB_full(:,:,:,1) = (~mA).*hide;
    current_sRGB_full(:,:,:,2) = (~mC).*hide;
    current_sRGB_full(:,:,:,3) = (~mB).*hide;
    current_sRGB_full = (current_sRGB_full *255/max(current_sRGB_full(:)));

    current_sRGB = uint8(current_sRGB *255/max(current_sRGB(:)));
    start_VIannotator({squeeze(current_sRGB(:,:,:,1)),squeeze(current_sRGB(:,:,:,2)),squeeze(current_sRGB(:,:,:,3))});


    if true
        ref = surface;
        ref.img = current_sRGB;
        ref.hdr.dime.datatype = 128;
        ref.hdr.dime.bitpix = 8;
        save_untouch_nii(ref,[odir,'/sphere_STPT',pf,'.nii.gz']);
    end

    %%
  
    stack = zeros(stack_shape);
    stack_full = zeros(stack_shape);
    stackRGB = zeros([stack_shape,3]);
    stackRGB_full = zeros([stack_shape,3]);

    current_sRGB_full_ = current_sRGB_full;


    for a = 1:3
        tmp = current_sRGB(:,:,:,a);
        stack(ind(:)>0) = tmp(ind(ind(:)>0));
        stackRGB(:,:,:,a) = stack;

        tmp = current_sRGB_full(:,:,:,a);
        stack_full(ind(:)>0) = tmp(ind(ind(:)>0));
        stackRGB_full(:,:,:,a) = stack_full;
    end

    figure(1);
    %img2D = squeeze(max(stackRGB,[],3));
    img2D = squeeze(max(stackRGB(:,:,dddd,:),[],3));
    img2D_save = fliplr(imrotate(img2D,90));
    imshow(img2D_save);
    axis equal
    imwrite(img2D_save,[odir,'/sphere_2D_mid',pf,'.png'])

    figure(2);
    img2Df = squeeze(max(stackRGB_full(:,:,dddd,:),[],3));
    img2Df_save = fliplr(imrotate(img2Df,90));
    imshow(img2Df_save);
    axis equal
    imwrite(img2D_save,[odir,'/sphere_2D_mid_2',pf,'.png'])
    %%
    nii = make_nii(stackRGB);
    nii.hdr.dime.datatype = 128;
    nii.hdr.dime.bitpix = 8;
    save_nii(nii,[odir,'/sphere_stack',pf,'.nii.gz']);
    
    %%
    nii = make_nii(stackRGB_full);
    nii.hdr.dime.datatype = 128;
    nii.hdr.dime.bitpix = 8;
    save_nii(nii,[odir,'/sphere_stack_full',pf,'.nii.gz']);
    %%
    s2D = zeros(stack_shape);
    s2D(indm) = 1;
    s2D = single(((squeeze(max(s2D,[],3)))));
    R = squeeze(img2D(:,:,1)>0);
    G = squeeze(img2D(:,:,2)>0);
    B = squeeze(img2D(:,:,3)>0);

    centers = single((~R)&(G)&(B));
    mid = single((R)&(G)&(~B));

    CC = bwconncomp(centers);
    tmp_c = cellfun(@(x)CC_center(x,size(R)),CC.PixelIdxList,'UniformOutput',false);
    tmp_x = round(cellfun(@(x)x(1),tmp_c));
    tmp_y = round(cellfun(@(x)x(2),tmp_c));
    centers2_xy = cat(2,tmp_x,tmp_y);
    centers2_ind = sub2ind(size(R),tmp_x,tmp_y);
    
    com = zeros(size(R));
    com(centers2_ind) = 1;
    figure(3);
    imagesc(mid+2*com);


    Cl = bwlabeln(mid);
    D = distmat(Cl(centers2_ind)',Cl(centers2_ind)');
    excludeM = (D<eps) &(~eye(size(D,1)));
    exclude = (max(excludeM,[],1))>0.5;


    CC = bwconncomp(mid|centers);
    tmp_n = cellfun(@(x)CC_ind2sub(x,size(R),true),CC.PixelIdxList,'UniformOutput',false);
    tmp_cc = cellfun(@(x)CC_center(x,size(R)),CC.PixelIdxList,'UniformOutput',false);


    
    valid_spheres = cellfun(@(x)numel(x),tmp_n)>100;

    tmp_eig_d = cellfun(@(x)CC_eig(x,'D'),tmp_n,'UniformOutput',false);
    tmp_eig_v = cellfun(@(x)CC_eig(x,'V'),tmp_n,'UniformOutput',false);
    a_eig_d = cat(3,tmp_eig_d{:});
    a_eig_v = cat(3,tmp_eig_v{:});
    a_cc = squeeze(cat(3,tmp_cc{:}));

    f = figure('units','inch','position',[0,0,10,10]);

    clf
    hold on
    imagesc(mid+2*com);
    s = 0.5;
    v = 1;
    sc = squeeze(a_eig_d(v,v,valid_spheres))';
    sc = sc./(squeeze(a_eig_d(2,2,valid_spheres))'+eps);
    quiver(a_cc(2,valid_spheres),a_cc(1,valid_spheres),...
           sc.*squeeze(a_eig_v(v,2,valid_spheres))',...
           sc.*squeeze(a_eig_v(v,1,valid_spheres))',...
           s,...
           'g');
    v = 2;
    sc = squeeze(a_eig_d(v,v,valid_spheres))';
    sc(:) = 1;
    quiver(a_cc(2,valid_spheres),a_cc(1,valid_spheres),...
           sc.*squeeze(a_eig_v(v,2,valid_spheres))',...
           sc.*squeeze(a_eig_v(v,1,valid_spheres))',...
           s,...
           'r');

    axis([0,1000,0,1000]);
    set(gca,'position',[0 0 1 1],'units','normalized')

    fig = gcf;
    Sf=getframe(fig);
    [X,map]=frame2im(Sf);
    close(f)
    X = (imrotate(X,90));
    imwrite(X,[odir,'/eig_vec',pf,'.png']);
    figure(3); 
    imshow(X)
    %%

    f = figure('units','inch','position',[0,0,5,5]);
    histogram(squeeze(a_eig_d(1,1,:)./(a_eig_d(2,2,:))+eps), 'Normalization','probability')
   
    xlabel('isotropy');
    ylabel('percentage');
    axis([0 1 0 0.25])
    [X,map]=frame2im(getframe(gcf));
    
    close(f);
    figure(4);
    imshow(X)
    
    imwrite(X,[odir,'/hist',pf,'.png']);
    %%
    f = figure('units','inch','position',[0,0,10,10]);
  
    clf
    hold on
  
    valid = squeeze(ind(:,:,25)>0);
    imagesc(valid);
    colormap(gray);
   
    axis([0,1000,0,1000]);
  
    v = 1;
    sc = squeeze(a_eig_d(v,v,valid_spheres))';
    sc = sc./(squeeze(a_eig_d(2,2,valid_spheres))'+eps);

    px = a_cc(2,valid_spheres);
    py = a_cc(1,valid_spheres);
    r = sc*15;
    alpha=-pi:0.01:pi;
    x=cos(alpha);
    y=sin(alpha);
    cmap = hot(100);
    for ii=1:numel(r)
      fill((r(ii)*x+px(ii)),(r(ii)*y+py(ii)),cmap(ceil(sc(ii)*100),:),'linewidth',2)
      hold on
    end

    set(gca,'position',[0 0 1 1],'units','normalized')
    

    fig = gcf;
    Sf=getframe(fig);
    [X,map]=frame2im(Sf);
    close(f)
    X = (imrotate(X,90));
    figure(15); 
    imshow(X)
    imwrite(X,[odir,'/anisotropy_circles',pf,'.png']);
    drawnow
end