#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔥 BITCOIN PUZZLE SOLVER v33 - REAL CUDA KERNEL 🔥                        ║
║                                                                              ║
║  Formula: pk = 2^puzzle - (counter × int(puzzle^E)) - r                     ║
║  CUDA C Kernel for GPU acceleration                                          ║
║  Requires: NVIDIA GPU with CUDA Toolkit 12.x + PyCUDA                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import math
import hashlib
import threading
from datetime import datetime
from decimal import Decimal, getcontext

getcontext().prec = 50

# ══════════════════════════════════════════════════════════════════════════════
# CUDA Configuration
# ══════════════════════════════════════════════════════════════════════════════
CUDA_AVAILABLE = False
CUDA_MODULE = None

try:
    import pycuda.driver as cuda
    import pycuda.autoinit
    from pycuda.compiler import SourceModule
    CUDA_AVAILABLE = True
    print(f"[GPU] CUDA detected: {cuda.Device(0).name()}")
except ImportError:
    print("[!] PyCUDA not installed. Install with: pip install pycuda")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# Compile CUDA Kernel
# ══════════════════════════════════════════════════════════════════════════════
CUDA_KERNEL_PATH = os.path.join(os.path.dirname(__file__), "puzzle_solver_cuda.cu")

def compile_cuda_kernel():
    """Compile the CUDA kernel at runtime"""
    if not os.path.exists(CUDA_KERNEL_PATH):
        print(f"[!] CUDA kernel not found: {CUDA_KERNEL_PATH}")
        return None

    with open(CUDA_KERNEL_PATH, 'r') as f:
        kernel_code = f.read()

    print("[CUDA] Compiling kernel...")
    try:
        # Compile with optimization
        module = SourceModule(
            kernel_code,
            options=['-O3', '--use_fast_math'],
            include_dirs=[],
            no_extern_c=True
        )
        print("[CUDA] Kernel compiled successfully!")
        return module
    except Exception as e:
        print(f"[!] CUDA compilation failed: {e}")
        return None

# ══════════════════════════════════════════════════════════════════════════════
# Telegram Bot
# ══════════════════════════════════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = "8678763407:AAHovW-mT3dA1j04NLe0JzNidRQZw9DIc-c"
TELEGRAM_CHAT_ID = "6221148602"

def send_telegram(message):
    def _send():
        try:
            import urllib.request
            import urllib.parse
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            urllib.request.urlopen(req, timeout=10)
        except:
            pass
    threading.Thread(target=_send, daemon=True).start()

# ══════════════════════════════════════════════════════════════════════════════
# Search Parameters
# ══════════════════════════════════════════════════════════════════════════════
E_MIN = 10.0000
E_MAX = 25.0000
E_STEP = 0.0001
COUNTER_MAX = 1000  # Will be adjusted per puzzle
REM_MAX = 200

# ══════════════════════════════════════════════════════════════════════════════
# Target Addresses (71-160)
# ══════════════════════════════════════════════════════════════════════════════
TARGET_ADDRESSES = {
    71: "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU", 72: "1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR",
    73: "12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4", 74: "1FWGcVDK3JGzCC3WtkYetULPszMaK2Jksv",
    75: "1HkWxtWEox8QUKgzAEVD7sDvWD7P6wYUzn", 76: "1DJh2eHFYQfACPmrvpyWc8MSTYKh7w9eRF",
    77: "1Bxk4CQdqL9p22JEtDfdXMsng1XacifUtE", 78: "15qF6X51huDjqTmF9BJgxXdt1xcj46Jmhb",
    79: "1ARk8HWJMn8js8tQmGUJeQHjSE7KRkn2t8", 80: "1BC1F9tNQZxfk6YZEHTVmCZWJcCEjwJQm2",
    81: "15qsCm78whspNQFydGJQk5rexzxTQopnHZ", 82: "13zYrYhhJxp6Ui1VV7pqa5WDhNWM45ARAC",
    83: "14MdEb4eFcT3MVG5sPFG4jGLuHJSnt1Dk2", 84: "1CMq3SvFcVEcpLMuuH8PUcNiqsK1oicG2D",
    85: "1K3x5L6G57Y494fDqBfrojD28UJv4s5JcK", 86: "1PxH3K1Shdjb7gSEoTX7UPDZ6SH4qGPrvq",
    87: "16AbnZjZZipwHMkYKBSfswGWKDmXHjEpSf", 88: "19QciEHbGVNY4hrhfKXmcBBCrJSBZ6TaVt",
    89: "1EzVHtmbN4fs4MiNk3ppEnKKhsmXYJ4s74", 90: "1AE8NzzgKE7Yhz7BWtAcAAxiFMbPo82NB5",
    91: "17Q7tuG2JwFFU9rXVj3uZqRtioH3mx2Jad", 92: "1K6xGMUbs6ZTXBnhw1pippqwK6wjBWtNpL",
    93: "15ANYzzCp5BFHcCnVFzXqyibpzgPLWaD8b", 94: "18ywPwj39nGjqBrQJSzZVq2izR12MDpDr8",
    95: "1CaBVPrwUxbQYYswu32w7Mj4HR4maNoJSX", 96: "1JWnE6p6UN7ZJBN7TtcbNDoRcjFtuDWoNL",
    97: "1CKCVdbDJasYmhswB6HKZHEAnNaDpK7W4n", 98: "1PXv28YxmYMaB8zxrKeZBW8dt2HK7RkRPX",
    99: "1AcAmB6jmtU6AiEcXkmiNE9TNVPsj9DULf", 100: "1EQJvpsmhazYCcKX5Au6AZmZKRnzarMVZu",
    101: "18KsfuHuzQaBTNLASyj15hy4LuqPUo1FNB", 102: "15EJFC5ZTs9nhsdvSUeBXjLAuYq3SWaxTc",
    103: "1HB1iKUqeffnVsvQsbpC6dNi1XKbyNuqao", 104: "1GvgAXVCbA8FBjXfWiAms4ytFeJcKsoyhL",
    105: "1824ZJQ7nKJ9QFTRBqn7z7dHV5EGpzUpH3", 106: "18A7NA9FTsnJxWgkoFfPAFbQzuQxpRtCos",
    107: "1NeGn21dUDDeqFQ63xb2SpgUuXuBLA4WT4", 108: "174SNxfqpdMGYy5YQcfLbSTK3MRNZEePoy",
    109: "1MnJ6hdhvK37VLmqcdEwqC3iFxyWH2PHUV", 110: "1KNRfGWw7Q9Rmwsc6NT5zsdvEb9M2Wkj5Z",
    111: "1PJZPzvGX19a7twf5HyD2VvNiPdHLzm9F6", 112: "1GuBBhf61rnvRe4K8zu8vdQB3kHzwFqSy7",
    113: "1GDSuiThEV64c166LUFC9uDcVdGjqkxKyh", 114: "1Me3ASYt5JCTAK2XaC32RMeH34PdprrfDx",
    115: "1CdufMQL892A69KXgv6UNBD17ywWqYpKut", 116: "1BkkGsX9ZM6iwL3zbqs7HWBV7SvosR6m8N",
    117: "1AWCLZAjKbV1P7AHvaPNCKiB7ZWVDMxFiz", 118: "1G6EFyBRU86sThN3SSt3GrHu1sA7w7nzi4",
    119: "1MZ2L1gFrCtkkn6DnTT2e4PFUTHw9gNwaj", 120: "1Hz3uv3nNZzBVMXLGadCucgjiCs5W9vaGz",
    121: "16zRPnT8znwq42q7XeMkZUhb1bKqgRogyy", 122: "1KrU4dHE5WrW8rhWDsTRjR21r8t3dsrS3R",
    123: "17uDfp5r4n441xkgLFmhNoSW1KWp6xVLD", 124: "13A3JrvXmvg5w9XGvyyR4JEJqiLz8ZySY3",
    125: "1UDHPdovvR985NrWSkdWQDEQ1xuRiTALq", 126: "15nf31J46iLuK1ZkTnqHo7WgN5cARFK3RA",
    127: "1Ab4vzG6wEQBDNQM1B2bvUz4fqXXdFk2WT", 128: "1Fz63c775VV9fNyj25d9Xfw3YHE6sKCxbt",
    129: "1QKBaU6WAeycb3DbKbLBkX7vJiaS8r42Xo", 130: "1CD91Vm97mLQvXhrnoMChhJx4TP9MaQkJo",
    131: "15MnK2jXPqTMURX4xC3h4mAZxyCcaWWEDD", 132: "13N66gCzWWHEZBxhVxG18P8wyjEWF9Yoi1",
    133: "1NevxKDYuDcCh1ZMMi6ftmWwGrZKC6j7Ux", 134: "19GpszRNUej5yYqxXoLnbZWKew3KdVLkXg",
    135: "1M7ipcdYHey2Y5RZM34MBbpugghmjaV89P", 136: "18aNhurEAJsw6BAgtANpexk5ob1aGTwSeL",
    137: "1FwZXt6EpRT7Fkndzv6K4b4DFoT4trbMrV", 138: "1CXvTzR6qv8wJ7eprzUKeWxyGcHwDYP1i2",
    139: "1MUJSJYtGPVGkBCTqGspnxyHahpt5Te8jy", 140: "13Q84TNNvgcL3HJiqQPvyBb9m4hxjS3jkV",
    141: "1LuUHyrQr8PKSvbcY1v1PiuGuqFjWpDumN", 142: "18192XpzzdDi2K11QVHR7td2HcPS6Qs5vg",
    143: "1NgVmsCCJaKLzGyKLFJfVequnFW9ZvnMLN", 144: "1AoeP37TmHdFh8uN72fu9AqgtLrUwcv2wJ",
    145: "1FTpAbQa4h8trvhQXjXnmNhqdiGBd1oraE", 146: "14JHoRAdmJg3XR4RjMDh6Wed6ft6hzbQe9",
    147: "19z6waranEf8CcP8FqNgdwUe1QRxvUNKBG", 148: "14u4nA5sugaswb6SZgn5av2vuChdMnD9E5",
    149: "1NBC8uXJy1GiJ6drkiZa1WuKn51ps7EPTv", 150: "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU",
    151: "1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR", 152: "12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4",
    153: "1FWGcVDK3JGzCC3WtkYetULPszMaK2Jksv", 154: "1HkWxtWEox8QUKgzAEVD7sDvWD7P6wYUzn",
    155: "1DJh2eHFYQfACPmrvpyWc8MSTYKh7w9eRF", 156: "1Bxk4CQdqL9p22JEtDfdXMsng1XacifUtE",
    157: "15qF6X51huDjqTmF9BJgxXdt1xcj46Jmhb", 158: "1ARk8HWJMn8js8tQmGUJeQHjSE7KRkn2t8",
    159: "1BC1F9tNQZxfk6YZEHTVmCZWJcCEjwJQm2", 160: "15qsCm78whspNQFydGJQk5rexzxTQopnHZ",
}

# ══════════════════════════════════════════════════════════════════════════════
# GPU Solver Class
# ══════════════════════════════════════════════════════════════════════════════
class GPUPuzzleSolver:
    def __init__(self):
        self.module = compile_cuda_kernel()
        if self.module is None:
            raise RuntimeError("Failed to compile CUDA kernel")

        # Get kernel function
        self.kernel = self.module.get_function("puzzle_solver_kernel")

        # Get device properties
        self.device = cuda.Device(0)
        self.max_threads = self.device.get_attribute(cuda.device_attribute.MAX_THREADS_PER_BLOCK)
        self.multiprocessors = self.device.get_attribute(cuda.device_attribute.MULTIPROCESSOR_COUNT)

        print(f"[GPU] Max threads per block: {self.max_threads}")
        print(f"[GPU] Multiprocessors: {self.multiprocessors}")

    def solve(self, puzzle_start=71, puzzle_end=160, 
              e_min=E_MIN, e_max=E_MAX, e_step=E_STEP,
              counter_max=COUNTER_MAX, rem_max=REM_MAX):
        """Launch GPU kernel to solve puzzles"""

        # Calculate grid dimensions
        threads_per_block = min(256, self.max_threads)
        blocks = self.multiprocessors * 4  # 4 blocks per SM for occupancy

        total_e_steps = int((e_max - e_min) / e_step)
        total_threads = threads_per_block * blocks
        e_steps_per_thread = (total_e_steps + total_threads - 1) // total_threads

        print(f"[GPU] Launching: {blocks} blocks × {threads_per_block} threads")
        print(f"[GPU] Total E steps: {total_e_steps:,}")
        print(f"[GPU] E steps per thread: {e_steps_per_thread:,}")

        # Allocate device memory
        d_results = cuda.mem_alloc(100 * 4 * 8)  # 100 results × 4 uint64s
        d_result_count = cuda.mem_alloc(4)  # int
        d_progress = cuda.mem_alloc(blocks * 8)  # uint64 per block

        cuda.memset_d32(d_result_count, 0, 1)
        cuda.memset_d32(d_progress, 0, blocks * 2)

        # Launch kernel
        start_time = time.time()

        self.kernel(
            numpy.int32(puzzle_start),
            numpy.int32(puzzle_end),
            numpy.float64(e_min),
            numpy.float64(e_step),
            numpy.int32(e_steps_per_thread),
            numpy.int32(counter_max),
            numpy.int32(rem_max),
            d_results,
            d_result_count,
            d_progress,
            block=(threads_per_block, 1, 1),
            grid=(blocks, 1)
        )

        # Wait for completion
        cuda.Context.synchronize()

        elapsed = time.time() - start_time

        # Get results
        h_result_count = numpy.zeros(1, dtype=numpy.int32)
        cuda.memcpy_dtoh(h_result_count, d_result_count)

        print(f"[GPU] Kernel completed in {elapsed:.2f} seconds")
        print(f"[GPU] Results found: {h_result_count[0]}")

        if h_result_count[0] > 0:
            h_results = numpy.zeros(100 * 4, dtype=numpy.uint64)
            cuda.memcpy_dtoh(h_results, d_results)

            for i in range(min(h_result_count[0], 100)):
                puzzle = h_results[i * 4]
                e_val = h_results[i * 4 + 1] / 10000.0
                counter = h_results[i * 4 + 2]
                r = h_results[i * 4 + 3]
                print(f"  🎉 Puzzle {puzzle}: E={e_val:.4f}, counter={counter}, r={r}")

        # Cleanup
        d_results.free()
        d_result_count.free()
        d_progress.free()

        return h_result_count[0]

# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("="*70)
    print("   🚀 BITCOIN PUZZLE SOLVER v33 - REAL CUDA KERNEL")
    print("="*70)

    if not CUDA_AVAILABLE:
        print("[!] CUDA not available. Exiting.")
        return

    try:
        solver = GPUPuzzleSolver()

        print("\n1. Start GPU search (all puzzles, E=10.000→25.000)")
        print("2. Test with small range")
        choice = input("\nChoice: ").strip()

        if choice == "1":
            solver.solve()
        elif choice == "2":
            solver.solve(e_min=10.0, e_max=10.1, e_step=0.001, counter_max=100)
        else:
            print("Invalid choice.")

    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import numpy
    main()
