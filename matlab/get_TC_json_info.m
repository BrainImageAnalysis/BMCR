function meta = get_TC_json_info(db_root, meta)



fname = [db_root,'/meta/TC_info.json'];
fprintf('looking for meta file : %s\n',fname);

if exist(fname,'file')
   fprintf('found a valid, unique json file\n');
   
   fid = fopen(fname);
   raw = fread(fid,inf);
   str = char(raw');
   fclose(fid); 
   json = jsondecode(str);
   meta.TissueCyte = 1000;
   if isfield(json,'ApparatusInfo')
   if isfield(json.ApparatusInfo,'TissueCyte_')
       fprintf('tissuecyte string is %s\n',json.ApparatusInfo.TissueCyte_);
       switch json.ApparatusInfo.TissueCyte_
           case  'TissueCyte1100'
                meta.TissueCyte = 1100;
           case  'TissueCyte1000'
                meta.TissueCyte = 1000;
       end
       fprintf('setting tissuecyte to %d\n',meta.TissueCyte);
   end
   fprintf('ApparatusInfo is missing in meta file');
   end
   
   if isfield(json.Mosaic,'xres_') && isfield(json.Mosaic,'yres_')
       fprintf('overriding pixel res from : %f %f\n',meta.pixelres);
       %meta.pixelres = [json.Mosaic.xres_,json.Mosaic.yres_];
       meta.pixelres = [json.Mosaic.yres_,json.Mosaic.xres_];
       fprintf('overriding pixel res to   : %f %f\n',meta.pixelres);
   end
   %if isfield(json.Mosaic,'Xres_') && isfield(json.Mosaic,'Yres_')
   %    fprintf('overriding pixel res from : %f %f\n',meta.pixelres);
   %    meta.pixelres = [json.Mosaic.Xres_,json.Mosaic.Yres_];
   %    fprintf('overriding pixel res to   : %f %f\n',meta.pixelres);
   %end
   if isfield(json,'StitchingInfo')
       fprintf('overriding cropping boundaries from : %d %d %d %d\n',meta.crop);
       %meta.crop = [...
       %    json.StitchingInfo.CroppingXLeft_pixel__,...
       %    json.StitchingInfo.CroppingXRight_pixel__,...
       %    json.StitchingInfo.CroppingYTop_pixel__,...
       %    json.StitchingInfo.CroppingYBottom_pixel__,...
        %   ];
      meta.crop = [...
           json.StitchingInfo.CroppingYTop_pixel__,...
           json.StitchingInfo.CroppingYBottom_pixel__,...
           json.StitchingInfo.CroppingXLeft_pixel__,...
           json.StitchingInfo.CroppingXRight_pixel__,...
           ];
      fprintf('overriding cropping boundaries to   : %d %d %d %d\n',meta.crop);
   end
else
    fprintf('did not find a valid, unique json file, using TC1000 defaults\n');
end
display(meta);

assert(meta.TissueCyte == 1000)
%meta.pixelres = [1.4,1.5];
