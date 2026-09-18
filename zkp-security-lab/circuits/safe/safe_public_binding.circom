pragma circom 2.0.0;

template SafePublicBinding() {
    signal input x;
    signal input claimed;
    signal computed;

    computed <== x * x;
    claimed === computed;
}

component main = SafePublicBinding();