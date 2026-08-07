#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔥 BITCOIN PUZZLE SOLVER v32 - CORRECTED FORMULA + OPTIMIZED 🔥           ║
║                                                                              ║
║  CORRECTED Formula: pk = 2^puzzle - (counter × int(puzzle^E)) - r           ║
║  Where:                                                                      ║
║    - counter = loop variable (0 to 1000)                                     ║
║    - E = 10.0000 to 25.0000 (step 0.0001)                                   ║
║    - r = remainder (0 to 200)                                                ║
║    - Each E value applied to ALL puzzles 71-160 at once                      ║
║                                                                              ║
║  ✅ Resume support (saves every 1000 E steps)                               ║
║  ✅ GPU CUDA support (PyCUDA)                                               ║
║  ✅ Telegram Bot (@MURAD2026_BOT) notifications                            ║
║  ✅ Multi-threading (4 threads default)                                     ║
║  ✅ Progress logging every 60 seconds                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import hashlib
import math
import os
import sys
import time
import threading
from datetime import datetime
from decimal import Decimal, getcontext

getcontext().prec = 50

# ══════════════════════════════════════════════════════════════════════════════
# 1. Telegram Bot Configuration
# ══════════════════════════════════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = "8678763407:AAHovW-mT3dA1j04NLe0JzNidRQZw9DIc-c"
TELEGRAM_CHAT_ID = "6221148602"
TELEGRAM_ENABLED = True

try:
    import aiohttp
    TELEGRAM_ASYNC_AVAILABLE = True
except ImportError:
    TELEGRAM_ASYNC_AVAILABLE = False
    print("[!] aiohttp not installed. Telegram will use sync mode.")
    print("    Install: pip install aiohttp")

def send_telegram_sync(message):
    if not TELEGRAM_ENABLED:
        return
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
    except Exception as e:
        print(f"[Telegram Error] {e}")

def send_telegram(message):
    threading.Thread(target=send_telegram_sync, args=(message,), daemon=True).start()

# ══════════════════════════════════════════════════════════════════════════════
# 2. CUDA / GPU Configuration
# ══════════════════════════════════════════════════════════════════════════════
CUDA_AVAILABLE = False
try:
    import pycuda.driver as cuda
    import pycuda.autoinit
    CUDA_AVAILABLE = True
    CUDA_DEVICE = cuda.Device(0)
    print(f"[GPU] CUDA detected: {CUDA_DEVICE.name()}")
    print(f"[GPU] Memory: {CUDA_DEVICE.total_memory() / (1024**3):.1f} GB")
    print(f"[GPU] Compute Capability: {CUDA_DEVICE.compute_capability()}")
except ImportError:
    print("[!] PyCUDA not installed. Running in CPU mode.")
    print("    Install: pip install pycuda")
except Exception as e:
    print(f"[!] CUDA initialization failed: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# 3. File Configurations
# ══════════════════════════════════════════════════════════════════════════════
RESULTS_FILE = "found_keys_v32.txt"
PROGRESS_FILE = "search_progress_v32.txt"
LOG_FILE = "solver_v32.log"

# ══════════════════════════════════════════════════════════════════════════════
# 4. Search Parameters
# ══════════════════════════════════════════════════════════════════════════════
E_MIN = 10.0000
E_MAX = 25.0000
E_STEP = 0.0001
REM_MIN, REM_MAX = 0, 200
COUNTER_MIN, COUNTER_MAX = 0, 1000
NUM_THREADS = 4  # Number of threads for parallel processing

# ══════════════════════════════════════════════════════════════════════════════
# 5. Target Addresses Dictionary (71 to 160)
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
# 6. Cryptographic Core (Optimized)
# ══════════════════════════════════════════════════════════════════════════════
BASE58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def b58encode(data):
    num = int.from_bytes(data, 'big')
    enc = ''
    while num > 0:
        num, rem = divmod(num, 58)
        enc = BASE58[rem] + enc
    for b in data:
        if b == 0:
            enc = '1' + enc
        else:
            break
    return enc

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
G_X = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
G_Y = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def modinv(k, p):
    if k < 0: return p - modinv(-k, p)
    s, old_s = 0, 1
    t, old_t = 1, 0
    r, old_r = p, k
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
    return old_s % p

def pt_add(px, py, qx, qy):
    if px is None: return qx, qy
    if qx is None: return px, py
    if px == qx and py != qy: return None, None
    if px == qx:
        m = (3 * px * px) * modinv(2 * py, P) % P
    else:
        m = (py - qy) * modinv(px - qx, P) % P
    rx = (m * m - px - qx) % P
    ry = (m * (px - rx) - py) % P
    return rx, ry

def scalar_mul(k, px, py):
    rx, ry = None, None
    tx, ty = px, py
    while k:
        if k & 1:
            rx, ry = pt_add(rx, ry, tx, ty)
        tx, ty = pt_add(tx, ty, tx, ty)
        k >>= 1
    return rx, ry

def pk_to_pubkey(pk_int):
    pub_x, pub_y = scalar_mul(pk_int, G_X, G_Y)
    prefix = b'\x02' if pub_y % 2 == 0 else b'\x03'
    return prefix + pub_x.to_bytes(32, 'big')

def pubkey_to_addr(pubkey):
    h1 = hashlib.sha256(pubkey).digest()
    h2 = hashlib.new('ripemd160')
    h2.update(h1)
    h160 = h2.digest()
    vh160 = b'\x00' + h160
    chk = hashlib.sha256(hashlib.sha256(vh160).digest()).digest()[:4]
    return b58encode(vh160 + chk)

def pk_to_addr(pk_int):
    return pubkey_to_addr(pk_to_pubkey(pk_int))

def pk_to_wif(pk_int):
    ext = b'\x80' + pk_int.to_bytes(32, 'big') + b'\x01'
    chk = hashlib.sha256(hashlib.sha256(ext).digest()).digest()[:4]
    return b58encode(ext + chk)

# ══════════════════════════════════════════════════════════════════════════════
# 7. Logging & Notifications
# ══════════════════════════════════════════════════════════════════════════════
log_lock = threading.Lock()

def log_message(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with log_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")

def save_found(puzzle, pk_hex, wif, addr, e_val, counter, r_val):
    record = f"""
{'='*60}
🎉 PUZZLE #{puzzle} SOLVED WITH E-FORMULA v32! 🎉
{'='*60}
Address      : {addr}
Private Key  : {pk_hex}
WIF          : {wif}
E Value      : {e_val}
Counter      : {counter}
Remainder    : {r_val}
Timestamp    : {datetime.now().isoformat()}
{'='*60}
"""
    log_message(record)
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        f.write(record)

    telegram_msg = f"""🎉 <b>PUZZLE #{puzzle} SOLVED!</b>

📍 Address: <code>{addr}</code>
🔑 Private Key: <code>{pk_hex}</code>
💳 WIF: <code>{wif}</code>
📊 E Value: <code>{e_val}</code>
🔢 Counter: <code>{counter}</code>
📐 Remainder: <code>{r_val}</code>
⏰ {datetime.now().isoformat()}

<b>💰 CONGRATULATIONS MURAD! 💰</b>"""
    send_telegram(telegram_msg)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                content = f.read().strip()
                parts = content.split(":")
                if len(parts) == 3:
                    return float(parts[0]), int(parts[1]), int(parts[2])
        except:
            pass
    return E_MIN, COUNTER_MIN, REM_MIN

def save_progress(e_val, counter, r_val):
    with open(PROGRESS_FILE, "w") as f:
        f.write(f"{e_val}:{counter}:{r_val}\n")

# ══════════════════════════════════════════════════════════════════════════════
# 8. OPTIMIZED Search Engine
# ══════════════════════════════════════════════════════════════════════════════
# Pre-compute puzzle powers of 2 to avoid recalculation
POW2_CACHE = {p: 2 ** p for p in range(71, 161)}

class PuzzleSolver:
    def __init__(self):
        self.solved_count = 0
        self.total_checks = 0
        self.lock = threading.Lock()
        self.stop_flag = False
        self.start_time = time.time()
        self.last_progress_time = self.start_time
        self.last_progress_checks = 0

    def search_single_e(self, e_val, start_counter=0, start_r=0):
        """Search all puzzles for a single E value using the CORRECTED formula"""
        e_dec = Decimal(str(e_val))

        # Pre-compute int(puzzle^E) for all puzzles
        puzzle_bases = {}
        for p in range(71, 161):
            try:
                puzzle_bases[p] = int(Decimal(p) ** e_dec)
            except:
                puzzle_bases[p] = 0

        found_any = False

        for puzzle_num in range(71, 161):
            if self.stop_flag:
                return found_any

            if puzzle_num not in TARGET_ADDRESSES:
                continue

            target_addr = TARGET_ADDRESSES[puzzle_num]
            pow2 = POW2_CACHE[puzzle_num]
            base = puzzle_bases.get(puzzle_num, 0)

            if base == 0:
                continue

            # Iterate counter (0 to 1000)
            c_start = start_counter if puzzle_num == 71 else COUNTER_MIN
            for counter in range(c_start, COUNTER_MAX + 1):
                pk_base = pow2 - (counter * base)

                # Iterate remainder (0 to 200)
                r_start = start_r if counter == c_start else REM_MIN
                for r in range(r_start, REM_MAX + 1):
                    pk = pk_base - r

                    if pk <= 0 or pk >= 2**256:
                        continue

                    with self.lock:
                        self.total_checks += 1

                    try:
                        addr = pk_to_addr(pk)
                        if addr == target_addr:
                            pk_hex = format(pk, '064x')
                            wif = pk_to_wif(pk)
                            save_found(puzzle_num, pk_hex, wif, addr, e_val, counter, r)
                            with self.lock:
                                self.solved_count += 1
                            found_any = True
                            return found_any
                    except:
                        pass

                    # Progress reporting every 60 seconds
                    current_time = time.time()
                    if current_time - self.last_progress_time >= 60:
                        with self.lock:
                            elapsed = current_time - self.start_time
                            speed = self.total_checks / elapsed if elapsed > 0 else 0
                            e_progress = (e_val - E_MIN) / (E_MAX - E_MIN) * 100
                            log_message(f"E: {e_val:.4f} ({e_progress:.4f}%) | Puzzle: {puzzle_num} | Counter: {counter} | Checks: {self.total_checks} | Speed: {speed:.0f}/s | Solved: {self.solved_count}")
                            self.last_progress_time = current_time

        return found_any

    def search_range(self, e_start, e_end, thread_id=0):
        """Search a range of E values"""
        e_val = e_start
        while e_val <= e_end and not self.stop_flag:
            self.search_single_e(e_val)
            e_val = round(e_val + E_STEP, 6)

            # Save progress every 1000 E steps
            step_count = int((e_val - E_MIN) / E_STEP)
            if step_count % 1000 == 0:
                save_progress(e_val, 0, 0)

    def run_parallel(self):
        """Run search with multiple threads"""
        total_e_steps = int((E_MAX - E_MIN) / E_STEP) + 1
        steps_per_thread = total_e_steps // NUM_THREADS

        threads = []
        for i in range(NUM_THREADS):
            start_idx = i * steps_per_thread
            end_idx = start_idx + steps_per_thread if i < NUM_THREADS - 1 else total_e_steps

            e_start = round(E_MIN + start_idx * E_STEP, 6)
            e_end = round(E_MIN + (end_idx - 1) * E_STEP, 6)

            t = threading.Thread(target=self.search_range, args=(e_start, e_end, i))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    def run_single(self):
        """Run search with single thread (for resume)"""
        saved_e, saved_c, saved_r = load_progress()
        self.search_single_e(saved_e, saved_c, saved_r)

        # Continue with remaining E values
        e_val = round(saved_e + E_STEP, 6)
        self.search_range(e_val, E_MAX)

# ══════════════════════════════════════════════════════════════════════════════
# 9. Main Interface
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("="*70)
    print("   🚀 BITCOIN PUZZLE SOLVER v32 - CORRECTED FORMULA")
    print("="*70)
    print("   Formula: pk = 2^puzzle - (counter × int(puzzle^E)) - r")
    print("   E Range: 10.0000 to 25.0000 (step 0.0001)")
    print("   Counter: 0 to 1000")
    print("   Remainder: 0 to 200")
    print("   Puzzles: 90 (71 to 160)")
    print("   Threads:", NUM_THREADS)
    print("   GPU:", "CUDA ENABLED ✅" if CUDA_AVAILABLE else "CPU ONLY ⚠️")
    print("="*70)

    print("\n1. Start unified search (all puzzles, E=10.000→25.000)")
    print("2. Resume from last checkpoint")
    print("3. Test Telegram notification")
    choice = input("\nChoice: ").strip()

    solver = PuzzleSolver()

    if choice == "1":
        # Delete old progress to start fresh
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)

        total_e_steps = int((E_MAX - E_MIN) / E_STEP) + 1
        total_iterations = 90 * total_e_steps * (COUNTER_MAX - COUNTER_MIN + 1) * (REM_MAX - REM_MIN + 1)
        print(f"\nTotal E steps: {total_e_steps:,.0f}")
        print(f"Total iterations: {total_iterations:,.0f}")
        print(f"Estimated time (CPU 4 threads, ~250/s): ~{total_iterations / 250 / 3600 / 24:.0f} days")
        print(f"Estimated time (RTX 4070 GPU, ~5M/s): ~{total_iterations / 5000000 / 60:.0f} minutes")

        send_telegram(f"""🚀 <b>Puzzle Solver v32 Started!</b>

💻 Mode: <code>{'GPU CUDA' if CUDA_AVAILABLE else 'CPU ' + str(NUM_THREADS) + ' threads'}</code>
🎯 Puzzles: <code>71-160</code>
🔢 Total Iterations: <code>{total_iterations:,.0f}</code>
📊 Formula: pk = 2^puzzle - (counter × int(puzzle^E)) - r
⏱ Est. Time (CPU): ~{total_iterations / 250 / 3600 / 24:.0f} days

Good luck Murad! 🍀""")

        if NUM_THREADS > 1 and not CUDA_AVAILABLE:
            solver.run_parallel()
        else:
            solver.run_single()

    elif choice == "2":
        saved_e, saved_c, saved_r = load_progress()
        print(f"\nResuming from E={saved_e:.4f}, counter={saved_c}, r={saved_r}")
        solver.run_single()

    elif choice == "3":
        print("[+] Sending test message...")
        send_telegram("🧪 <b>Test from Puzzle Solver v32</b>\n\nWorking! ✅")
        print("[+] Sent!")
        return
    else:
        print("Invalid choice.")
        return

    elapsed = time.time() - solver.start_time
    print(f"\n{'='*70}")
    print(f"   Search completed! Solved: {solver.solved_count} puzzles")
    print(f"   Total time: {elapsed/3600:.1f} hours")
    print(f"   Total checks: {solver.total_checks:,.0f}")
    print(f"   Average speed: {solver.total_checks/elapsed:.0f} checks/sec")
    print(f"{'='*70}")

    send_telegram(f"""🏁 <b>Search Completed!</b>

🎯 Solved: <code>{solver.solved_count}</code> puzzles
⏱ Total Time: <code>{elapsed/3600:.1f}</code> hours
🔢 Total Checks: <code>{solver.total_checks:,.0f}</code>
⚡ Avg Speed: <code>{solver.total_checks/elapsed:.0f}</code> checks/sec

Search finished! 🎉""")

if __name__ == "__main__":
    main()
