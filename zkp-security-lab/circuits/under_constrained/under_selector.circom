pragma circom 2.0.0;

template UnderSelector() {
    signal input sel;
    signal input a;
    signal input b;
    signal output out;

    out <== sel * a + (1 - sel) * b;
}

component main = UnderSelector();