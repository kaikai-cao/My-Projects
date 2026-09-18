pragma circom 2.0.0;

template AmbiguousDomain() {
    signal input x;
    signal input bound;
    signal output y;

    y <== x * x + bound;
}

component main = AmbiguousDomain();