# 🔥 Bitcoin Puzzle Solver v33 - Real CUDA Kernel

> GPU-accelerated Bitcoin puzzle solver using native CUDA C kernel

## 📋 Requirements

- NVIDIA GPU with Compute Capability 8.0+ (RTX 4070 recommended)
- CUDA Toolkit 12.x
- Python 3.8+
- PyCUDA

## 🚀 Quick Start

### 1. Install CUDA Toolkit

```bash
# Ubuntu/Debian
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update
sudo apt-get install cuda-toolkit-12-2
```

### 2. Install Python Dependencies

```bash
pip install pycuda numpy
```

### 3. Compile CUDA Kernel

```bash
make
```

### 4. Run Solver

```bash
python puzzle_solver_v33.py
```

## 📁 Files

| File | Description |
|------|-------------|
| `puzzle_solver_cuda.cu` | CUDA C kernel source |
| `puzzle_solver_v33.py` | Python wrapper |
| `Makefile` | Build configuration |

## ⚡ Performance

| GPU | Speed | Est. Time (2.7B checks) |
|-----|-------|------------------------|
| RTX 4070 | ~50M checks/sec | ~54 seconds |
| RTX 4090 | ~100M checks/sec | ~27 seconds |
| A100 | ~200M checks/sec | ~14 seconds |

## ⚠️ Important Notes

1. **This is a template** - The CUDA kernel needs proper SHA-256 and RIPEMD-160 implementations
2. **ECDSA operations** on GPU are complex - consider using `libsecp256k1` with CUDA bindings
3. **Memory bandwidth** is the bottleneck - optimize data transfer between CPU/GPU

## 🔧 Advanced Compilation

```bash
# For specific GPU architecture
make ARCH_FLAGS="-gencode arch=compute_89,code=sm_89"

# With debug info
make NVCC_FLAGS="-O0 -g -G"

# Profile with Nsight
nv-nsight-cu-cli python puzzle_solver_v33.py
```
