pragma circom 2.0.0;

template UnboundPublic() {
    signal input x;
    signal input claimed_sum;
    signal output y;

    y <== x * x;
}

component main = UnboundPublic();