pragma circom 2.0.0;

template OverEquality() {
    signal input a;
    signal input b;
    signal input c;
    signal result;

    result <== a + b - c;
    result === 0;
}

component main = OverEquality();