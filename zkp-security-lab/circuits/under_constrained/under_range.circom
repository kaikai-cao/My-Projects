pragma circom 2.0.0;

template UnderRange() {
    signal input x;
    signal output y;

    y <== x * x;
}

component main = UnderRange();