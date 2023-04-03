function center = CC_ind2sub(CC,shape,com)
    [X,Y] = ind2sub(shape,CC);
    center = cat(2,X,Y);
    if com 
        c = repmat(mean(center,1),size(X,1),1);
        center = center - c;
    end