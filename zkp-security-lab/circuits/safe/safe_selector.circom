pragma circom 2.0.0;

template SafeSelector() {
    signal input sel;
    signal input a;
    signal input b;
    signal output out;

    sel * (sel - 1) === 0;
    out <== sel * a + (1 - sel) * b;
}

component main = SafeSelector();