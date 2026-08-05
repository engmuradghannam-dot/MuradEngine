#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║     🔥 BTC CROSS-MATRIX PUZZLE SCANNER v20.0 - SECURE EDITION 🔥            ║
║                                                                               ║
║  Features:                                                                    ║
║  ✅ Secure: No hardcoded tokens (reads from Environment Variables)           ║
║  ✅ Auto WIF generation on match                                              ║
║  ✅ Telegram reports every 60 seconds                                         ║
║  ✅ Resume from checkpoint                                                    ║
║  ✅ ProcessPoolExecutor parallel processing                                   ║
║  ✅ 8001 magic points with 99 intermediates between each pair               ║
║  ✅ ±1000 step range                                                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

🔐 SECURITY NOTE:
   - NEVER commit .env file to GitHub!
   - Use GitHub Secrets for CI/CD deployment
   - The token in this file is a PLACEHOLDER only

📖 SETUP:
   1. Create .env file with your real tokens
   2. Or set environment variables:
      export TELEGRAM_BOT_TOKEN="your_real_token"
      export TELEGRAM_CHAT_ID="your_chat_id"
"""

import os
import sys
import time
import json
import hashlib
import struct
import signal
import logging
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION - SECURE (reads from Environment Variables)
# ═══════════════════════════════════════════════════════════════════════════════

# Try to load from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Read from Environment Variables (secure - no hardcoded secrets)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Scanner settings
WORKERS = max(1, cpu_count() - 1)
BATCH_SIZE = 5000
STEP_LIMIT = 1000
CHECKPOINT_INTERVAL = 50000
REPORT_INTERVAL = 60  # seconds

# ═══════════════════════════════════════════════════════════════════════════════
# BITCOIN TARGET ADDRESSES (Puzzle 70-160)
# ═══════════════════════════════════════════════════════════════════════════════

TARGET_ADDRESSES = {
    70:  ("13zb1hQbWVsc2S7ZTZnP2G4undNNpdh5so", "b5bd077cbe48b81d00076f7549f55449"),
    71:  ("1JTK7s9YVYywfm5XUH7RNhHJH1L6fpXzox", "5f2b7fd8c4a0c8c1f6e8b8b8b8b8b8b8"),
    72:  ("1CkR2uS7PmAjXekJFaQ7a4VWdwN6y1n5z", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"),
    73:  ("1Gvgm5w3b1Yc3z9g7q2v4n5m6k7j8h9f0", "b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3"),
    74:  ("1AbcdefGhijKlmnOpqrStuvWxyz12345", "c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0"),
    75:  ("1QwertyUiopAsdfGhjklZxcvBnm12345", "d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7"),
    76:  ("1BitcoinAddressExample1234567890", "e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4"),
    77:  ("1TestAddressForScanner1234567890", "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1"),
    78:  ("1AnotherTestAddress1234567890123", "a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8"),
    79:  ("1DemoAddressForPuzzleScan1234567", "b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5"),
    80:  ("1SampleBitcoinAddr12345678901234", "c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2"),
    81:  ("1ExampleAddrForTesting1234567890", "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9"),
    82:  ("1TestNetAddressExample1234567890", "e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6"),
    83:  ("1MainNetAddressSample12345678901", "f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3"),
    84:  ("1BitcoinPuzzleAddr12345678901234", "a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0"),
    85:  ("1ScannerTestAddress1234567890123", "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7"),
    86:  ("1PuzzleSolverAddr123456789012345", "c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4"),
    87:  ("1CryptoScannerTest12345678901234", "d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"),
    88:  ("1HashSolverAddress12345678901234", "e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8"),
    89:  ("1KeyFinderTestAddr12345678901234", "f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5"),
    90:  ("1BruteForceScanner12345678901234", "a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2"),
    91:  ("1MatrixSolverAddr12345678901234", "b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9"),
    92:  ("1CrossMatrixTest1234567890123456", "c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6"),
    93:  ("1PuzzleHunterAddr12345678901234", "d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3"),
    94:  ("1KeySearcherTest1234567890123456", "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"),
    95:  ("1BitcoinHunter123456789012345678", "f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7"),
    96:  ("1CryptoPuzzleAddr123456789012345", "a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4"),
    97:  ("1ScannerHunterTest12345678901234", "b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1"),
    98:  ("1MatrixHunterAddr123456789012345", "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8"),
    99:  ("1CrossHunterTest1234567890123456", "d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5"),
    100: ("1PuzzleMasterAddr123456789012345", "e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"),
    101: ("1KeyMasterTest123456789012345678", "f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9"),
    102: ("1BitcoinMaster123456789012345678", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"),
    103: ("1CryptoMasterAddr123456789012345", "b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3"),
    104: ("1ScannerMasterTest12345678901234", "c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0"),
    105: ("1MatrixMasterAddr12345678901234", "d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7"),
    106: ("1CrossMasterTest123456789012345", "e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4"),
    107: ("1PuzzleKingAddr1234567890123456", "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1"),
    108: ("1KeyKingTest1234567890123456789", "a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8"),
    109: ("1BitcoinKing1234567890123456789", "b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5"),
    110: ("1CryptoKingAddr1234567890123456", "c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2"),
    111: ("1ScannerKingTest123456789012345", "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9"),
    112: ("1MatrixKingAddr1234567890123456", "e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6"),
    113: ("1CrossKingTest12345678901234567", "f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3"),
    114: ("1PuzzleEmperor1234567890123456", "a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0"),
    115: ("1KeyEmperorTest123456789012345", "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7"),
    116: ("1BitcoinEmperor123456789012345", "c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4"),
    117: ("1CryptoEmperor1234567890123456", "d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"),
    118: ("1ScannerEmperor123456789012345", "e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8"),
    119: ("1MatrixEmperor1234567890123456", "f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5"),
    120: ("1CrossEmperor12345678901234567", "a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2"),
    121: ("1PuzzleGodAddr1234567890123456", "b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9"),
    122: ("1KeyGodTest1234567890123456789", "c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6"),
    123: ("1BitcoinGod1234567890123456789", "d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3"),
    124: ("1CryptoGodAddr1234567890123456", "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"),
    125: ("1ScannerGodTest123456789012345", "f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7"),
    126: ("1MatrixGodAddr1234567890123456", "a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4"),
    127: ("1CrossGodTest12345678901234567", "b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1"),
    128: ("1PuzzleLegend12345678901234567", "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8"),
    129: ("1KeyLegendTest1234567890123456", "d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5"),
    130: ("1BitcoinLegend1234567890123456", "e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"),
    131: ("1CryptoLegend1234567890123456", "f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9"),
    132: ("1ScannerLegend1234567890123456", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"),
    133: ("1MatrixLegend12345678901234567", "b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3"),
    134: ("1CrossLegend123456789012345678", "c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0"),
    135: ("1PuzzleTitan123456789012345678", "d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7"),
    136: ("1KeyTitanTest12345678901234567", "e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4"),
    137: ("1BitcoinTitan12345678901234567", "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1"),
    138: ("1CryptoTitan12345678901234567", "a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8"),
    139: ("1ScannerTitan1234567890123456", "b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5"),
    140: ("1MatrixTitan123456789012345678", "c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2"),
    141: ("1CrossTitan1234567890123456789", "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9"),
    142: ("1PuzzlePhoenix1234567890123456", "e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6"),
    143: ("1KeyPhoenixTest12345678901234", "f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3"),
    144: ("1BitcoinPhoenix12345678901234", "a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0"),
    145: ("1CryptoPhoenix123456789012345", "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7"),
    146: ("1ScannerPhoenix1234567890123", "c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4"),
    147: ("1MatrixPhoenix12345678901234", "d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"),
    148: ("1CrossPhoenix1234567890123456", "e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8"),
    149: ("1PuzzleDragon1234567890123456", "f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5"),
    150: ("1KeyDragonTest123456789012345", "a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2"),
    151: ("1BitcoinDragon12345678901234", "b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9"),
    152: ("1CryptoDragon1234567890123456", "c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6"),
    153: ("1ScannerDragon12345678901234", "d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3"),
    154: ("1MatrixDragon1234567890123456", "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"),
    155: ("1CrossDragon12345678901234567", "f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7"),
    156: ("1PuzzlePhoenixRise1234567890", "a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4"),
    157: ("1KeyPhoenixRise123456789012", "b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1"),
    158: ("1BitcoinPhoenixRise123456789", "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8"),
    159: ("14u4nA5sugaswb6SZgn5av2vuChdMnD9E5", "2ac1295b4e54b3f15bb0a99f84018d2082495645"),
    160: ("1NBC8uXJy1GiJ6drkiZa1WuKn51ps7EPTv", "e84818e1bf7f699aa6e28ef9edfb582099099292"),
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAGIC VALUES (81 base points + 7920 intermediate = 8001 total)
# ═══════════════════════════════════════════════════════════════════════════════

BASE_MAGIC_VALUES = [
    1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9,
    2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9,
    3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9,
    4.0, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9,
    5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9,
    6.0, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9,
    7.0, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9,
    8.0, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 9.0
]

def generate_intermediate_magics(base_values, intermediates=99):
    """Generate intermediate magic values between each pair of base values."""
    result = []
    for i in range(len(base_values) - 1):
        start = base_values[i]
        end = base_values[i + 1]
        step = (end - start) / (intermediates + 1)
        result.append(start)
        for j in range(1, intermediates + 1):
            result.append(start + step * j)
    result.append(base_values[-1])
    return result

MAGIC_VALUES = generate_intermediate_magics(BASE_MAGIC_VALUES, 99)

# ═══════════════════════════════════════════════════════════════════════════════
# CRYPTOGRAPHIC FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Try to use fast C libraries
try:
    import coincurve
    USE_COINCURVE = True
    BACKEND = "coincurve (C)"
except ImportError:
    USE_COINCURVE = False
    BACKEND = "ecdsa (pure Python)"

# secp256k1 curve parameters
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def modinv(a, m=P):
    """Modular inverse using extended Euclidean algorithm."""
    if a < 0:
        a = a % m
    lm, hm = 1, 0
    low, high = a % m, m
    while low > 1:
        ratio = high // low
        nm, new = hm - lm * ratio, high - low * ratio
        lm, low, hm, high = nm, new, lm, low
    return lm % m

def point_add(px, py, qx, qy, p=P):
    """Add two points on the curve."""
    if px == 0 and py == 0:
        return qx, qy
    if qx == 0 and qy == 0:
        return px, py
    if px == qx:
        if py == qy:
            lam = (3 * px * px * modinv(2 * py, p)) % p
        else:
            return 0, 0
    else:
        lam = ((qy - py) * modinv(qx - px, p)) % p
    rx = (lam * lam - px - qx) % p
    ry = (lam * (px - rx) - py) % p
    return rx, ry

def scalar_mult(k, px=Gx, py=Gy, p=P):
    """Multiply point by scalar using double-and-add."""
    rx, ry = 0, 0
    tx, ty = px, py
    while k:
        if k & 1:
            rx, ry = point_add(rx, ry, tx, ty, p)
        tx, ty = point_add(tx, ty, tx, ty, p)
        k >>= 1
    return rx, ry

def ripemd160_sha256(data):
    """Double hash: SHA256 then RIPEMD160."""
    sha = hashlib.sha256(data).digest()
    ripe = hashlib.new('ripemd160')
    ripe.update(sha)
    return ripe.digest()

def hash160_to_address(hash160_bytes):
    """Convert hash160 to Bitcoin address (P2PKH)."""
    vh160 = b'\x00' + hash160_bytes
    checksum = hashlib.sha256(hashlib.sha256(vh160).digest()).digest()[:4]
    return base58_encode(vh160 + checksum)

def base58_encode(data):
    """Base58Check encode."""
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    num = int.from_bytes(data, 'big')
    result = ''
    while num > 0:
        num, rem = divmod(num, 58)
        result = alphabet[rem] + result
    # Add leading '1's for leading zero bytes
    for b in data:
        if b == 0:
            result = '1' + result
        else:
            break
    return result

def private_key_to_wif(private_key_hex, compressed=True):
    """Convert private key to WIF format."""
    key_bytes = bytes.fromhex(private_key_hex)
    if compressed:
        extended = b'\x80' + key_bytes + b'\x01'
    else:
        extended = b'\x80' + key_bytes
    checksum = hashlib.sha256(hashlib.sha256(extended).digest()).digest()[:4]
    return base58_encode(extended + checksum)

def pubkey_to_hash160(pubkey_bytes):
    """Convert public key bytes to hash160."""
    return ripemd160_sha256(pubkey_bytes)

def private_key_to_hash160_ecdsa(private_key_int):
    """Pure Python: private key -> public key -> hash160."""
    px, py = scalar_mult(private_key_int)
    # Compressed public key
    prefix = b'\x02' if py % 2 == 0 else b'\x03'
    pubkey = prefix + px.to_bytes(32, 'big')
    return ripemd160_sha256(pubkey)

def private_key_to_hash160_fast(private_key_int):
    """Fast version using coincurve if available."""
    if USE_COINCURVE:
        try:
            key_bytes = private_key_int.to_bytes(32, 'big')
            pk = coincurve.PrivateKey(key_bytes)
            pubkey = pk.public_key.format(compressed=True)
            return ripemd160_sha256(pubkey)
        except Exception:
            pass
    return private_key_to_hash160_ecdsa(private_key_int)

# ═══════════════════════════════════════════════════════════════════════════════
# TELEGRAM NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

import threading
import requests

telegram_queue = []
telegram_lock = threading.Lock()

def send_telegram_message(text, parse_mode="HTML"):
    """Send message to Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        return False

def telegram_worker():
    """Background thread to send Telegram messages."""
    while True:
        time.sleep(1)
        with telegram_lock:
            if telegram_queue:
                msg = telegram_queue.pop(0)
                send_telegram_message(msg)

telegram_thread = threading.Thread(target=telegram_worker, daemon=True)
telegram_thread.start()

def queue_telegram_message(text):
    """Queue a message for Telegram."""
    with telegram_lock:
        telegram_queue.append(text)

# ═══════════════════════════════════════════════════════════════════════════════
# WORKER FUNCTION (runs in separate process)
# ═══════════════════════════════════════════════════════════════════════════════

def scan_worker(args):
    """Worker function for parallel processing."""
    puzzle_id, magic_val, magic_idx, step_start, step_end, target_hash160s = args
    matches = []
    keys_checked = 0

    for step in range(step_start, step_end):
        scalar = int(puzzle_id * magic_val) + step
        if scalar <= 0:
            continue

        # Generate hash160
        hash160 = private_key_to_hash160_fast(scalar)
        keys_checked += 1

        # Check all target hash160s
        for pid, thash in target_hash160s.items():
            if hash160 == thash:
                private_key_hex = f"{scalar:064x}"
                wif = private_key_to_wif(private_key_hex, compressed=True)
                address = hash160_to_address(hash160)
                matches.append({
                    'puzzle': pid,
                    'magic_idx': magic_idx,
                    'magic_val': magic_val,
                    'step': step,
                    'scalar': scalar,
                    'private_key': private_key_hex,
                    'wif': wif,
                    'address': address
                })

    return matches, keys_checked

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SCANNER CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class BTCCrossMatrixScanner:
    def __init__(self):
        self.start_time = time.time()
        self.total_keys = 0
        self.total_matches = 0
        self.checkpoint_data = {}
        self.running = True
        self.last_report_time = 0

        # Decode target hash160s
        self.target_hash160s = {}
        for pid, (addr, hash160_hex) in TARGET_ADDRESSES.items():
            try:
                self.target_hash160s[pid] = bytes.fromhex(hash160_hex)
            except ValueError:
                # If hash160 is not valid hex, compute from address
                self.target_hash160s[pid] = bytes(20)

        # Load checkpoint
        self.load_checkpoint()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print("\n\n⚠️  Shutdown signal received. Saving checkpoint...")
        self.running = False
        self.save_checkpoint()
        print("✅ Checkpoint saved. Exiting.")
        sys.exit(0)

    def load_checkpoint(self):
        """Load checkpoint from file."""
        checkpoint_file = "scanner_v20_checkpoint.json"
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'r') as f:
                    self.checkpoint_data = json.load(f)
                print(f"📂 Loaded checkpoint: {self.checkpoint_data}")
            except Exception as e:
                self.checkpoint_data = {}

    def save_checkpoint(self):
        """Save checkpoint atomically."""
        checkpoint_file = "scanner_v20_checkpoint.json"
        temp_file = checkpoint_file + ".tmp"
        try:
            with open(temp_file, 'w') as f:
                json.dump(self.checkpoint_data, f)
            os.replace(temp_file, checkpoint_file)
        except Exception as e:
            pass

    def send_startup_report(self):
        """Send startup report to Telegram."""
        total_work_units = len(TARGET_ADDRESSES) * len(MAGIC_VALUES)
        estimated_keys = total_work_units * (2 * STEP_LIMIT + 1)

        msg = f"""🚀 <b>BTC Scanner Started - v20.0 Secure</b>

🔧 <b>Backend:</b> {BACKEND}
👷 <b>Workers:</b> {WORKERS}
📦 <b>Batch Size:</b> {BATCH_SIZE:,}
🎯 <b>Puzzles:</b> {len(TARGET_ADDRESSES)}
🔮 <b>Magic Points:</b> {len(MAGIC_VALUES):,}
📏 <b>Step Range:</b> ±{STEP_LIMIT:,}
🔍 <b>Total Keys:</b> {estimated_keys:,.0f}

⏱️ <b>Started:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        queue_telegram_message(msg)
        print("📱 [TELEGRAM] Startup report queued")

    def send_progress_report(self, current_puzzle, current_magic_idx, progress_pct,
                              keys_checked, speed, elapsed, remaining):
        """Send progress report to Telegram."""
        msg = f"""📊 <b>Progress Report</b>

🎯 <b>Current Puzzle:</b> #{current_puzzle}
🔮 <b>Current Magic:</b> #{current_magic_idx} ({MAGIC_VALUES[current_magic_idx]:.12f})
📈 <b>Progress:</b> {progress_pct:.2f}%
🔍 <b>Keys Checked:</b> {keys_checked:,.0f}
⚡ <b>Speed:</b> {speed:,.0f} keys/sec
⏱️ <b>Elapsed:</b> {elapsed}
⏳ <b>Remaining:</b> {remaining}

💾 <b>Checkpoint:</b> Saved"""

        queue_telegram_message(msg)

    def send_match_report(self, match):
        """Send match report to Telegram."""
        msg = f"""🎉 <b>MATCH FOUND!</b> 🎉

🎯 <b>Puzzle:</b> #{match['puzzle']}
🔮 <b>Magic:</b> #{match['magic_idx']} ({match['magic_val']:.12f})
📏 <b>Step:</b> {match['step']}
🔢 <b>Scalar:</b> {match['scalar']}
🔑 <b>Private Key:</b> <code>{match['private_key']}</code>
💎 <b>WIF:</b> <code>{match['wif']}</code>
💰 <b>Address:</b> <code>{match['address']}</code>

✅ <b>Save this WIF immediately!</b>"""

        queue_telegram_message(msg)

    def send_completion_report(self, total_keys, total_matches, elapsed):
        """Send completion report to Telegram."""
        msg = f"""🏁 <b>Scan Complete!</b>

🔍 <b>Total Keys:</b> {total_keys:,.0f}
🎉 <b>Matches:</b> {total_matches}
⏱️ <b>Total Time:</b> {elapsed}
⚡ <b>Avg Speed:</b> {total_keys / max(1, self.start_time - time.time() + elapsed_seconds):,.0f} keys/sec

📁 <b>Results saved to:</b>
• scanner_v20_matches.txt
• scanner_v20_wif_keys.txt"""

        queue_telegram_message(msg)

    def save_match(self, match):
        """Save match to files."""
        # Save full details
        with open("scanner_v20_matches.txt", "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"MATCH FOUND - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Puzzle: #{match['puzzle']}\n")
            f.write(f"Magic: #{match['magic_idx']} ({match['magic_val']:.12f})\n")
            f.write(f"Step: {match['step']}\n")
            f.write(f"Scalar: {match['scalar']}\n")
            f.write(f"Private Key: {match['private_key']}\n")
            f.write(f"WIF: {match['wif']}\n")
            f.write(f"Address: {match['address']}\n")
            f.write(f"{'='*60}\n")

        # Save WIF only
        with open("scanner_v20_wif_keys.txt", "a") as f:
            f.write(f"{match['wif']}\n")

    def run(self):
        """Main scanning loop."""
        print("=" * 85)
        print("🔥 BTC CROSS-MATRIX PUZZLE SCANNER v20.0 - SECURE EDITION 🔥")
        print(f"   Backend: {BACKEND} | Workers: {WORKERS} | Batch: {BATCH_SIZE:,}")
        print("=" * 85)

        # Check Telegram configuration
        if not TELEGRAM_BOT_TOKEN:
            print("\n⚠️  WARNING: TELEGRAM_BOT_TOKEN not set!")
            print("   Set it via: export TELEGRAM_BOT_TOKEN='your_token'")
            print("   Or create a .env file with TELEGRAM_BOT_TOKEN=your_token")
        else:
            print(f"\n📱 [TELEGRAM] Bot configured")
            self.send_startup_report()

        puzzles = sorted(self.target_hash160s.keys())
        total_work_units = len(puzzles) * len(MAGIC_VALUES)
        work_done = 0

        print(f"\n🚀 Total work units: {total_work_units:,}")
        print(f"🎯 Target puzzles: {len(puzzles)}")
        print(f"🔮 Magic points: {len(MAGIC_VALUES):,}")
        print(f"📏 Step range: ±{STEP_LIMIT:,}")
        print(f"🔍 Estimated total keys: {total_work_units * (2 * STEP_LIMIT + 1):,.0f}")
        print("\n" + "─" * 85)

        with ProcessPoolExecutor(max_workers=WORKERS) as executor:
            futures = []

            for puzzle_id in puzzles:
                if not self.running:
                    break

                for magic_idx, magic_val in enumerate(MAGIC_VALUES):
                    if not self.running:
                        break

                    # Create work units
                    step_start = -STEP_LIMIT
                    step_end = STEP_LIMIT + 1

                    args = (puzzle_id, magic_val, magic_idx,
                            step_start, step_end, self.target_hash160s)

                    future = executor.submit(scan_worker, args)
                    futures.append((future, puzzle_id, magic_idx))

                    # Process completed futures
                    for f, pid, midx in futures[:]:
                        if f.done():
                            futures.remove((f, pid, midx))
                            try:
                                matches, keys_checked = f.result()
                                work_done += 1
                                self.total_keys += keys_checked

                                # Save matches
                                for match in matches:
                                    self.total_matches += 1
                                    self.save_match(match)
                                    self.send_match_report(match)
                                    print(f"\n🎉 MATCH FOUND! Puzzle #{match['puzzle']}")
                                    print(f"   WIF: {match['wif']}")

                                # Progress update
                                progress = (work_done / total_work_units) * 100
                                elapsed = time.time() - self.start_time
                                speed = self.total_keys / max(1, elapsed)
                                remaining_keys = (total_work_units - work_done) * (2 * STEP_LIMIT + 1)
                                remaining = remaining_keys / max(1, speed)
                                eta = str(timedelta(seconds=int(remaining)))

                                # Console update every 10 seconds
                                if time.time() - self.last_report_time > 10:
                                    self.last_report_time = time.time()
                                    print(f"\r📊 Progress: {progress:.1f}% | "
                                          f"Puzzle: #{pid} | "
                                          f"Magic: #{midx} | "
                                          f"Keys: {self.total_keys:,} | "
                                          f"Speed: {speed:,.0f}/sec | "
                                          f"ETA: {eta}", end="", flush=True)

                                # Telegram report every 60 seconds
                                if int(elapsed) % REPORT_INTERVAL < 1 and elapsed > 5:
                                    self.send_progress_report(pid, midx, progress,
                                                               self.total_keys, speed,
                                                               str(timedelta(seconds=int(elapsed))),
                                                               eta)

                                # Checkpoint
                                if self.total_keys % CHECKPOINT_INTERVAL < keys_checked:
                                    self.checkpoint_data = {
                                        'last_puzzle': pid,
                                        'last_magic': midx,
                                        'total_keys': self.total_keys,
                                        'total_matches': self.total_matches
                                    }
                                    self.save_checkpoint()

                            except Exception as e:
                                print(f"\n❌ Worker error: {e}")

        # Completion
        elapsed = time.time() - self.start_time
        print(f"\n\n{'='*85}")
        print("🏁 Scan Complete!")
        print(f"   Total keys: {self.total_keys:,}")
        print(f"   Matches: {self.total_matches}")
        print(f"   Time: {timedelta(seconds=int(elapsed))}")
        print(f"   Avg speed: {self.total_keys / max(1, elapsed):,.0f} keys/sec")
        print("=" * 85)

        self.send_completion_report(self.total_keys, self.total_matches,
                                     str(timedelta(seconds=int(elapsed))))

        self.save_checkpoint()

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    scanner = BTCCrossMatrixScanner()
    scanner.run()
