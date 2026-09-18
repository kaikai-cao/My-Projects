pragma circom 2.0.0;

template AmbiguousDeadVar() {
    signal input x;
    signal output y;
    signal dead;

    dead <-- x + 1;
    y <== x * x;
}

component main = AmbiguousDeadVar();