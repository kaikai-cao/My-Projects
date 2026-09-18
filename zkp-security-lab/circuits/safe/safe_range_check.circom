pragma circom 2.0.0;

template SafeRangeCheck() {
    signal input x;
    signal output y;
    signal b0;
    signal b1;

    b0 <-- x & 1;
    b1 <-- x >> 1;

    b0 * (b0 - 1) === 0;
    b1 * (b1 - 1) === 0;
    x === b0 + 2 * b1;
    y <== x * x;
}

component main = SafeRangeCheck();