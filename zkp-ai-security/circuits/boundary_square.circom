pragma circom 2.1.9;

template BoundarySquare() {
    signal input x;
    signal output y;
    signal intermediate z;

    z <-- x * x;
    y <== z + 1;
}

component main = BoundarySquare();