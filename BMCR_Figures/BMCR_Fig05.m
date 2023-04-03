%%
BMCR_data='/disk/skibbe/nextcloud/BIA/Henrik/Marmonet/BMCR_tracer/BMCR_img_data/';

%%
% tracer data with overlapping injections sites in A8aV
data_A8aV_fn = ...
{'A8aV-R01_0029-TT22',...
'A8aV-R01_0030-TT23',...
'A8aV-R01_0033-TT25',...
'A8aV-R01_0034-TT26',...
'A8aV-R01_0039-TT27',...
'A8aV-R01_0040-TT28',...
'A8aV-R01_0056-TT35',...
'A8aV-R01_0057-TT36',...
'A8aV-R01_0063-TT42',...
'A8aV-R01_0064-TT43',...
'A8aV-R01_0070-TT45',...
'A8aV-R01_0075-TT46',...
'A8aV-R01_0076-TT49',...
'A8aV-R01_0091-TT63',...
'A8aV-R01_0101-TT71'};
%%


for a = 1:numel(data_A8aV_fn)
    fn = [BMCR_data,'/',data_A8aV_fn{a},'/3D_stacks/anterograde_tracer_signal_normalized.nii.gz'];
    img = load_untouch_nii(fn);
    fn = [BMCR_data,'/',data_A8aV_fn{a},'/3D_stacks/streamline_density.nii.gz'];
    img_sl = load_untouch_nii(fn);
    fn = [BMCR_data,'/',data_A8aV_fn{a},'/3D_stacks/anterograde_cell_density.nii.gz'];
    img_cl = load_untouch_nii(fn);
    if a == 1
        shape = size(img.img);
        data_A8aV_stack = zeros(shape,'single');
        data_A8aV_stack_sl = zeros(shape,'single');
        data_A8aV_stack_c = zeros(shape,'single');
    end
    data_A8aV_stack = max(data_A8aV_stack,single(img.img));
    data_A8aV_stack_sl = max(data_A8aV_stack_sl,single(img_sl.img));
    data_A8aV_stack_c = data_A8aV_stack_c + single(img_cl.img>0);
end
%%
% tracer data with overlapping injections sites in A32 
data_A32_fn = ...
{'A32-R01_0072-TT50',...
'A32-R01_0095-TT69'};

for a = 1:numel(data_A32_fn)
    fn = [BMCR_data,'/',data_A32_fn{a},'/3D_stacks/anterograde_tracer_signal_normalized.nii.gz'];
    img = load_untouch_nii(fn);
    fn = [BMCR_data,'/',data_A32_fn{a},'/3D_stacks/streamline_density.nii.gz'];
    img_sl = load_untouch_nii(fn);
    fn = [BMCR_data,'/',data_A32_fn{a},'/3D_stacks/anterograde_cell_density.nii.gz'];
    img_cl = load_untouch_nii(fn);
    if a == 1
        shape = size(img.img);
        data_A32_stack = zeros(shape,'single');
        data_A32_stack_sl = zeros(shape,'single');
        data_A32_stack_c = zeros(shape,'single');
    end
    data_A32_stack = max(data_A32_stack,single(img.img));
    data_A32_stack_sl = max(data_A32_stack_sl,single(img_sl.img));
    data_A32_stack_c = data_A32_stack_c + single(img_cl.img>0);
    
end
%%

% 3D image stacks for tracer density
img_R = squeeze(data_A32_stack/2^16).^0.5;
img_G = squeeze(data_A8aV_stack/2^16).^0.5;

% 3D image stacks for streamline density
img_R_sl = squeeze(data_A32_stack_sl/2^16).^0.5;
img_G_sl = squeeze(data_A8aV_stack_sl/2^16).^0.5;

%%
% Save them as nifti or use a matlab section viewer visulize the data
% Two examples below:
%%
of = 260;
r = 5;
imgRGB_tr = cat(3,squeeze(max(img_R(:,:,of:of+r),[],3)),...
               squeeze(max(img_G(:,:,of:of+r),[],3)),...
               squeeze(max(img_R(:,:,of:of+r),[],3)));
imgRGB_sl = cat(3,squeeze(max(img_R_sl(:,:,of:of+r),[],3)),...
               squeeze(max(img_G_sl(:,:,of:of+r),[],3)),...
               squeeze(max(img_R(:,:,of:of+r),[],3)));           
imgRGB = cat(1,imgRGB_sl,imgRGB_tr);
imgRGB(:,:,3) = 0;
figure(1);imagesc(fliplr(imrotate(imgRGB,90)));
%%

of = 590;
r = 15;
imgRGB_tr = cat(3,squeeze(max(img_R(:,of:of+r,:),[],2)),...
               squeeze(max(img_G(:,of:of+r,:),[],2)),...
               squeeze(max(img_R(:,of:of+r,:),[],2)));
imgRGB_sl = cat(3,squeeze(max(img_R_sl(:,of:of+r,:),[],2)),...
               squeeze(max(img_G_sl(:,of:of+r,:),[],2)),...
               squeeze(max(img_R(:,of:of+r,:),[],2)));           
imgRGB = cat(1,imgRGB_sl,imgRGB_tr);
imgRGB(:,:,3) = 0;
figure(2);imagesc(fliplr(imrotate(imgRGB,90)));

