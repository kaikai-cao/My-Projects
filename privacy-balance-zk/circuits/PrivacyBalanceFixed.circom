pragma circom 2.0.0;

include "circomlib/circuits/poseidon.circom";
include "circomlib/circuits/bitify.circom";

template MerkleRoot(levels) {
    signal input leaf;
    signal input pathElements[levels];
    signal input pathIndex;
    signal output out;

    // ===== 所有 signal 声明 =====
    signal current[levels + 1];
    signal pathBits[levels];
    signal isRight[levels];
    signal left[levels];
    signal right[levels];
    signal diffLeft[levels];
    signal diffRight[levels];

    // ===== 所有 component 声明 =====
    component pathIndexBits = Num2Bits(levels);
    component hash[levels];

    // ===== 连接 =====
    pathIndexBits.in <== pathIndex;
    for (var i = 0; i < levels; i++) {
        pathBits[i] <== pathIndexBits.out[i];
    }

    current[0] <== leaf;

    for (var i = 0; i < levels; i++) {
        isRight[i] <== pathBits[i];

        // 分步计算 left
        diffLeft[i] <== pathElements[i] - current[i];
        left[i] <== current[i] + isRight[i] * diffLeft[i];

        // 分步计算 right
        diffRight[i] <== current[i] - pathElements[i];
        right[i] <== pathElements[i] + isRight[i] * diffRight[i];

        hash[i] = Poseidon(2);
        hash[i].inputs[0] <== left[i];
        hash[i].inputs[1] <== right[i];

        current[i + 1] <== hash[i].out;
    }

    out <== current[levels];
}

template PrivacyBalanceFixed() {
    signal input root;
    signal input threshold;
    signal input nullifier;
    signal input chainId;
    signal input contractAddress;

    signal input balance;
    signal input salt;
    signal input pubkey;
    signal input pathElements[2];
    signal input pathIndex;
    signal input nullifierPreimage;

    component leafHash = Poseidon(3);
    leafHash.inputs[0] <== balance;
    leafHash.inputs[1] <== salt;
    leafHash.inputs[2] <== pubkey;

    signal leaf;
    leaf <== leafHash.out;

    component merkle = MerkleRoot(2);
    merkle.leaf <== leaf;
    merkle.pathElements[0] <== pathElements[0];
    merkle.pathElements[1] <== pathElements[1];
    merkle.pathIndex <== pathIndex;

    merkle.out === root;

    signal diff;
    diff <== balance - threshold;

    component diffRange = Num2Bits(64);
    diffRange.in <== diff;

    component balanceRange = Num2Bits(64);
    balanceRange.in <== balance;

    component thresholdRange = Num2Bits(64);
    thresholdRange.in <== threshold;

    component nullifierHash = Poseidon(3);
    nullifierHash.inputs[0] <== nullifierPreimage;
    nullifierHash.inputs[1] <== chainId;
    nullifierHash.inputs[2] <== contractAddress;

    signal computedNullifier;
    computedNullifier <== nullifierHash.out;

    computedNullifier === nullifier;
}

component main {public [root, threshold, nullifier, chainId, contractAddress]} = PrivacyBalanceFixed();