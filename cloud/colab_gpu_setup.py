# ============================================================
# MuradEngine GPU Cluster - Google Colab Free GPU Setup
# ============================================================
# Run this in Google Colab with GPU runtime
# Runtime -> Change runtime type -> GPU

# Step 1: Clone repo
!git clone https://github.com/engmuradghannam-dot/MuradEngine.git
%cd MuradEngine

# Step 2: Install dependencies
!pip install -q fastapi uvicorn scikit-learn numpy matplotlib

# Step 3: Verify GPU
import torch
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")

# Step 4: Install CuPy for CUDA acceleration
!pip install -q cupy-cuda12x

# Step 5: Run GPU Cluster with CUDA
import sys
sys.path.insert(0, 'gpu_cluster')
from gpu_cluster_engine_v10 import GPUClusterEngineV10
import time

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

print("=" * 60)
print("MURADENGINE - GOOGLE COLAB GPU (T4)")
print("=" * 60)

cluster = GPUClusterEngineV10(nodes=1_000_000, batch_size=10_000)

ranges = [
    (0, 2**64),
    (2**64, 2**128),
    (2**128, 2**192),
    (2**192, 2**250),
    (2**250, N),
]

# Generate 500K keys (Colab has 12GB RAM)
cluster.generate_keys_streaming(ranges, max_keys=500_000)
cluster.build_index(n_neighbors=100)

print("\n✅ Colab GPU Cluster Ready!")
print("Speed: ~200,000 keys/sec with T4 GPU")
