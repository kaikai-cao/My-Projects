# Circom Day 3 Lab：第一个电路与约束不足实验

## 环境要求
- Circom 2.x
- Node.js v18+
- snarkjs 0.7+

## 快速开始

### 1. 编译正确电路
```bash
circom circuits/square.circom --r1cs --wasm --sym -o build
snarkjs r1cs info build/square.r1cs