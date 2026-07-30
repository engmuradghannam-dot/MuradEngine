#!/usr/bin/env python3
"""
MuradEngine API Server - Bitcoin Key Locality Analysis
Deployed on Railway.app
"""

import os
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import random

app = FastAPI(
    title="MuradEngine API",
    description="Bitcoin Key Locality Analysis Engine",
    version="8.2.0"
)

# secp256k1 order
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

class KeyRequest(BaseModel):
    key: Optional[int] = None
    range_start: Optional[int] = 0
    range_end: Optional[int] = None
    count: Optional[int] = 100

class TestResult(BaseModel):
    test_id: str
    status: str
    results: Dict

class FeatureVector(BaseModel):
    features: List[float]
    key_magnitude: int
    key_hex: str

def feature_extractor(k: int) -> np.ndarray:
    """Extract 24-dim feature vector from private key k"""
    k_bytes = k.to_bytes(32, 'big')
    k_arr = np.frombuffer(k_bytes, dtype=np.uint8)

    features = []

    # 1. Basic stats (4)
    features.extend([
        float(np.mean(k_arr)),
        float(np.std(k_arr)),
        float(np.min(k_arr)),
        float(np.max(k_arr)),
    ])

    # 2. FFT magnitude (4)
    fft_vals = np.abs(np.fft.fft(k_arr.astype(float)))
    features.extend([
        float(np.mean(fft_vals)),
        float(np.std(fft_vals)),
        float(np.max(fft_vals)),
        float(np.sum(fft_vals[:4])),
    ])

    # 3. Bit-level features (8)
    bits = np.unpackbits(k_arr)
    features.extend([
        float(np.mean(bits)),
        float(np.std(bits)),
        float(np.sum(bits[:64])),
        float(np.sum(bits[-64:])),
        float(np.sum(bits[:32])),
        float(np.sum(bits[-32:])),
        float(np.sum(bits[:16])),
        float(np.sum(bits[-16:])),
    ])

    # 4. Byte position features (4)
    features.extend([
        float(k_arr[0]),
        float(k_arr[1]),
        float(k_arr[30]),
        float(k_arr[31]),
    ])

    # 5. Entropy & patterns (4)
    unique, counts = np.unique(k_arr, return_counts=True)
    entropy = -np.sum((counts / len(k_arr)) * np.log2(counts / len(k_arr) + 1e-10))
    features.extend([
        entropy,
        float(len(unique)),
        float(np.sum(k_arr[::2])),
        float(np.sum(k_arr[1::2])),
    ])

    return np.array(features, dtype=np.float32)

@app.get("/")
def root():
    return {
        "name": "MuradEngine API",
        "version": "8.2.0",
        "status": "running",
        "endpoints": [
            "/",
            "/health",
            "/extract_features",
            "/generate_keys",
            "/test_results",
            "/run_test7"
        ]
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": str(np.datetime64('now'))}

@app.post("/extract_features", response_model=FeatureVector)
def extract_features(request: KeyRequest):
    if request.key is None:
        raise HTTPException(status_code=400, detail="key is required")

    k = request.key % N
    features = feature_extractor(k)

    return FeatureVector(
        features=features.tolist(),
        key_magnitude=k.bit_length(),
        key_hex=hex(k)[:20] + "..."
    )

@app.post("/generate_keys")
def generate_keys(request: KeyRequest):
    start = request.range_start
    end = request.range_end or (start + 2**64)
    count = min(request.count, 1000)

    range_size = end - start
    keys = []

    for _ in range(count):
        offset = random.randint(0, range_size - 1)
        k = (start + offset) % N
        features = feature_extractor(k)
        keys.append({
            "key_hex": hex(k)[:20] + "...",
            "magnitude": k.bit_length(),
            "features": features.tolist()
        })

    return {"count": len(keys), "range": [start, end], "keys": keys}

@app.get("/test_results")
def test_results():
    return {
        "tests_completed": ["Test 1-6", "Test 7"],
        "test7": {
            "dataset": "100K Training | 20K Test | 5 Ranges",
            "top1_hit": "61.78%",
            "r2_leakage": 0.276,
            "blind_recovery": "67.46%",
            "verdict": "Cross-range generalization is PARTIAL. Feature space captures magnitude patterns beyond MSB."
        }
    }

@app.post("/run_test7")
def run_test7():
    """Run Test 7: Large-Scale Scaling (simplified version)"""
    import time
    from sklearn.preprocessing import StandardScaler
    from sklearn.neighbors import NearestNeighbors

    start_time = time.time()

    # Generate small sample for demo
    ranges = [
        (0, 2**64),
        (2**128, 2**128 + 2**64),
        (2**192, 2**192 + 2**64),
    ]

    samples_per_range = 1000
    all_keys = []
    all_features = []
    all_ranges = []

    for i, (r_start, r_end) in enumerate(ranges):
        range_size = r_end - r_start
        for _ in range(samples_per_range):
            offset = random.randint(0, range_size - 1)
            k = (r_start + offset) % N
            all_keys.append(k)
            all_features.append(feature_extractor(k))
            all_ranges.append(i)

    all_features = np.array(all_features)

    # Normalize
    scaler = StandardScaler()
    scaled = scaler.fit_transform(all_features)

    # NN
    nn = NearestNeighbors(n_neighbors=10, metric='euclidean')
    nn.fit(scaled)

    # Test on new sample
    test_k = random.randint(0, 2**64)
    test_feat = feature_extractor(test_k)
    test_scaled = scaler.transform(test_feat.reshape(1, -1))

    distances, indices = nn.kneighbors(test_scaled, n_neighbors=5)

    elapsed = time.time() - start_time

    return {
        "status": "completed",
        "training_samples": len(all_keys),
        "test_key_magnitude": test_k.bit_length(),
        "nearest_neighbors": [
            {
                "rank": i+1,
                "distance": float(distances[0][i]),
                "range": int(all_ranges[indices[0][i]]),
                "magnitude": all_keys[indices[0][i]].bit_length()
            }
            for i in range(5)
        ],
        "elapsed_seconds": round(elapsed, 2)
    }



@app.post("/run_gpu_cluster_v10")
def run_gpu_cluster_v10():
    """Run GPU Cluster v10.0 - Massive Scale Analysis"""
    from gpu_cluster.gpu_cluster_engine_v10 import GPUClusterEngineV10
    import time
    import random

    N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    start_time = time.time()

    cluster = GPUClusterEngineV10(nodes=1_000_000, batch_size=10_000, chunk_size=50)

    ranges = [
        (0, 2**64),
        (2**64, 2**128),
        (2**128, 2**192),
        (2**192, 2**250),
        (2**250, N),
    ]

    cluster.generate_keys_streaming(ranges, max_keys=50_000)
    cluster.build_index(n_neighbors=50)

    test_k = random.randint(0, 2**64)
    test_feat = feature_extractor(test_k)
    test_scaled = cluster.scaler.transform(test_feat.reshape(1, -1))
    distances, indices = cluster.nn_model.kneighbors(test_scaled, n_neighbors=5)

    elapsed = time.time() - start_time
    stats = cluster.get_stats()

    return {
        "status": "completed",
        "version": "10.0",
        "nodes": stats["nodes"],
        "capacity": stats["total_capacity"],
        "training_samples": stats["keys_generated"],
        "memory_mb": round(stats["memory_usage_mb"], 2),
        "test_key_magnitude": test_k.bit_length(),
        "nearest_neighbors": [
            {
                "rank": i+1,
                "distance": float(distances[0][i]),
                "range": int(cluster.labels[indices[0][i]]),
                "magnitude": 0
            }
            for i in range(5)
        ],
        "elapsed_seconds": round(elapsed, 2)
    }

@app.get("/gpu_cluster_status")
def gpu_cluster_status():
    """Get GPU Cluster status and capabilities"""
    return {
        "versions": {
            "v9.0": {
                "nodes": 1000,
                "batch_size": 10000,
                "capacity": 10000000,
                "status": "stable"
            },
            "v10.0": {
                "nodes": 1000000,
                "batch_size": 10000,
                "capacity": 10000000000,
                "status": "operational",
                "features": ["streaming", "memory_optimized", "massive_scale"]
            }
        },
        "endpoints": [
            "/run_gpu_cluster",
            "/run_gpu_cluster_v10",
            "/gpu_cluster_status"
        ]
    }



# ============================================================
# Cloud GPU Endpoints
# ============================================================

@app.get("/cloud/gpu_status")
def cloud_gpu_status():
    """Get Cloud GPU cluster status"""
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if gpu_available else "None"
    except:
        gpu_available = False
        gpu_name = "None"

    return {
        "local_gpu": {
            "available": gpu_available,
            "name": gpu_name,
        },
        "cloud_options": {
            "google_colab": {
                "gpu": "NVIDIA T4",
                "vram": "12GB",
                "cost": "Free",
                "limit": "12 hours/session",
                "speed": "~200,000 keys/sec",
                "setup": "cloud/colab_gpu_setup.py"
            },
            "kaggle": {
                "gpu": "NVIDIA P100",
                "vram": "16GB",
                "cost": "Free",
                "limit": "9 hours/session",
                "speed": "~300,000 keys/sec",
                "setup": "cloud/kaggle_gpu_setup.py"
            },
            "aws_free": {
                "gpu": "CPU Only",
                "vram": "N/A",
                "cost": "Free (750hrs/month)",
                "limit": "t2.micro",
                "speed": "~20,000 keys/sec",
                "setup": "cloud/aws_gpu_setup.sh"
            },
            "aws_spot": {
                "gpu": "NVIDIA T4",
                "vram": "16GB",
                "cost": "$0.16/hour",
                "limit": "None",
                "speed": "~250,000 keys/sec",
                "setup": "cloud/aws_gpu_setup.sh"
            }
        },
        "multi_vm": {
            "orchestrator": "cloud/multi_vm_orchestrator.py",
            "max_free_capacity": "2.58 TRILLION keys/month",
            "workers": ["colab", "kaggle", "aws_free"]
        }
    }

@app.post("/cloud/benchmark_cuda")
def benchmark_cuda(batch_size: int = 10000):
    """Benchmark CPU vs CUDA GPU"""
    from gpu_cluster.gpu_cluster_engine_cuda import GPUClusterEngineCUDA
    import time

    engine = GPUClusterEngineCUDA()

    # Quick benchmark
    keys = [random.randint(0, N) for _ in range(batch_size)]

    # CPU
    start = time.time()
    _ = engine.feature_extractor_batch_cpu(
        np.frombuffer(b''.join([k.to_bytes(32, 'big') for k in keys]), dtype=np.uint8).reshape(batch_size, 32)
    )
    cpu_time = time.time() - start

    # GPU (if available)
    if engine.cuda:
        start = time.time()
        _ = engine.feature_extractor_batch_cuda(keys)
        gpu_time = time.time() - start
        speedup = cpu_time / gpu_time
    else:
        gpu_time = None
        speedup = None

    return {
        "batch_size": batch_size,
        "cpu_time_ms": round(cpu_time * 1000, 2),
        "gpu_time_ms": round(gpu_time * 1000, 2) if gpu_time else None,
        "speedup": round(speedup, 2) if speedup else None,
        "cuda_available": engine.cuda,
        "gpu_name": engine.device if engine.cuda else None
    }

@app.post("/cloud/run_multi_vm")
def run_multi_vm(workers: int = 3, samples_per_worker: int = 50_000):
    """Run distributed analysis across multiple VMs"""
    import sys
    sys.path.insert(0, 'cloud')
    from multi_vm_orchestrator import MultiVMOrchestrator

    orch = MultiVMOrchestrator()
    orch.discover_workers()

    if not orch.workers:
        return {
            "status": "no_workers",
            "message": "No workers found. Please configure workers.json",
            "setup_guide": "See cloud/README.md"
        }

    N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    ranges = [
        (0, 2**64),
        (2**64, 2**128),
        (2**128, 2**192),
        (2**192, 2**250),
        (2**250, N),
    ]

    results = orch.distribute_work(ranges, samples_per_worker)

    return {
        "status": "completed",
        "workers": len(orch.workers),
        "total_keys": results.get("total_keys", 0),
        "elapsed_seconds": round(results.get("elapsed_seconds", 0), 2),
        "speed": round(results.get("speed", 0), 0),
        "cluster_stats": orch.get_cluster_stats()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
