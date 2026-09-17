pragma circom 2.1.9;

template SafeSquare() {
    signal input x;
    signal output y;
    y <== x * x;
}

component main = SafeSquare();