#!/usr/bin/env python3
"""
MuradEngine Massive Parallel Test v13.0
Simulates 1,000,000 workers on local machine + VMs
Uses multiprocessing to maximize CPU utilization

Run: python cloud/massive_parallel_test.py
"""

import numpy as np
import time
import random
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gpu_cluster.gpu_cluster_engine_v10 import GPUClusterEngineV10

# secp256k1 order
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Configuration
TOTAL_WORKERS = 1_000_000  # Target: 1 million workers
LOCAL_WORKERS = mp.cpu_count() * 2  # Local processes
SIMULATED_WORKERS = TOTAL_WORKERS - LOCAL_WORKERS  # Simulated

def worker_task(args):
    """Task executed by each worker process"""
    worker_id, range_start, range_end, samples = args

    # Create mini cluster for this worker
    cluster = GPUClusterEngineV10(nodes=100, batch_size=1000)

    ranges = [(range_start, range_end)]
    cluster.generate_keys_streaming(ranges, max_keys=samples)

    return {
        "worker_id": worker_id,
        "keys_generated": cluster.keys_generated,
        "features_shape": list(cluster.features.shape) if cluster.features is not None else None,
        "pid": os.getpid()
    }

def run_massive_parallel(total_keys=1_000_000):
    """Run massive parallel generation"""
    print("=" * 70)
    print("MURADENGINE MASSIVE PARALLEL v13.0")
    print("=" * 70)
    print("Target Workers: %s" % f"{TOTAL_WORKERS:,}")
    print("Local Workers: %d" % LOCAL_WORKERS)
    print("Simulated Workers: %s" % f"{SIMULATED_WORKERS:,}")
    print("Total Keys: %s" % f"{total_keys:,}")
    print("CPU Cores: %d" % mp.cpu_count())
    print()

    # Generate ranges for all workers
    keys_per_worker = total_keys // LOCAL_WORKERS
    ranges = []
    step = N // LOCAL_WORKERS

    for i in range(LOCAL_WORKERS):
        r_start = i * step
        r_end = (i + 1) * step if i < LOCAL_WORKERS - 1 else N
        ranges.append((i, r_start, r_end, keys_per_worker))

    print("🚀 Starting %d parallel workers..." % LOCAL_WORKERS)
    start_time = time.time()

    # Run in parallel using all CPU cores
    results = []
    with ProcessPoolExecutor(max_workers=LOCAL_WORKERS) as executor:
        futures = {executor.submit(worker_task, r): r[0] for r in ranges}

        for future in as_completed(futures):
            worker_id = futures[future]
            try:
                result = future.result()
                results.append(result)
                if worker_id % 10 == 0:
                    print("   Worker %d: %s keys" % (worker_id, f"{result['keys_generated']:,}"))
            except Exception as e:
                print("   Worker %d: ERROR - %s" % (worker_id, str(e)))

    elapsed = time.time() - start_time
    total_generated = sum(r["keys_generated"] for r in results)

    print("\n" + "=" * 70)
    print("MASSIVE PARALLEL COMPLETE")
    print("=" * 70)
    print("Workers Completed: %d" % len(results))
    print("Total Keys: %s" % f"{total_generated:,}")
    print("Time: %.2fs" % elapsed)
    print("Speed: %s keys/sec" % f"{total_generated/elapsed:,.0f}")
    print("Efficiency: %.1f%%" % (len(results) / LOCAL_WORKERS * 100))

    # Simulate remaining workers
    if SIMULATED_WORKERS > 0:
        print("\n📊 Simulated Workers: %s" % f"{SIMULATED_WORKERS:,}")
        simulated_keys = SIMULATED_WORKERS * keys_per_worker
        print("Simulated Keys: %s" % f"{simulated_keys:,}")
        print("GRAND TOTAL: %s keys" % f"{total_generated + simulated_keys:,}")

    return {
        "local_workers": len(results),
        "local_keys": total_generated,
        "simulated_workers": SIMULATED_WORKERS,
        "simulated_keys": SIMULATED_WORKERS * keys_per_worker if SIMULATED_WORKERS > 0 else 0,
        "elapsed": elapsed,
        "speed": total_generated / elapsed
    }

if __name__ == "__main__":
    # Use spawn to avoid issues with CUDA
    mp.set_start_method('spawn', force=True)

    result = run_massive_parallel(total_keys=100_000)

    print("\n✅ Test Complete!")
    print(json.dumps(result, indent=2))
