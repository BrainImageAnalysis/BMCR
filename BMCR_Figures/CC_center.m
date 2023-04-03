function center = CC_center(CC,shape)
    [X,Y] = ind2sub(shape,CC);
    center = [mean(X),mean(Y)];