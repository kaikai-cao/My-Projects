pragma circom 2.0.0;

template TmpUnconstrained() {
    signal input a;
    signal input b;
    signal input c;
    signal output out;
    signal tmp;

    tmp <-- a * b;
    out <== tmp + c;
}

component main = TmpUnconstrained();