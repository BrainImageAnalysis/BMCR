function R = CC_eig(CC,t)
    [V,D] = eig(CC'*CC);
    if t == 'V'
        R = V;
    else
        R = D;
    end