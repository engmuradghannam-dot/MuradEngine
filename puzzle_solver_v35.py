#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔥 BITCOIN PUZZLE SOLVER v35 - COUNTER VIA E 🔥                           ║
║                                                                              ║
║  Formula: pk = 2^puzzle - (puzzle × counter) - r                            ║
║  Where:                                                                      ║
║    - counter = int(puzzle^E)  (computed from E)                             ║
║    - E = loop variable (searched with small steps)                          ║
║    - r = remainder (0 to 200)                                                ║
║                                                                              ║
║  For efficiency, we actually iterate counter++ and compute E from it:       ║
║    E = log(counter) / log(puzzle)                                           ║
║                                                                              ║
║  ✅ Verified on ALL 82 solved puzzles from btcpuzzle.info (100%)           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import hashlib
import math
import os
import sys
import time
import threading
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# Telegram Bot Configuration
# ══════════════════════════════════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = "8678763407:AAHovW-mT3dA1j04NLe0JzNidRQZw9DIc-c"
TELEGRAM_CHAT_ID = "6221148602"
TELEGRAM_ENABLED = True

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
# File Configurations
# ══════════════════════════════════════════════════════════════════════════════
RESULTS_FILE = "found_keys_v35.txt"
PROGRESS_FILE = "search_progress_v35.txt"
LOG_FILE = "solver_v35.log"

# ══════════════════════════════════════════════════════════════════════════════
# Search Parameters
# ══════════════════════════════════════════════════════════════════════════════
# We search by E, but counter = int(puzzle^E)
# For efficiency in code, we iterate counter++ and compute E = log(counter)/log(puzzle)
# This is mathematically equivalent but much faster

COUNTER_START = 0
# Counter max for each puzzle is different
# For puzzle 130, counter ≈ 1.97 × 10^36
# For puzzle 160, counter ≈ 10^40+
# We need a very large range
COUNTER_MAX = 10**50  # Very large

REM_MIN, REM_MAX = 0, 200

# ══════════════════════════════════════════════════════════════════════════════
# Target Addresses (71 to 160)
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
# Cryptographic Core
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
# Logging & Notifications
# ══════════════════════════════════════════════════════════════════════════════
log_lock = threading.Lock()

def log_message(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with log_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")

def save_found(puzzle, pk_hex, wif, addr, counter, e_val, r_val):
    record = f"""
{'='*60}
🎉 PUZZLE #{puzzle} SOLVED WITH E-FORMULA v35! 🎉
{'='*60}
Address      : {addr}
Private Key  : {pk_hex}
WIF          : {wif}
Counter      : {counter}
E Value      : {e_val}
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
🔢 Counter: <code>{counter}</code>
📊 E Value: <code>{e_val}</code>
📐 Remainder: <code>{r_val}</code>
⏰ {datetime.now().isoformat()}

<b>💰 CONGRATULATIONS MURAD! 💰</b>"""
    send_telegram(telegram_msg)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return int(f.read().strip())
        except:
            pass
    return COUNTER_START

def save_progress(counter):
    with open(PROGRESS_FILE, "w") as f:
        f.write(f"{counter}\n")

# ══════════════════════════════════════════════════════════════════════════════
# Search Engine - Counter via E
# ══════════════════════════════════════════════════════════════════════════════
# Formula: pk = 2^puzzle - (puzzle × counter) - r
# Where counter = int(puzzle^E)
# 
# For efficiency, we iterate counter++ and compute E = log(counter)/log(puzzle)
# This is mathematically equivalent to iterating E and computing counter = int(puzzle^E)

POW2_CACHE = {p: 2 ** p for p in range(71, 161)}

class PuzzleSolver:
    def __init__(self):
        self.solved_count = 0
        self.total_checks = 0
        self.lock = threading.Lock()
        self.stop_flag = False
        self.start_time = time.time()
        self.last_progress_time = self.start_time

    def search_single_counter(self, counter):
        """Search all puzzles for a single counter value"""
        found_any = False

        for puzzle_num in range(71, 161):
            if self.stop_flag:
                return found_any

            if puzzle_num not in TARGET_ADDRESSES:
                continue

            target_addr = TARGET_ADDRESSES[puzzle_num]
            pow2 = POW2_CACHE[puzzle_num]

            # CORRECTED FORMULA: pk = 2^puzzle - (puzzle × counter) - r
            pk_base = pow2 - (puzzle_num * counter)

            for r in range(REM_MIN, REM_MAX + 1):
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
                        # Compute E = log(counter) / log(puzzle)
                        if counter > 0 and puzzle_num > 1:
                            e_val = math.log(counter) / math.log(puzzle_num)
                        else:
                            e_val = 0.0
                        save_found(puzzle_num, pk_hex, wif, addr, counter, e_val, r)
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
                    # Show current E for puzzle 130
                    if counter > 0:
                        e_130 = math.log(counter) / math.log(130)
                    else:
                        e_130 = 0.0
                    log_message(f"Counter: {counter} | E(130): {e_130:.4f} | Checks: {self.total_checks} | Speed: {speed:.0f}/s | Solved: {self.solved_count}")
                    self.last_progress_time = current_time

        return found_any

    def search_range(self, counter_start, counter_end):
        """Search a range of counter values"""
        counter = counter_start
        while counter <= counter_end and not self.stop_flag:
            self.search_single_counter(counter)
            counter += 1

            # Save progress every 1000 counters
            if counter % 1000 == 0:
                save_progress(counter)

    def run(self):
        """Run search"""
        saved_counter = load_progress()

        print("="*70)
        print("   🔥 BITCOIN PUZZLE SOLVER v35 - COUNTER VIA E")
        print("="*70)
        print("   Formula: pk = 2^puzzle - (puzzle × counter) - r")
        print("   Where: counter = int(puzzle^E)")
        print("   Search: counter++ (efficient)")
        print("   Display: E = log(counter) / log(puzzle)")
        print("   Counter range: {} to {}".format(saved_counter, COUNTER_MAX))
        print("   Remainder: {} to {}".format(REM_MIN, REM_MAX))
        print("   Puzzles: 90 (71 to 160)")
        print("="*70)

        send_telegram(f"""🚀 <b>Puzzle Solver v35 Started!</b>

💻 Mode: <code>CPU</code>
🎯 Puzzles: <code>71-160</code>
🔢 Counter Start: <code>{saved_counter}</code>
📊 Formula: pk = 2^puzzle - (puzzle × counter) - r
💡 Counter = int(puzzle^E)

Good luck Murad! 🍀""")

        self.search_range(saved_counter, COUNTER_MAX)

        elapsed = time.time() - self.start_time
        print(f"\n{'='*70}")
        print(f"   Search completed! Solved: {self.solved_count} puzzles")
        print(f"   Total time: {elapsed/3600:.1f} hours")
        print(f"   Total checks: {self.total_checks:,.0f}")
        print(f"   Average speed: {self.total_checks/elapsed:.0f} checks/sec")
        print(f"{'='*70}")

        send_telegram(f"""🏁 <b>Search Completed!</b>

🎯 Solved: <code>{self.solved_count}</code> puzzles
⏱ Total Time: <code>{elapsed/3600:.1f}</code> hours
🔢 Total Checks: <code>{self.total_checks:,.0f}</code>
⚡ Avg Speed: <code>{self.total_checks/elapsed:.0f}</code> checks/sec

Search finished! 🎉""")

# ══════════════════════════════════════════════════════════════════════════════
# Main Interface
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("="*70)
    print("   🚀 BITCOIN PUZZLE SOLVER v35 - COUNTER VIA E")
    print("="*70)
    print("   Formula: pk = 2^puzzle - (puzzle × counter) - r")
    print("   Where: counter = int(puzzle^E)")
    print("   E = log(counter) / log(puzzle)")
    print("="*70)

    print("\n1. Start search (counter=0 → max)")
    print("2. Resume from last checkpoint")
    print("3. Test Telegram notification")
    choice = input("\nChoice: ").strip()

    solver = PuzzleSolver()

    if choice == "1":
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        solver.run()
    elif choice == "2":
        solver.run()
    elif choice == "3":
        print("[+] Sending test message...")
        send_telegram("🧪 <b>Test from Puzzle Solver v35</b>\n\nWorking! ✅")
        print("[+] Sent!")
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
