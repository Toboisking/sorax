"""
WiFi Security Testing Toolkit — Packet Sniffer & AP Scanner
Captures beacons, probes, and data frames. Discovers networks and clients.
"""

from __future__ import annotations

import time
import json
import signal
import sys
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from scapy.all import (
    sniff as scapy_sniff,
    Dot11, Dot11Beacon, Dot11ProbeReq, Dot11ProbeResp,
    Dot11Elt, RadioTap, Dot11Deauth, Dot11Disas,
    Dot11AssoReq, Dot11ReassoReq, Dot11Auth,
    EAPOL, Raw,
    conf as scapy_conf
)
from monitor import InterfaceManager


@dataclass
class AccessPoint:
    bssid: str
    ssid: str = ""
    channel: int = 0
    rssi: int = -100
    encryption: set[str] = field(default_factory=set)
    vendor: str = ""
    first_seen: float = 0.0
    last_seen: float = 0.0
    beacons: int = 0
    clients: list[str] = field(default_factory=list)

    @property
    def encryption_str(self) -> str:
        enc = self.encryption
        if "WPA3" in enc:
            return "WPA3"
        if "WPA2" in enc and "WPA" in enc:
            return "WPA2/WPA"
        if "WPA2" in enc:
            return "WPA2"
        if "WPA" in enc:
            return "WPA"
        if "WEP" in enc:
            return "WEP"
        if "OPN" in enc:
            return "Open"
        return "Unknown"

    @property
    def is_wps(self) -> bool:
        return "WPS" in self.encryption


@dataclass
class Client:
    mac: str
    probed_ssids: list[str] = field(default_factory=list)
    rssi: int = -100
    first_seen: float = 0.0
    last_seen: float = 0.0
    associated_bssid: str | None = None


class NetworkScanner:
    """Passive scanner that discovers APs and clients from captured frames."""

    OUI_PREFIXES: dict[str, str] = {
        "00:1a:70": "Cisco-Linksys",
        "00:18:f8": "Cisco-Linksys",
        "00:0c:41": "Cisco-Linksys",
        "d4:6e:0e": "TP-Link",
        "14:cc:20": "TP-Link",
        "50:c7:bf": "TP-Link",
        "f4:f2:6d": "TP-Link",
        "b0:95:75": "TP-Link",
        "c0:25:06": "Avaya/TP-Link",
        "00:90:4c": "TP-Link",
        "9c:53:22": "Ubiquiti",
        "04:18:d6": "Ubiquiti",
        "fc:ec:da": "Ubiquiti",
        "dc:9f:db": "Ubiquiti",
        "78:8a:20": "Ubiquiti",
        "24:a4:3c": "Ubiquiti",
        "44:d9:e7": "Ubiquiti",
        "74:83:c2": "Ubiquiti",
        "80:2a:a8": "Ubiquiti",
        "ac:86:74": "D-Link",
        "c8:d3:a3": "D-Link",
        "1c:bd:b9": "D-Link",
        "f0:7d:68": "D-Link",
        "c8:be:19": "D-Link",
        "78:54:2e": "D-Link",
        "00:22:b0": "D-Link",
        "c8:3a:35": "Tenda",
        "00:b0:0c": "Tenda",
        "c4:e9:84": "Netgear",
        "00:14:6c": "Netgear",
        "e0:46:9a": "Netgear",
        "84:1b:5e": "Netgear",
    }

    def __init__(self, iface: str):
        self.iface = iface
        self.aps: dict[str, AccessPoint] = {}
        self.clients: dict[str, Client] = {}
        self._running = False
        self._packet_count = 0

        scapy_conf.verb = 0

    def _oui_lookup(self, mac: str) -> str:
        prefix = mac[:8].lower()
        return self.OUI_PREFIXES.get(prefix, "")

    def _encryption_from_rsn(self, elt) -> set[str]:
        """Parse RSN (WPA2/WPA3) IE."""
        enc: set[str] = set()
        raw = bytes(elt.info)
        if len(raw) < 2:
            return enc

        if len(raw) >= 8:
            suite = raw[6:10]
            if suite == b'\x00\x0f\xac\x04':
                enc.add("CCMP")
            elif suite == b'\x00\x0f\xac\x02':
                enc.add("TKIP")

        if len(raw) >= 12:
            count = int.from_bytes(raw[10:12], "little")
            offset = 12
            for _ in range(min(count, 4)):
                if offset + 4 <= len(raw):
                    suite = raw[offset:offset + 4]
                    if suite == b'\x00\x0f\xac\x04':
                        enc.add("CCMP")
                    elif suite == b'\x00\x0f\xac\x02':
                        enc.add("TKIP")
                    offset += 4

        if offset + 2 <= len(raw):
            count = int.from_bytes(raw[offset:offset + 2], "little")
            offset += 2
            for _ in range(min(count, 4)):
                if offset + 4 <= len(raw):
                    suite = raw[offset:offset + 4]
                    if suite == b'\x00\x0f\xac\x02':
                        enc.add("WPA2")
                    elif suite == b'\x00\x0f\xac\x08':
                        enc.add("WPA3")
                    elif suite == b'\x00\x0f\xac\x09':
                        enc.add("WPA3")
                    elif suite == b'\x00\x0f\xac\x0a':
                        enc.add("WPA3")
                    elif suite == b'\x00\x0f\xac\x05':
                        enc.add("WPA2")
                    elif suite == b'\x00\x0f\xac\x06':
                        enc.add("WPA2")
                    offset += 4
        return enc

    def _handle_packet(self, pkt) -> None:
        self._packet_count += 1

        if not pkt.haslayer(Dot11):
            return

        dot11 = pkt[Dot11]
        now = time.time()

        rssi = -100
        if pkt.haslayer(RadioTap):
            rt = pkt[RadioTap]
            if hasattr(rt, 'dBm_AntSignal') and rt.dBm_AntSignal is not None:
                rssi = rt.dBm_AntSignal

        # Management frames
        if dot11.type == 0:
            bssid = dot11.addr3 if dot11.addr3 else dot11.addr2
            if not bssid:
                return
            bssid = bssid.upper()

            if dot11.subtype == 8 and pkt.haslayer(Dot11Beacon):
                self._process_beacon(pkt, dot11, bssid, rssi, now)

            elif dot11.subtype == 4 and pkt.haslayer(Dot11ProbeReq):
                self._process_probe_request(pkt, dot11, rssi, now)

            elif dot11.subtype == 5 and pkt.haslayer(Dot11ProbeResp):
                self._process_probe_response(pkt, dot11, bssid, rssi, now)

        # Data frames — track association
        elif dot11.type == 2:
            src = dot11.addr2.upper() if dot11.addr2 else None
            dst = dot11.addr1.upper() if dot11.addr1 else None
            bssid = dot11.addr3.upper() if dot11.addr3 else None

            if src and bssid and bssid in self.aps:
                if src not in self.aps[bssid].clients:
                    self.aps[bssid].clients.append(src)

            if src and src not in self.clients:
                self.clients[src] = Client(mac=src, first_seen=now, last_seen=now)
            if src in self.clients:
                self.clients[src].last_seen = now

    def _process_beacon(self, pkt, dot11, bssid: str, rssi: int, now: float) -> None:
        if bssid not in self.aps:
            self.aps[bssid] = AccessPoint(bssid=bssid, first_seen=now)

        ap = self.aps[bssid]
        ap.last_seen = now
        ap.beacons += 1
        if rssi > ap.rssi:
            ap.rssi = rssi

        beacon = pkt[Dot11Beacon]
        cap = beacon.cap if hasattr(beacon, 'cap') else 0

        if cap & 0x0010:
            if ap.encryption_str == "Unknown":
                ap.encryption.add("ENC")
        elif not ap.encryption:
            ap.encryption.add("OPN")

        elt = pkt.getlayer(Dot11Elt)
        while elt:
            info = bytes(elt.info) if elt.info else b""
            if elt.ID == 0:
                ap.ssid = info.decode("utf-8", errors="replace").strip("\x00") or "<hidden>"
            elif elt.ID == 3:
                if len(info) >= 1:
                    ap.channel = info[0]
            elif elt.ID == 48:
                enc = self._encryption_from_rsn(elt)
                ap.encryption.update(enc)
            elif elt.ID == 221 and len(info) >= 4:
                if info[:4] == b'\x00P\xf2\x02':
                    ap.encryption.add("WPA")
                elif info[:4] == b'\x00P\xf2\x04':
                    ap.encryption.add("WPS")
            try:
                elt = elt.payload.getlayer(Dot11Elt)
            except Exception:
                break

        if not ap.vendor:
            ap.vendor = self._oui_lookup(bssid)

    def _process_probe_request(self, pkt, dot11, rssi: int, now: float) -> None:
        src = dot11.addr2.upper() if dot11.addr2 else None
        if not src:
            return

        if src not in self.clients:
            self.clients[src] = Client(mac=src, first_seen=now)
        client = self.clients[src]
        client.rssi = max(client.rssi, rssi)
        client.last_seen = now

        elt = pkt.getlayer(Dot11Elt)
        while elt:
            if elt.ID == 0 and elt.info:
                ssid = elt.info.decode("utf-8", errors="replace").strip("\x00")
                if ssid and ssid not in client.probed_ssids:
                    client.probed_ssids.append(ssid)
            try:
                elt = elt.payload.getlayer(Dot11Elt)
            except Exception:
                break

    def _process_probe_response(self, pkt, dot11, bssid: str, rssi: int,
                                now: float) -> None:
        if bssid not in self.aps:
            self.aps[bssid] = AccessPoint(bssid=bssid, first_seen=now)
        ap = self.aps[bssid]
        ap.last_seen = now
        if rssi > ap.rssi:
            ap.rssi = rssi

        elt = pkt.getlayer(Dot11Elt)
        while elt:
            if elt.ID == 0 and elt.info:
                ssid = elt.info.decode("utf-8", errors="replace").strip("\x00")
                if ssid and ap.ssid in ("", "<hidden>"):
                    ap.ssid = ssid
            elif elt.ID == 3 and elt.info and not ap.channel:
                ap.channel = elt.info[0]
            try:
                elt = elt.payload.getlayer(Dot11Elt)
            except Exception:
                break

    def start(self, duration: float = 0, channel_hop: bool = True,
              hop_channels: list[int] | None = None) -> None:
        """Start scanning. Set duration=0 for continuous until Ctrl+C."""
        InterfaceManager.require_root()

        if channel_hop:
            from threading import Thread
            from monitor import ChannelHopper
            hopper = ChannelHopper(
                self.iface, channels=hop_channels, dwell=0.25
            )
            hop_thread = Thread(target=hopper.start, daemon=True)
            hop_thread.start()

        print(f"[*] Scanning on {self.iface}... Press Ctrl+C to stop.\n")

        self._running = True
        signal.signal(signal.SIGINT, lambda s, f: setattr(self, '_running', False))

        try:
            scapy_sniff(
                iface=self.iface,
                prn=self._handle_packet,
                store=False,
                timeout=duration or None,
            )
        except PermissionError:
            print("[!] Permission denied. Run with sudo.")
            sys.exit(1)

    def display_results(self) -> None:
        """Pretty-print discovered APs and clients."""
        print(f"\n{'='*80}")
        print(f"  ACCESS POINTS FOUND: {len(self.aps)}")
        print(f"{'='*80}")
        print(f"{'BSSID':<20} {'CH':>3} {'RSSI':>4} {'ENC':<12} {'SSID':<25} {'Beacons':>7} {'Vendor'}")
        print("-" * 80)

        for ap in sorted(self.aps.values(),
                         key=lambda a: (-a.rssi, -(a.last_seen - a.first_seen))):
            print(f"{ap.bssid:<20} {ap.channel:>3} {ap.rssi:>4} "
                  f"{ap.encryption_str:<12} {ap.ssid[:24]:<25} {ap.beacons:>7} "
                  f"{ap.vendor}")

        print(f"\n{'='*80}")
        print(f"  CLIENTS FOUND: {len(self.clients)}")
        print(f"{'='*80}")

        for client in sorted(self.clients.values(),
                             key=lambda c: -c.rssi):
            probes = ", ".join(client.probed_ssids[:5]) or "(none)"
            extra = f" +{len(client.probed_ssids) - 5}" if len(client.probed_ssids) > 5 else ""
            print(f"  {client.mac:<20} RSSI:{client.rssi:>4} Probes: {probes}{extra}")

    def export_json(self, path: str | Path) -> None:
        """Export scan results to JSON."""
        data = {
            "aps": [
                {
                    "bssid": ap.bssid,
                    "ssid": ap.ssid,
                    "channel": ap.channel,
                    "rssi": ap.rssi,
                    "encryption": ap.encryption_str,
                    "vendor": ap.vendor,
                    "clients": ap.clients,
                }
                for ap in self.aps.values()
            ],
            "clients": [
                {
                    "mac": c.mac,
                    "rssi": c.rssi,
                    "probed_ssids": c.probed_ssids,
                }
                for c in self.clients.values()
            ],
            "timestamp": time.time(),
        }
        Path(path).write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WiFi Network Scanner")
    parser.add_argument("iface", help="Wireless interface in monitor mode")
    parser.add_argument("-t", "--time", type=float, default=30,
                        help="Scan duration in seconds (0=continuous)")
    parser.add_argument("--no-hop", action="store_true",
                        help="Disable channel hopping")
    parser.add_argument("-o", "--output", type=str,
                        help="Save results to JSON file")
    parser.add_argument("--channels", type=str,
                        help="Comma-separated list of channels to hop (e.g. 1,6,11)")
    args = parser.parse_args()

    channels = None
    if args.channels:
        channels = [int(c.strip()) for c in args.channels.split(",")]

    scanner = NetworkScanner(args.iface)
    scanner.start(duration=args.time, channel_hop=not args.no_hop,
                  hop_channels=channels)
    scanner.display_results()

    if args.output:
        scanner.export_json(args.output)
        print(f"\n[*] Results saved to {args.output}")
