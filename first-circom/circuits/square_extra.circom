pragma circom 2.0.0;

template Square()
{
    signal input x;
    signal output y;
    signal output z;

    y <== x*x;
    z <== x+x;
}

component main = Square();