# ============================================================
# MuradEngine GPU Cluster - Kaggle Free GPU Setup
# ============================================================
# 1. Go to kaggle.com -> Notebooks -> New
# 2. Settings -> Accelerator -> GPU P100
# 3. Upload this as a notebook

# Install
!pip install -q fastapi uvicorn scikit-learn numpy matplotlib

# Clone
!git clone https://github.com/engmuradghannam-dot/MuradEngine.git

# Verify GPU
import torch
print("Kaggle GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")

# Run
import sys
sys.path.insert(0, 'MuradEngine/gpu_cluster')
from gpu_cluster_engine_v10 import GPUClusterEngineV10

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
cluster = GPUClusterEngineV10(nodes=1_000_000, batch_size=10_000)

ranges = [
    (0, 2**64), (2**64, 2**128), (2**128, 2**192),
    (2**192, 2**250), (2**250, N),
]

cluster.generate_keys_streaming(ranges, max_keys=500_000)
cluster.build_index(n_neighbors=100)

print("\n✅ Kaggle P100 GPU Ready!")
print("Speed: ~300,000 keys/sec with P100")
