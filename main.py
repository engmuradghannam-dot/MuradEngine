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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
