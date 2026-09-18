pragma circom 2.0.0;

template OverRangeCheck() {
    signal input x;
    signal output y;
    signal x0;
    signal x1;

    x0 <-- x & 1;
    x1 <-- x >> 1;

    x0 * (x0 - 1) === 0;
    x1 * (x1 - 1) === 0;
    x === x0 + 2 * x1;
    x0 === 1;
    y <== x * x;
}

component main = OverRangeCheck();