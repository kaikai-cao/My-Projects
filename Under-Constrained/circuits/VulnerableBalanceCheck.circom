pragma circom 2.0.0;

template VulnerableBalanceCheck() {
    signal input currentBalance;
    signal input withdrawAmount;
    signal output newBalance;

    // 仅保留算术计算，没有范围检查和比较约束
    newBalance <== currentBalance - withdrawAmount;
}

component main = VulnerableBalanceCheck();