%%
npts = 32;
bdir = randn(3,npts);
figure(1);
max_iter = 10000;
for b = 1:max_iter
    bdir = bdir./sqrt(repmat(sum(bdir.^2,1),3,1));
    alpha = 0.01;
    bdir_new = bdir;
    bdir_2 = cat(2,bdir,-bdir);
    bdir_2_ = bdir_2;
    bdir_2_(1,:) = - bdir_2_(1,:);
    bdir_2 = cat(2,bdir_2,bdir_2_);
    
    for a = 1:size(bdir,2)
        %%
        bdir_ = bdir_2(:,a);
        bdir_ = repmat(bdir_,1,4*npts);
        d = (bdir_2 - bdir_);
        d(:,a) = [];
        dn = 1./(sum(d.^2,1)+eps);    
        d = sum(d.*repmat(dn,3,1),2);
        bdir_new(:,a) = bdir_new(:,a) - alpha * d;    
    end
    bdir = bdir_new;
    if mod(b,50) == 0 || max_iter == b
        clf
        hold on
        plot3(bdir(1,:),bdir(2,:),bdir(3,:),'*');
        plot3(-bdir(1,:),-bdir(2,:),-bdir(3,:),'r*');
        bdir_ = bdir;
        bdir_(1,:) = -bdir_(1,:); 
        plot3(bdir_(1,:),bdir_(2,:),bdir_(3,:),'g*');
        plot3(-bdir_(1,:),-bdir_(2,:),-bdir_(3,:),'g*');
        axis equal
        drawnow
    end
end
%%
Nx = repmat([1,0,0]',1,npts);
Nz = repmat([0,0,1]',1,npts);
bdir_r = bdir;
flipme = dot(bdir_r,Nz)<0;
bdir_r(:,flipme) = -bdir_r(:,flipme);
flipme = dot(bdir_r,Nx)<0;
bdir_r(1,flipme) = -bdir_r(1,flipme);


clf
hold on
plot3(bdir_r(1,:),bdir_r(2,:),bdir_r(3,:),'*');
bdir_ = bdir_r;
bdir_(1,:) = -bdir_(1,:); 
plot3(bdir_(1,:),bdir_(2,:),bdir_(3,:),'r*');
bdir_final = cat(2,bdir_,bdir_r);
plot3(-bdir_final(1,:),-bdir_final(2,:),-bdir_final(3,:),'g*');
axis equal
%%
bdir_yz = bdir_r;
bdir_yz(2:3,:) = -bdir_yz(2:3,:);
bdir_out = cat(2,bdir_r,bdir_yz);


clf
hold on
plot3(bdir_out(1,:),bdir_out(2,:),bdir_out(3,:),'*');
plot3(-bdir_out(1,:),-bdir_out(2,:),-bdir_out(3,:),'r*');
axis equal
%%
save(['bvec_sym4_',num2str(size(bdir_out,2)),'.mat'],'bdir_out')




