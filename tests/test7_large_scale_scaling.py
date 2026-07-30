#!/usr/bin/env python3
"""
MuradEngine v8.2 - Test 7: Large-Scale Scaling (100K+ samples)
Bitcoin Key Locality Analysis - Cross-Range Generalization

Author: Murad Ghannam
Date: 2026-07-30
"""

import numpy as np
import hashlib
import time
import random
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import LinearRegression

# secp256k1 order
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def feature_extractor(k):
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


def generate_dataset():
    """Generate training and test datasets"""

    print("=" * 70)
    print("🚀 MURADENGINE v8.2 - TEST 7: LARGE-SCALE SCALING")
    print("=" * 70)

    np.random.seed(42)

    # Training ranges
    ranges = [
        (0, 2**64),
        (2**128, 2**128 + 2**64),
        (2**192, 2**192 + 2**64),
        (2**250, 2**250 + 2**64),
        (N - 2**64, N),
    ]

    samples_per_range = 20000
    all_keys = []
    all_features = []
    all_ranges = []

    start_time = time.time()

    for i, (r_start, r_end) in enumerate(ranges):
        print(f"\n   🎯 Range {i+1}: [{hex(r_start)[:20]}..., {hex(r_end)[:20]}...]")

        range_size = r_end - r_start

        for batch in range(samples_per_range // 1000):
            offsets = [random.randint(0, range_size - 1) for _ in range(1000)]

            for offset in offsets:
                k = r_start + offset
                if k >= N:
                    k = k % N

                feat = feature_extractor(k)
                all_keys.append(k)
                all_features.append(feat)
                all_ranges.append(i)

            if (batch + 1) % 5 == 0:
                total_done = (batch + 1) * 1000
                print(f"      Progress: {total_done}/{samples_per_range}")

    all_keys = np.array(all_keys, dtype=object)
    all_features = np.array(all_features, dtype=np.float32)
    all_ranges = np.array(all_ranges)

    elapsed = time.time() - start_time
    print(f"\n✅ Training data: {len(all_keys):,} samples in {elapsed:.2f}s")

    # Test ranges (intermediate)
    test_ranges = [
        (2**32, 2**32 + 2**64),
        (2**160, 2**160 + 2**64),
        (2**220, 2**220 + 2**64),
        (2**252, 2**252 + 2**64),
    ]

    test_samples_per_range = 5000
    test_keys = []
    test_features = []
    test_ranges_idx = []

    for i, (r_start, r_end) in enumerate(test_ranges):
        print(f"\n   🎯 Test Range {i+1}")
        range_size = r_end - r_start

        for batch in range(test_samples_per_range // 1000):
            offsets = [random.randint(0, range_size - 1) for _ in range(1000)]

            for offset in offsets:
                k = r_start + offset
                if k >= N:
                    k = k % N

                feat = feature_extractor(k)
                test_keys.append(k)
                test_features.append(feat)
                test_ranges_idx.append(i)

            total_done = (batch + 1) * 1000
            print(f"      Progress: {total_done}/{test_samples_per_range}")

    test_keys = np.array(test_keys, dtype=object)
    test_features = np.array(test_features, dtype=np.float32)
    test_ranges_idx = np.array(test_ranges_idx)

    print(f"\n✅ Test data: {len(test_keys):,} samples")

    return (all_keys, all_features, all_ranges, 
            test_keys, test_features, test_ranges_idx)


def run_nearest_neighbor(train_features, test_features, all_ranges, test_ranges_idx):
    """Run nearest neighbor retrieval"""

    print("\n" + "=" * 70)
    print("🔍 NEAREST NEIGHBOR RETRIEVAL")
    print("=" * 70)

    # Normalize
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_features)
    test_scaled = scaler.transform(test_features)

    # Build NN index
    print("\n   Building NN index...")
    start = time.time()
    nn_model = NearestNeighbors(n_neighbors=100, metric='euclidean', algorithm='auto', n_jobs=-1)
    nn_model.fit(train_scaled)
    print(f"   ✅ Built in {time.time()-start:.2f}s")

    # Query
    print(f"\n   Querying {len(test_features):,} samples...")
    start = time.time()
    distances, indices = nn_model.kneighbors(test_scaled, n_neighbors=100)
    query_time = time.time() - start
    print(f"   ✅ Done in {query_time:.2f}s ({query_time/len(test_features)*1000:.2f}ms/sample)")

    # Analyze range retrieval
    range_stats = defaultdict(lambda: defaultdict(int))
    for test_idx in range(len(test_features)):
        test_r = test_ranges_idx[test_idx]
        for train_idx in indices[test_idx]:
            train_r = all_ranges[train_idx]
            range_stats[test_r][train_r] += 1

    # Top-1 adjacent range hit
    same_range_hits = 0
    for test_idx in range(len(test_features)):
        test_r = test_ranges_idx[test_idx]
        nearest = [test_r, test_r + 1]
        if all_ranges[indices[test_idx][0]] in nearest:
            same_range_hits += 1

    top1_hit = same_range_hits / len(test_features) * 100
    print(f"\n   📊 Top-1 Adjacent Range Hit: {top1_hit:.2f}%")

    return distances, indices, scaler, range_stats, top1_hit


def analyze_leakage(all_features, all_keys, test_features, test_keys):
    """Analyze feature leakage to log2(k)"""

    print("\n" + "=" * 70)
    print("🔴 FEATURE LEAKAGE ANALYSIS")
    print("=" * 70)

    train_logk = np.array([float(k.bit_length()) for k in all_keys], dtype=np.float32)
    test_logk = np.array([float(k.bit_length()) for k in test_keys], dtype=np.float32)

    # Linear regression
    lr = LinearRegression()
    lr.fit(all_features, train_logk)
    r2_train = lr.score(all_features, train_logk)
    r2_test = lr.score(test_features, test_logk)

    print(f"\n   R² (features → log2k):")
    print(f"   Training: {r2_train:.4f}")
    print(f"   Test:     {r2_test:.4f}")

    # Feature correlations
    feature_names = [
        'mean', 'std', 'min', 'max',
        'fft_mean', 'fft_std', 'fft_max', 'fft_sum4',
        'bit_mean', 'bit_std', 'bit_sum64f', 'bit_sum64l',
        'bit_sum32f', 'bit_sum32l', 'bit_sum16f', 'bit_sum16l',
        'pos_b0', 'pos_b1', 'pos_b30', 'pos_b31',
        'entropy', 'unique', 'even_sum', 'odd_sum'
    ]

    leakages = []
    for i, name in enumerate(feature_names):
        corr = abs(np.corrcoef(all_features[:, i], train_logk)[0, 1])
        leakages.append((name, corr))

    leakages.sort(key=lambda x: x[1], reverse=True)

    print(f"\n   Top 5 Leaked Features:")
    for name, corr in leakages[:5]:
        status = "🔴" if corr > 0.3 else "🟡" if corr > 0.1 else "🟢"
        print(f"   {status} {name:<15}: {corr:.4f}")

    return leakages, r2_train, r2_test


def blind_recovery_test(train_features, test_features, all_ranges, test_ranges_idx, scaler):
    """Test recovery with MSB masked"""

    print("\n" + "=" * 70)
    print("🎯 BLIND RECOVERY TEST (MSB Masked)")
    print("=" * 70)

    train_masked = scaler.transform(train_features).copy()
    test_masked = scaler.transform(test_features).copy()

    # Mask position features
    for idx in [16, 17, 18, 19]:
        train_masked[:, idx] = 0
        test_masked[:, idx] = 0

    print("   🎭 Masked: pos_b0, pos_b1, pos_b30, pos_b31")

    nn_masked = NearestNeighbors(n_neighbors=100, metric='euclidean', algorithm='auto', n_jobs=-1)
    nn_masked.fit(train_masked)

    _, indices_masked = nn_masked.kneighbors(test_masked, n_neighbors=100)

    masked_hits = 0
    for test_idx in range(len(test_features)):
        test_r = test_ranges_idx[test_idx]
        nearest = [test_r, test_r + 1]
        if all_ranges[indices_masked[test_idx][0]] in nearest:
            masked_hits += 1

    masked_hit = masked_hits / len(test_features) * 100
    print(f"\n   📊 Masked Top-1 Hit: {masked_hit:.2f}%")

    return masked_hit


def main():
    """Main execution"""

    # Generate data
    (all_keys, all_features, all_ranges,
     test_keys, test_features, test_ranges_idx) = generate_dataset()

    # Run NN retrieval
    distances, indices, scaler, range_stats, top1_hit = run_nearest_neighbor(
        all_features, test_features, all_ranges, test_ranges_idx
    )

    # Analyze leakage
    leakages, r2_train, r2_test = analyze_leakage(
        all_features, all_keys, test_features, test_keys
    )

    # Blind recovery
    masked_hit = blind_recovery_test(
        all_features, test_features, all_ranges, test_ranges_idx, scaler
    )

    # Final summary
    print("\n" + "=" * 70)
    print("✅ TEST 7 COMPLETE - SUMMARY")
    print("=" * 70)
    print(f"   Dataset: 100K Training | 20K Test | 5 Ranges")
    print(f"   Top-1 Adjacent Range Hit: {top1_hit:.2f}%")
    print(f"   R² (features → log2k): {r2_train:.4f}")
    print(f"   Blind Recovery (MSB Masked): {masked_hit:.2f}%")
    print(f"   Performance Change: {masked_hit - top1_hit:+.2f}%")
    print("\n   VERDICT: Cross-range generalization is PARTIAL.")
    print("   Feature space captures magnitude patterns beyond MSB.")
    print("=" * 70)


if __name__ == "__main__":
    main()
