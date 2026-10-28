"""
WiFi Security Testing Toolkit — Monitor Mode & Interface Manager
Handles wireless interface prep, channel hopping, and capability detection.
"""

import subprocess
import re
import time
import sys
import signal
import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class WirelessInterface:
    name: str
    mac: str
    chipset: str = ""
    driver: str = ""
    monitor_mode: bool = False
    channels_2ghz: list[int] = field(default_factory=list)
    channels_5ghz: list[int] = field(default_factory=list)
    supports_injection: bool = False
    supports_packet_capture: bool = True

    @property
    def all_channels(self) -> list[int]:
        return sorted(set(self.channels_2ghz + self.channels_5ghz))


class InterfaceManager:
    """Detect, enumerate, and prepare wireless interfaces."""

    @staticmethod
    def is_windows() -> bool:
        return sys.platform == "win32"

    @staticmethod
    def require_root() -> None:
        if InterfaceManager.is_windows():
            return
        if os.geteuid() != 0:
            print("[!] Root privileges required. Re-run with sudo.")
            sys.exit(1)

    @classmethod
    def enumerate(cls) -> list[WirelessInterface]:
        """Find all wireless interfaces with capabilities."""
        ifaces: list[WirelessInterface] = []

        try:
            result = subprocess.run(
                ["iwconfig"], capture_output=True, text=True, timeout=10
            )
            for block in result.stdout.split("\n\n"):
                if not block.strip() or "no wireless extensions" in block:
                    continue
                name_match = re.search(r"^(\S+)", block)
                if not name_match:
                    continue
                name = name_match.group(1)
                mac = "00:00:00:00:00:00"
                mac_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", block)
                if mac_match:
                    mac = mac_match.group(0).lower()
                ifaces.append(WirelessInterface(name=name, mac=mac))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        try:
            result = subprocess.run(
                ["iw", "dev"], capture_output=True, text=True, timeout=10
            )
            current = None
            for line in result.stdout.splitlines():
                phy = re.search(r"^phy#(\d+)", line)
                iface = re.search(r"^\s+Interface\s+(\S+)", line)
                addr = re.search(r"^\s+addr\s+(\S+)", line)
                if phy:
                    continue
                if iface:
                    current = iface.group(1)
                if addr and current:
                    existing = [i for i in ifaces if i.name == current]
                    if existing:
                        existing[0].mac = addr.group(1).lower()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        for iface in ifaces:
            cls._enrich_capabilities(iface)

        return ifaces

    @classmethod
    def _enrich_capabilities(cls, iface: WirelessInterface) -> None:
        """Detect supported channels and injection capability."""
        try:
            result = subprocess.run(
                ["iwlist", iface.name, "channel"],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.splitlines():
                ch_match = re.search(r"Channel\s+(\d+)\s*:\s*([\d.]+)\s*GHz", line)
                if ch_match:
                    ch = int(ch_match.group(1))
                    freq = float(ch_match.group(2))
                    if freq < 3:
                        iface.channels_2ghz.append(ch)
                    else:
                        iface.channels_5ghz.append(ch)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            iface.channels_2ghz = list(range(1, 14))

        try:
            result = subprocess.run(
                ["aireplay-ng", "--test", iface.name],
                capture_output=True, text=True, timeout=10
            )
            if "Injection is working!" in result.stdout:
                iface.supports_injection = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    @classmethod
    def enable_monitor_mode(cls, iface_name: str) -> str:
        """Enable monitor mode. Returns the monitor interface name."""
        cls.require_root()

        try:
            subprocess.run(["airmon-ng", "check", "kill"],
                           capture_output=True, timeout=15)
        except FileNotFoundError:
            pass

        try:
            result = subprocess.run(
                ["airmon-ng", "start", iface_name],
                capture_output=True, text=True, timeout=15
            )
            mon_match = re.search(r"monitor mode.*?on\s+(\S+)", result.stdout)
            if not mon_match:
                mon_match = re.search(r"\(monitor mode enabled on\s+(\S+)\)", result.stdout)
            if mon_match:
                return mon_match.group(1)
        except FileNotFoundError:
            pass

        try:
            subprocess.run(["ip", "link", "set", iface_name, "down"],
                           capture_output=True, check=True)
            subprocess.run(["iw", iface_name, "set", "monitor", "none"],
                           capture_output=True, check=True)
            subprocess.run(["ip", "link", "set", iface_name, "up"],
                           capture_output=True, check=True)
            return iface_name
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        try:
            subprocess.run(["iwconfig", iface_name, "mode", "monitor"],
                           capture_output=True, check=True)
            subprocess.run(["ifconfig", iface_name, "up"],
                           capture_output=True, check=True)
            return iface_name
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        raise RuntimeError(f"Failed to enable monitor mode on {iface_name}")

    @classmethod
    def disable_monitor_mode(cls, iface_name: str) -> None:
        """Restore managed mode."""
        try:
            subprocess.run(["airmon-ng", "stop", iface_name],
                           capture_output=True, timeout=10)
        except FileNotFoundError:
            pass

        try:
            subprocess.run(["ip", "link", "set", iface_name, "down"],
                           capture_output=True)
            subprocess.run(["iw", iface_name, "set", "type", "managed"],
                           capture_output=True)
            subprocess.run(["ip", "link", "set", iface_name, "up"],
                           capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    @classmethod
    def set_channel(cls, iface: str, channel: int) -> bool:
        """Set the interface to a specific channel."""
        try:
            subprocess.run(
                ["iw", "dev", iface, "set", "channel", str(channel)],
                capture_output=True, check=True, timeout=5
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass

        try:
            subprocess.run(
                ["iwconfig", iface, "channel", str(channel)],
                capture_output=True, check=True, timeout=5
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False


class ChannelHopper:
    """Hop between channels on a schedule, useful for scanning."""

    def __init__(self, iface: str, channels: list[int] | None = None,
                 dwell: float = 0.3):
        self.iface = iface
        self.channels = channels or list(range(1, 14))
        self.dwell = dwell
        self._running = False
        self._current_idx = 0

    def start(self) -> None:
        self._running = True
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        while self._running:
            ch = self.channels[self._current_idx % len(self.channels)]
            InterfaceManager.set_channel(self.iface, ch)
            time.sleep(self.dwell)
            self._current_idx += 1

    def stop(self) -> None:
        self._running = False

    def _handle_signal(self, signum, frame):
        self._running = False


if __name__ == "__main__":
    InterfaceManager.require_root()
    ifaces = InterfaceManager.enumerate()
    for i in ifaces:
        print(f"[*] {i.name} | MAC: {i.mac} | 2.4GHz: {i.channels_2ghz} "
              f"| 5GHz: {i.channels_5ghz} | Injection: {i.supports_injection}")
