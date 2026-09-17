pragma circom 2.1.9;

template UnsafeSquare() {
    signal input x;
    signal output y;
    y <-- x * x;
}

component main = UnsafeSquare();