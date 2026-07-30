#!/usr/bin/env python3
"""
MuradEngine GPU Cluster v11.0 - CUDA Accelerated
Uses CuPy for GPU acceleration + Multi-VM support

Author: Murad Ghannam
Date: 2026-07-30
"""

import numpy as np
import time
import random
import warnings
warnings.filterwarnings('ignore')

# Try to import CuPy for CUDA acceleration
try:
    import cupy as cp
    from cupy.cuda import Device
    CUDA_AVAILABLE = True
    print("✅ CUDA available - Using GPU acceleration")
except ImportError:
    CUDA_AVAILABLE = False
    print("⚠️ CUDA not available - Falling back to CPU")

# secp256k1 order
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

class GPUClusterEngineCUDA:
    """CUDA Accelerated GPU Cluster"""

    def __init__(self, nodes=1_000_000, batch_size=10_000):
        self.nodes = nodes
        self.batch_size = batch_size
        self.total_keys = nodes * batch_size
        self.cuda = CUDA_AVAILABLE
        self.device = None

        if self.cuda:
            self.device = Device(0)
            print("   GPU: %s" % str(self.device.mem_info))

    def feature_extractor_batch_cuda(self, keys_batch):
        """CUDA-accelerated feature extraction"""
        n = len(keys_batch)
        if n == 0:
            return np.zeros((0, 24), dtype=np.float32)

        key_bytes_list = [k.to_bytes(32, 'big') for k in keys_batch]
        key_bytes = np.frombuffer(b''.join(key_bytes_list), dtype=np.uint8).reshape(n, 32)

        if self.cuda:
            key_bytes_gpu = cp.asarray(key_bytes.astype(cp.float32))
            features = cp.zeros((n, 24), dtype=cp.float32)

            features[:, 0] = cp.mean(key_bytes_gpu, axis=1)
            features[:, 1] = cp.std(key_bytes_gpu, axis=1)
            features[:, 2] = cp.min(key_bytes_gpu, axis=1)
            features[:, 3] = cp.max(key_bytes_gpu, axis=1)

            fft_vals = cp.abs(cp.fft.fft(key_bytes_gpu, axis=1))
            features[:, 4] = cp.mean(fft_vals, axis=1)
            features[:, 5] = cp.std(fft_vals, axis=1)
            features[:, 6] = cp.max(fft_vals, axis=1)
            features[:, 7] = cp.sum(fft_vals[:, :4], axis=1)

            features_cpu = cp.asnumpy(features)

            bits = np.unpackbits(key_bytes).reshape(n, 256)
            features_cpu[:, 8] = np.mean(bits, axis=1)
            features_cpu[:, 9] = np.std(bits.astype(float), axis=1)
            features_cpu[:, 10] = np.sum(bits[:, :64], axis=1)
            features_cpu[:, 11] = np.sum(bits[:, -64:], axis=1)
            features_cpu[:, 12] = np.sum(bits[:, :32], axis=1)
            features_cpu[:, 13] = np.sum(bits[:, -32:], axis=1)
            features_cpu[:, 14] = np.sum(bits[:, :16], axis=1)
            features_cpu[:, 15] = np.sum(bits[:, -16:], axis=1)

            features_cpu[:, 16] = key_bytes[:, 0]
            features_cpu[:, 17] = key_bytes[:, 1]
            features_cpu[:, 18] = key_bytes[:, 30]
            features_cpu[:, 19] = key_bytes[:, 31]

            for i in range(n):
                unique, counts = np.unique(key_bytes[i], return_counts=True)
                probs = counts / 32.0
                features_cpu[i, 20] = -np.sum(probs * np.log2(probs + 1e-10))
                features_cpu[i, 21] = len(unique)
                features_cpu[i, 22] = np.sum(key_bytes[i, ::2])
                features_cpu[i, 23] = np.sum(key_bytes[i, 1::2])

            return features_cpu
        else:
            return self.feature_extractor_batch_cpu(key_bytes)

    def feature_extractor_batch_cpu(self, key_bytes):
        """CPU fallback"""
        n = key_bytes.shape[0]
        features = np.zeros((n, 24), dtype=np.float32)

        features[:, 0] = np.mean(key_bytes, axis=1)
        features[:, 1] = np.std(key_bytes, axis=1)
        features[:, 2] = np.min(key_bytes, axis=1)
        features[:, 3] = np.max(key_bytes, axis=1)

        fft_vals = np.abs(np.fft.fft(key_bytes.astype(float), axis=1))
        features[:, 4] = np.mean(fft_vals, axis=1)
        features[:, 5] = np.std(fft_vals, axis=1)
        features[:, 6] = np.max(fft_vals, axis=1)
        features[:, 7] = np.sum(fft_vals[:, :4], axis=1)

        bits = np.unpackbits(key_bytes).reshape(n, 256)
        features[:, 8] = np.mean(bits, axis=1)
        features[:, 9] = np.std(bits.astype(float), axis=1)
        features[:, 10] = np.sum(bits[:, :64], axis=1)
        features[:, 11] = np.sum(bits[:, -64:], axis=1)
        features[:, 12] = np.sum(bits[:, :32], axis=1)
        features[:, 13] = np.sum(bits[:, -32:], axis=1)
        features[:, 14] = np.sum(bits[:, :16], axis=1)
        features[:, 15] = np.sum(bits[:, -16:], axis=1)

        features[:, 16] = key_bytes[:, 0]
        features[:, 17] = key_bytes[:, 1]
        features[:, 18] = key_bytes[:, 30]
        features[:, 19] = key_bytes[:, 31]

        for i in range(n):
            unique, counts = np.unique(key_bytes[i], return_counts=True)
            probs = counts / 32.0
            features[i, 20] = -np.sum(probs * np.log2(probs + 1e-10))
            features[i, 21] = len(unique)
            features[i, 22] = np.sum(key_bytes[i, ::2])
            features[i, 23] = np.sum(key_bytes[i, 1::2])

        return features

    def benchmark(self, batch_sizes=[1000, 5000, 10000, 50000]):
        """Benchmark CPU vs GPU"""
        print("\n" + "=" * 60)
        print("BENCHMARK: CPU vs GPU")
        print("=" * 60)

        for bs in batch_sizes:
            keys = [random.randint(0, N) for _ in range(bs)]

            start = time.time()
            _ = self.feature_extractor_batch_cpu(
                np.frombuffer(b''.join([k.to_bytes(32, 'big') for k in keys]), dtype=np.uint8).reshape(bs, 32)
            )
            cpu_time = time.time() - start

            if self.cuda:
                start = time.time()
                _ = self.feature_extractor_batch_cuda(keys)
                gpu_time = time.time() - start
                speedup = cpu_time / gpu_time
                print("Batch %6d: CPU %6.1fms | GPU %6.1fms | Speedup %.1fx" % (bs, cpu_time*1000, gpu_time*1000, speedup))
            else:
                print("Batch %6d: CPU %6.1fms | GPU N/A" % (bs, cpu_time*1000))


if __name__ == "__main__":
    engine = GPUClusterEngineCUDA()
    engine.benchmark()
